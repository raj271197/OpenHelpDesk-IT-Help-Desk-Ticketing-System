import smtplib
from email.message import EmailMessage
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from extensions import db
from flask import current_app as app
from models import Ticket, TicketUpdate, User

ticket_bp = Blueprint('ticket', __name__, url_prefix='/tickets')

STATUS_STYLES = {
    'Open': 'danger',
    'In Progress': 'warning',
    'Resolved': 'success'
}

PRIORITY_STYLES = {
    'Low': 'secondary',
    'Medium': 'warning',
    'High': 'danger'
}


def send_notification(subject, message, recipient):
    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
        return
    try:
        email = EmailMessage()
        email['Subject'] = subject
        email['From'] = app.config['MAIL_USERNAME']
        email['To'] = recipient
        email.set_content(message)
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as smtp:
            if app.config['MAIL_USE_TLS']:
                smtp.starttls()
            smtp.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            smtp.send_message(email)
    except Exception:
        pass

@ticket_bp.route('/dashboard')
@login_required
def dashboard():
    priority = request.args.get('priority')
    status = request.args.get('status')
    ticket_query = Ticket.query

    if current_user.role == 'user':
        ticket_query = ticket_query.filter_by(user_id=current_user.id)

    if priority:
        ticket_query = ticket_query.filter_by(priority=priority)
    if status:
        ticket_query = ticket_query.filter_by(status=status)

    tickets = ticket_query.order_by(Ticket.created_at.desc()).all()
    total_open = Ticket.query.filter_by(status='Open').count()
    total_in_progress = Ticket.query.filter_by(status='In Progress').count()
    total_resolved = Ticket.query.filter_by(status='Resolved').count()
    return render_template(
        'dashboard.html',
        tickets=tickets,
        status_styles=STATUS_STYLES,
        priority_styles=PRIORITY_STYLES,
        total_open=total_open,
        total_in_progress=total_in_progress,
        total_resolved=total_resolved,
    )

@ticket_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        priority = request.form.get('priority')
        ticket = Ticket(
            user_id=current_user.id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            status='Open'
        )
        db.session.add(ticket)
        db.session.commit()
        send_notification(
            'New Helpdesk Ticket Created',
            f'Your ticket "{title}" has been submitted and is now open.',
            current_user.email,
        )
        flash('Ticket created successfully.', 'success')
        return redirect(url_for('ticket.dashboard'))
    return render_template('create_ticket.html')

@ticket_bp.route('/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role == 'user' and ticket.user_id != current_user.id:
        flash('Access denied to that ticket.', 'danger')
        return redirect(url_for('ticket.dashboard'))

    if request.method == 'POST' and current_user.role == 'admin':
        status = request.form.get('status')
        comment = request.form.get('comment')
        ticket.status = status
        ticket_update = TicketUpdate(
            ticket_id=ticket.id,
            updated_by=current_user.id,
            status=status,
            comment=comment,
        )
        db.session.add(ticket_update)
        db.session.commit()
        send_notification(
            'Your ticket has been updated',
            f'Ticket "{ticket.title}" has moved to {status}. Comment: {comment}',
            ticket.user.email,
        )
        flash('Ticket updated successfully.', 'success')
        return redirect(url_for('ticket.ticket_detail', ticket_id=ticket.id))

    updates = TicketUpdate.query.filter_by(ticket_id=ticket.id).order_by(TicketUpdate.timestamp.desc()).all()
    return render_template('ticket_detail.html', ticket=ticket, updates=updates, status_styles=STATUS_STYLES)
