from flask import Blueprint, render_template, session, redirect, url_for, request
from .database import get_db
from datetime import datetime, timedelta, date

admin = Blueprint('admin', __name__)

# -------------------------------------------------
# Admin Access Control
# -------------------------------------------------
def admin_required():
    return session.get('user_is_admin') is True


# -------------------------------------------------
# Admin Dashboard
# -------------------------------------------------
@admin.route('/admin')
def admin_dashboard():
    if not admin_required():
        return redirect(url_for('main.index'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM members")
    total_members = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS pending FROM members WHERE status = 'Pending'")
    pending = cursor.fetchone()['pending']

    cursor.execute("SELECT COUNT(*) AS active FROM members WHERE status = 'Active'")
    active = cursor.fetchone()['active']

    cursor.execute("SELECT COUNT(*) AS inactive FROM members WHERE status = 'Inactive'")
    inactive = cursor.fetchone()['inactive']

    return render_template(
        'admin_dashboard.html',
        title="Admin Dashboard",
        total_members=total_members,
        pending=pending,
        active=active,
        inactive=inactive
    )


# -------------------------------------------------
# Member Management List
# -------------------------------------------------
@admin.route('/admin/members')
def admin_members():
    if not admin_required():
        return redirect(url_for('main.index'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            m.*,
            u.is_admin
        FROM members m
        LEFT JOIN users u ON u.callsign = m.callsign
        ORDER BY m.callsign ASC
    """)
    rows = cursor.fetchall()

    members = []
    for m in rows:
        m = dict(m)

        # Convert dues string → date object
        if m["dues_paid_until"]:
            try:
                m["dues_date"] = datetime.strptime(m["dues_paid_until"], "%Y-%m-%d").date()
            except:
                m["dues_date"] = None
        else:
            m["dues_date"] = None

        members.append(m)

    return render_template(
        'admin_members.html',
        title="Manage Members",
        members=members,
        today=date.today()
    )


# -------------------------------------------------
# Approve Member
# -------------------------------------------------
@admin.route('/admin/members/<int:member_id>/approve')
def approve_member(member_id):
    if not admin_required():
        return redirect(url_for('main.index'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE members SET status = 'Active' WHERE id = ?", (member_id,))
    conn.commit()

    return redirect(url_for('admin.admin_members'))


# -------------------------------------------------
# Deactivate Member
# -------------------------------------------------
@admin.route('/admin/members/<int:member_id>/deactivate')
def deactivate_member(member_id):
    if not admin_required():
        return redirect(url_for('main.index'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE members SET status = 'Inactive' WHERE id = ?", (member_id,))
    conn.commit()

    return redirect(url_for('admin.admin_members'))


# -------------------------------------------------
# Update Dues Paid Until
# -------------------------------------------------
@admin.route('/admin/members/<int:member_id>/set_dues', methods=['POST'])
def set_dues(member_id):
    if not admin_required():
        return redirect(url_for('main.index'))

    dues = request.form.get('dues_paid_until', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE members
        SET dues_paid_until = ?
        WHERE id = ?
    """, (dues, member_id))

    conn.commit()

    return redirect(url_for('admin.admin_members'))


# -------------------------------------------------
# Renew +1 Year
# -------------------------------------------------
@admin.route('/admin/members/<int:member_id>/renew')
def renew_member(member_id):
    if not admin_required():
        return redirect(url_for('main.index'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT dues_paid_until FROM members WHERE id = ?", (member_id,))
    row = cursor.fetchone()

    today = date.today()

    if row['dues_paid_until']:
        try:
            current_dues = datetime.strptime(row['dues_paid_until'], "%Y-%m-%d").date()
        except:
            current_dues = today
    else:
        current_dues = today

    # If expired, renew from today; otherwise extend from current date
    if current_dues < today:
        new_dues = today.replace(year=today.year + 1)
    else:
        new_dues = current_dues.replace(year=current_dues.year + 1)

    cursor.execute("""
        UPDATE members
        SET dues_paid_until = ?
        WHERE id = ?
    """, (new_dues.isoformat(), member_id))

    conn.commit()

    return redirect(url_for('admin.admin_members'))


# -------------------------------------------------
# Edit Member (Full Admin Override)
# -------------------------------------------------
@admin.route('/admin/members/<int:member_id>/edit', methods=['GET', 'POST'])
def edit_member(member_id):
    if not admin_required():
        return redirect(url_for('main.index'))

    conn = get_db()
    cursor = conn.cursor()

    # Load existing member + admin flag
    cursor.execute("""
        SELECT m.*, u.is_admin
        FROM members m
        JOIN users u ON u.callsign = m.callsign
        WHERE m.id = ?
    """, (member_id,))
    member = cursor.fetchone()

    if request.method == 'POST':
        first = request.form.get('first_name')
        last = request.form.get('last_name')
        address = request.form.get('address')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip')
        email = request.form.get('email')
        phone = request.form.get('phone')
        new_callsign = request.form.get('callsign').upper()
        status = request.form.get('status')

        # Checkbox: checked → "1", unchecked → None
        is_admin = 1 if request.form.get("is_admin") == "1" else 0

        # >>> NEW FIELD: agreed_to_terms <<<
        agreed_to_terms = 1 if request.form.get("agreed_to_terms") else 0

        # Update members table
        cursor.execute("""
            UPDATE members
            SET first_name=?, last_name=?, address=?, city=?, state=?, zip=?,
                email=?, phone=?, callsign=?, status=?, agreed_to_terms=?
            WHERE id=?
        """, (first, last, address, city, state, zip_code,
              email, phone, new_callsign, status, agreed_to_terms, member_id))

        # Update users table (admin role + callsign sync)
        cursor.execute("""
            UPDATE users
            SET is_admin = ?, callsign = ?
            WHERE callsign = ?
        """, (is_admin, new_callsign, member['callsign']))

        conn.commit()
        return redirect(url_for('admin.admin_members'))

    return render_template("admin_edit_member.html", member=member)