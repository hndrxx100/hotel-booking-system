from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Room, Guest, Booking, Payment, CheckLog
from datetime import datetime

bp = Blueprint('guest', __name__, url_prefix='/guest')

@bp.route('/register', methods=['GET', 'POST'])
def register_guest():
    # Register a new guest
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        existing_guest = Guest.query.filter_by(email=email).first()
        if existing_guest:
            flash('Guest with this email already exists.', 'warning')
        else:
            guest = Guest(full_name=full_name, email=email, phone=phone)
            db.session.add(guest)
            db.session.commit()
            flash('Guest registered successfully!', 'success')
            return redirect(url_for('guest.view_rooms'))
    return render_template('guest/register.html')

@bp.route('/rooms')
def view_rooms():
    # View available rooms (FR1) - accessible without login
    rooms = Room.query.filter_by(is_available=True).all()
    return render_template('guest/rooms.html', rooms=rooms)

@bp.route('/book/<int:room_id>', methods=['GET', 'POST'])
def book_room(room_id):
    # Make a booking (FR2)
    room = Room.query.get_or_404(room_id)
    if request.method == 'POST':
        # Check if guest exists or create a new one
        email = request.form['email']
        guest = Guest.query.filter_by(email=email).first()
        if not guest:
            full_name = request.form['full_name']
            phone = request.form['phone']
            guest = Guest(full_name=full_name, email=email, phone=phone)
            db.session.add(guest)
            db.session.commit()
        if room.is_available:
            check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d').date()
            check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d').date()
            if check_in < datetime.utcnow().date() or check_out <= check_in:
                flash('Invalid dates.', 'danger')
            else:
                booking = Booking(
                    guest_id=guest.id,
                    room_id=room_id,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    status='Pending'
                )
                db.session.add(booking)
                room.is_available = False
                payment = Payment(booking_id=booking.id, amount=room.price, payment_method='Card')
                db.session.add(payment)
                db.session.commit()
                flash('Booking created! A confirmation will be sent.', 'success')
                # Placeholder for email confirmation (FR3)
                return redirect(url_for('guest.dashboard', guest_id=guest.id))
        flash('Room not available.', 'danger')
    return render_template('guest/book.html', room=room)

@bp.route('/dashboard/<int:guest_id>')
def dashboard(guest_id):
    # Display guest's bookings (requires guest ID)
    guest = Guest.query.get_or_404(guest_id)
    bookings = Booking.query.filter_by(guest_id=guest.id).all()
    return render_template('guest/dashboard.html', guest=guest, bookings=bookings)

@bp.route('/cancel/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    # Cancel a booking (FR4)
    booking = Booking.query.get_or_404(booking_id)
    if booking.status in ['Pending', 'Paid']:
        booking.status = 'Cancelled'
        booking.room.is_available = True
        db.session.commit()
        flash('Booking cancelled.', 'success')
        # Placeholder for refund logic
    else:
        flash('Cannot cancel a checked-in or checked-out booking.', 'danger')
    return redirect(url_for('guest.dashboard', guest_id=booking.guest_id))

@bp.route('/modify/<int:booking_id>', methods=['GET', 'POST'])
def modify_booking(booking_id):
    # Modify a booking (FR4)
    booking = Booking.query.get_or_404(booking_id)
    if request.method == 'POST' and booking.status in ['Pending', 'Paid']:
        new_check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d').date()
        new_check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d').date()
        if new_check_in < datetime.utcnow().date() or new_check_out <= new_check_in:
            flash('Invalid dates.', 'danger')
        else:
            booking.check_in_date = new_check_in
            booking.check_out_date = new_check_out
            booking.status = 'Modified'
            db.session.commit()
            flash('Booking modified.', 'success')
            return redirect(url_for('guest.dashboard', guest_id=booking.guest_id))
    return render_template('guest/modify.html', booking=booking)