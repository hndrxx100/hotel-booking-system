from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.models import Guest, Booking

dashboard_bp = Blueprint('dashboard', __name__)


# === Unified Dashboard Route ===
@dashboard_bp.route('/dashboard')
def dashboard():
    # Staff login
    if 'user_role' in session:
        role = session['user_role']

        if role == 'Admin':
            return render_template('admin_dashboard.html')
        elif role == 'Receptionist':
            return render_template('receptionist_dashboard.html')
        else:
            flash('Unknown staff role.', 'error')
            return redirect(url_for('auth.login'))

    # Guest login
    elif 'guest_id' in session:
        guest = Guest.query.get(session['guest_id'])
        return render_template('guest_dashboard.html', guest=guest)

    # No one logged in
    flash('Please log in to access your dashboard.', 'error')
    return redirect(url_for('auth.login'))


# === Redirect legacy dashboard routes to unified route ===
@dashboard_bp.route('/admin_dashboard')
@dashboard_bp.route('/receptionist_dashboard')
@dashboard_bp.route('/guest_dashboard')
def legacy_dashboard_redirect():
    return redirect(url_for('dashboard.dashboard'))


# === Guest Bookings ===
@dashboard_bp.route('/my_bookings')
def my_bookings():
    if 'guest_id' not in session:
        flash('Please log in to view your bookings.', 'error')
        return redirect(url_for('auth.guest_login'))

    guest = Guest.query.get(session['guest_id'])
    bookings = Booking.query.filter_by(guest_id=session['guest_id']).all()

    return render_template('guest_dashboard.html', guest=guest, bookings=bookings)

