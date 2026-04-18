# OpenHelpDesk

A free, open-source IT help desk ticketing system built with Flask, SQLAlchemy, and Bootstrap.

## Features

- User signup and login
- OTP login flow without paid email/SMS services
- Role-based access: user and admin
- Ticket creation, tracking, status updates, and deletion
- Admin ticket updates with comments
- Filter tickets by priority and status
- Responsive UI with Bootstrap and custom styling

## Installation

1. Create a Python virtual environment:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Create a `.env` file from `.env.example` and set your secret key.

4. Run the app:

   ```powershell
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser.

## Notes

- The first registered account becomes the admin.
- OTP is emailed when SMTP is configured. In local development, it can also be flashed directly for testing.
- Email notifications are optional and require SMTP credentials in `.env`.
- The production deployment target for this repository is a single Python web service. There is no `package.json` in this repo.

## Deploy On Render

This repository is a single Flask application with server-rendered templates in `templates/` and static assets in `static/`. Deploy it as one Python Web Service from the repository root.

### Recommended architecture

- Web Service: Flask app
- Postgres: Render Postgres database

### Manual Render settings

- Service Type: `Web Service`
- Runtime: `Python`
- Root Directory: repository root
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Health Check Path: `/health`

### Required environment variables

- `SECRET_KEY`: any long random string
- `DATABASE_URL`: your Render Postgres internal connection string

### Optional environment variables

- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USE_TLS`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `SESSION_COOKIE_SECURE`

### Important production note

Do not rely on SQLite for Render production deployments. Render services use an ephemeral filesystem unless you attach a persistent disk, so local SQLite data can be lost on restart or redeploy. Use Render Postgres for persistent ticket data.

## Files

- `app.py`: Flask application entrypoint
- `models.py`: SQLAlchemy models for users, tickets, and updates
- `routes/auth.py`: Authentication and OTP routes
- `routes/tickets.py`: Ticket dashboard and update routes
- `templates/`: HTML templates for UI
- `static/css/styles.css`: Custom UI styling
