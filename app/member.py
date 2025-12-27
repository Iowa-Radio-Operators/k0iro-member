from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash
from .database import get_db

member = Blueprint('member', __name__)

@member.route('/apply', methods=['GET', 'POST'])
def apply():
    error = None

    if request.method == 'POST':
        first = request.form.get('first_name', '').strip()
        last = request.form.get('last_name', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        zip_code = request.form.get('zip', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        callsign = request.form.get('callsign', '').strip().upper()
        password = request.form.get('password', '')

        # NEW: Agreement checkbox
        agreed = request.form.get('agreed_to_terms')
        if not agreed:
            error = "You must agree to the club bylaws and constitution to apply."
            return render_template('apply.html', title="Apply", error=error)

        # Basic validation
        if not all([first, last, address, city, state, zip_code, email, phone, callsign, password]):
            error = "All fields are required."
            return render_template('apply.html', title="Apply", error=error)

        conn = get_db()
        cursor = conn.cursor()

        # Check if callsign already exists in users table
        cursor.execute("SELECT id FROM users WHERE callsign = ?", (callsign,))
        existing = cursor.fetchone()

        if existing:
            error = "That call sign is already registered."
            return render_template('apply.html', title="Apply", error=error)

        # Insert into members table
        cursor.execute("""
            INSERT INTO members (
                first_name, last_name, address, city, state, zip,
                phone, email, status, dues_paid_until, callsign, agreed_to_terms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', NULL, ?, ?)
        """, (
            first, last, address, city, state, zip_code,
            phone, email, callsign, 1  # agreed_to_terms = 1
        ))

        # Insert into users table
        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users (callsign, email, password_hash, is_admin, is_active)
            VALUES (?, ?, ?, 0, 1)
        """, (callsign, email, password_hash))

        conn.commit()

        # Auto-login
        session['user'] = callsign
        session['user_id'] = cursor.lastrowid
        session['user_is_admin'] = False

        return redirect(url_for('main.index'))

    return render_template('apply.html', title="Apply", error=error)