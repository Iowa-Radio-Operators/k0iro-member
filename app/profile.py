from flask import Blueprint, render_template, session, redirect, url_for
from .database import get_db

# This file defines its OWN blueprint
profile = Blueprint('profile', __name__)

@profile.route('/profile')
def profile_page():
    # Must be logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    conn = get_db()
    cursor = conn.cursor()

    # Pull membership info
    cursor.execute("""
        SELECT *
        FROM members
        WHERE email = (
            SELECT email FROM users WHERE id = ?
        )
    """, (user_id,))
    member = cursor.fetchone()

    # Pull user info
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    return render_template('profile.html', title="My Account", member=member, user=user)