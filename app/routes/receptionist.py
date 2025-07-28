from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash
from app.models import Receptionist
from app import db

receptionist_bp = Blueprint('receptionist', __name__)


@receptionist_bp.route('/receptionist/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        receptionist = Receptionist.query.filter_by(email=email).first()
        if receptionist and receptionist.check_password(password):
            session['receptionist_id'] = receptionist.id
            session['role'] = 'receptionist'
            if 'X-Requested-With' in request.headers:  # Detect AJAX
                return jsonify({'success': True, 'redirect': url_for('dashboard.receptionist_dashboard_html')})
            return redirect(url_for('dashboard.receptionist_dashboard_html'))
        else:
            error = 'Invalid email or password'
            if 'X-Requested-With' in request.headers:
                return jsonify({'success': False, 'message': error}), 401
            flash(error, 'danger')
    return render_template('receptionist/login.html')


@receptionist_bp.route('/receptionist/logout')
def logout():
    session.clear()
    return redirect(url_for('receptionist.login'))
