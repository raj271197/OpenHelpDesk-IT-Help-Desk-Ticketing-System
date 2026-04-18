from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from constants import (
    MAX_COMMENT_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_TITLE_LENGTH,
    PRIORITY_STYLES,
    STATUS_STYLES,
    TICKET_CATEGORIES,
    TICKET_PRIORITIES,
    TICKET_STATUSES,
)
from extensions import db
from models import Ticket, TicketUpdate
from notifications import send_email


ticket_bp = Blueprint('ticket', __name__, url_prefix='/tickets')


def _normalize_short_text(value):
    return ' '.join((value or '').split())


def _normalize_long_text(value):
    return (value or '').strip()


def _visible_ticket_query():
    query = Ticket.query.options(joinedload(Ticket.user))
    if current_user.role != 'admin':
        query = query.filter_by(user_id=current_user.id)
    return query


def _get_ticket_or_404(ticket_id):
    ticket = Ticket.query.options(joinedload(Ticket.user), joinedload(Ticket.updates)).get_or_404(ticket_id)
    if current_user.role != 'admin' and ticket.user_id != current_user.id:
        flash('Access denied to that ticket.', 'danger')
        return None
    return ticket


def _validate_ticket_form(form):
    title = _normalize_short_text(form.get('title'))
    description = _normalize_long_text(form.get('description'))
    category = form.get('category')
    priority = form.get('priority')

    errors = []
    if len(title) < 5 or len(title) > MAX_TITLE_LENGTH:
        errors.append('Ticket title must be between 5 and 255 characters.')
    if len(description) < 10 or len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append('Description must be between 10 and 4000 characters.')
    if category not in TICKET_CATEGORIES:
        errors.append('Choose a valid ticket category.')
    if priority not in TICKET_PRIORITIES:
        errors.append('Choose a valid ticket priority.')

    return {
        'title': title,
        'description': description,
        'category': category,
        'priority': priority,
    }, errors


def _validate_update_form(form, current_status):
    status = form.get('status')
    comment = _normalize_long_text(form.get('comment'))

    errors = []
    if status not in TICKET_STATUSES:
        errors.append('Choose a valid ticket status.')
    if len(comment) > MAX_COMMENT_LENGTH:
        errors.append('Comment must be 2000 characters or fewer.')
    if not comment and status == current_status:
        errors.append('Provide a comment or change the ticket status before saving.')

    return {'status': status, 'comment': comment}, errors


@ticket_bp.route('/dashboard')
@login_required
def dashboard():
    priority = request.args.get('priority')
    status = request.args.get('status')
    base_query = _visible_ticket_query()
    ticket_query = base_query

    if priority:
        if priority not in TICKET_PRIORITIES:
            flash('Invalid priority filter ignored.', 'warning')
            return redirect(url_for('ticket.dashboard', status=status))
        ticket_query = ticket_query.filter_by(priority=priority)

    if status:
        if status not in TICKET_STATUSES:
            flash('Invalid status filter ignored.', 'warning')
            return redirect(url_for('ticket.dashboard', priority=priority))
        ticket_query = ticket_query.filter_by(status=status)

    tickets = ticket_query.order_by(Ticket.created_at.desc()).all()
    total_open = base_query.filter_by(status='Open').count()
    total_in_progress = base_query.filter_by(status='In Progress').count()
    total_resolved = base_query.filter_by(status='Resolved').count()

    return render_template(
        'dashboard.html',
        tickets=tickets,
        status_styles=STATUS_STYLES,
        priority_styles=PRIORITY_STYLES,
        ticket_priorities=TICKET_PRIORITIES,
        ticket_statuses=TICKET_STATUSES,
        total_open=total_open,
        total_in_progress=total_in_progress,
        total_resolved=total_resolved,
    )


@ticket_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    form_data = {
        'title': '',
        'description': '',
        'category': TICKET_CATEGORIES[0],
        'priority': TICKET_PRIORITIES[0],
    }

    if request.method == 'POST':
        form_data, errors = _validate_ticket_form(request.form)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'create_ticket.html',
                form_data=form_data,
                ticket_categories=TICKET_CATEGORIES,
                ticket_priorities=TICKET_PRIORITIES,
            )

        ticket = Ticket(
            user_id=current_user.id,
            title=form_data['title'],
            description=form_data['description'],
            category=form_data['category'],
            priority=form_data['priority'],
            status='Open',
        )
        db.session.add(ticket)
        db.session.commit()

        send_email(
            'New Helpdesk Ticket Created',
            f'Your ticket "{ticket.title}" has been submitted and is now open.',
            current_user.email,
        )
        flash('Ticket created successfully.', 'success')
        return redirect(url_for('ticket.dashboard'))

    return render_template(
        'create_ticket.html',
        form_data=form_data,
        ticket_categories=TICKET_CATEGORIES,
        ticket_priorities=TICKET_PRIORITIES,
    )


@ticket_bp.route('/<int:ticket_id>', methods=['GET'])
@login_required
def ticket_detail(ticket_id):
    ticket = _get_ticket_or_404(ticket_id)
    if ticket is None:
        return redirect(url_for('ticket.dashboard'))

    return render_template(
        'ticket_detail.html',
        ticket=ticket,
        updates=ticket.updates,
        status_styles=STATUS_STYLES,
        ticket_statuses=TICKET_STATUSES,
    )


@ticket_bp.route('/<int:ticket_id>/update', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    if current_user.role != 'admin':
        abort(403)

    ticket = Ticket.query.options(joinedload(Ticket.user)).get_or_404(ticket_id)
    form_data, errors = _validate_update_form(request.form, ticket.status)
    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('ticket.ticket_detail', ticket_id=ticket.id))

    ticket.status = form_data['status']
    ticket_update = TicketUpdate(
        ticket_id=ticket.id,
        updated_by=current_user.id,
        status=form_data['status'],
        comment=form_data['comment'] or None,
    )
    db.session.add(ticket_update)
    db.session.commit()

    send_email(
        'Your ticket has been updated',
        (
            f'Ticket "{ticket.title}" has been updated to {form_data["status"]}.\n\n'
            f'Comment: {form_data["comment"] or "No additional comment."}'
        ),
        ticket.user.email,
    )
    flash('Ticket updated successfully.', 'success')
    return redirect(url_for('ticket.ticket_detail', ticket_id=ticket.id))


@ticket_bp.route('/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    ticket = _get_ticket_or_404(ticket_id)
    if ticket is None:
        return redirect(url_for('ticket.dashboard'))

    deleted_title = ticket.title
    recipient_email = ticket.user.email
    deleted_by_admin = current_user.role == 'admin' and current_user.id != ticket.user_id

    db.session.delete(ticket)
    db.session.commit()

    if deleted_by_admin:
        send_email(
            'Your ticket has been deleted',
            f'An administrator deleted your ticket "{deleted_title}".',
            recipient_email,
        )

    flash('Ticket deleted successfully.', 'success')
    return redirect(url_for('ticket.dashboard'))
