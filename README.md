# OpenHelpDesk

A free, open-source IT help desk ticketing system built with Flask, SQLite, and Bootstrap.

## Features

- User signup and login
- OTP login flow without paid email/SMS services
- Role-based access: user and admin
- Ticket creation, tracking, and status updates
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
- OTP is generated locally and stored in the database for verification.
- Email notifications are optional and require SMTP credentials in `.env`.

## Files

- `app.py`: Flask application entrypoint
- `models.py`: SQLAlchemy models for users, tickets, and updates
- `routes/auth.py`: Authentication and OTP routes
- `routes/tickets.py`: Ticket dashboard and update routes
- `templates/`: HTML templates for UI
- `static/css/styles.css`: Custom UI styling
