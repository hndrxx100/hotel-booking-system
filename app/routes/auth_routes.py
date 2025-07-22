from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash

from app import db
from app.models import User, Guest

auth_bp = Blueprint('auth', __name__)


# === Guest Login ===
@auth_bp.route('/guest_login', methods=['GET', 'POST'])
def guest_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        guest = Guest.query.filter_by(email=email).first()

        if not guest or not guest.password_hash:
            flash('No account found. Please create one after booking.', 'error')
            return redirect(url_for('auth.guest_login'))

        if not check_password_hash(guest.password_hash, password):
            flash('Incorrect password.', 'error')
            return redirect(url_for('auth.guest_login'))

        session['guest_id'] = guest.id
        session['guest_name'] = guest.full_name
        session['guest_email'] = guest.email
        session['role'] = 'guest'  # <-- Add this

        flash('Guest login successful!', 'info')
        return redirect(url_for('dashboard.dashboard'))

    return render_template('login.html', guest_login=True)


# === Staff Login (Admin/Receptionist) ===
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['username'] = user.username
            session['user_role'] = user.role  # Use a consistent key like 'user_role'
            session['role'] = user.role  # <-- Add this
            flash('Login successful!', 'success')

            return redirect(url_for('dashboard.dashboard'))

        flash('Invalid credentials.', 'error')
        return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth_bp.route('/create_account', methods=['POST'])
def create_account():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Missing credentials'})

    guest = Guest.query.filter_by(email=email).first()

    if not guest:
        return jsonify({'success': False, 'message': 'No booking found with that email. Please book first.'})

    if guest.password_hash:
        return jsonify({'success': False, 'message': 'Account already exists.'})

    guest.set_password(password)  # ✅ Use the method defined in the model
    db.session.commit()

    return jsonify({'success': True, 'message': 'Account created successfully.'})


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
