from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func, extract
from app import app, db
from models import Staff, Guest, Booking, Room, RoomCategory, Payment
from forms import (RoomSearchForm, BookingForm, BookingLookupForm, ModifyBookingForm,
                   LoginForm, StaffForm, RoomCategoryForm, RoomForm)
from calendar import month_name
import logging
from random import shuffle
from scheduler import CLEANING_DURATION_HOURS
from sqlalchemy.sql import text
from datetime import date
from email_service import send_booking_confirmation, send_booking_modification, \
    send_booking_cancellation, send_payment_confirmation  # Import email functions
import os
from dotenv import load_dotenv

load_dotenv()
app.jinja_env.filters['month_name'] = lambda num: month_name[num]
import json


def admin_required(f):
    """Decorator to require admin role"""

    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'modal_type=error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


def staff_required(f):
    """Decorator to require admin or receptionist role"""

    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'receptionist']:
            flash('Access denied. Staff privileges required.', 'modal_type=error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


def get_available_rooms(check_in, check_out, exclude_booking_id=None):
    if check_out <= check_in:
        raise ValueError("Check-out date must be after check-in date")
    if check_in < date.today():
        raise ValueError("Check-in date cannot be in the past")
    query = db.session.query(Room).join(RoomCategory).filter(
        Room.status == 'available'  # Only include rooms with status 'available'
    )
    overlapping_bookings = db.session.query(Booking.room_id).filter(
        and_(
            Booking.status.in_(['pending', 'confirmed', 'checked_in']),
            Booking.payment_status != 'cancelled',
            Booking.check_in < check_out,
            Booking.check_out > check_in
        )
    )
    if exclude_booking_id:
        overlapping_bookings = overlapping_bookings.filter(Booking.id != exclude_booking_id)
    query = query.filter(~Room.id.in_(overlapping_bookings))
    return query.all()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search_rooms', methods=['GET', 'POST'])
def search_rooms():
    form = RoomSearchForm()
    available_rooms = []
    if form.validate_on_submit():
        check_in = form.check_in.data
        check_out = form.check_out.data
        try:
            available_rooms = get_available_rooms(check_in, check_out)
        except ValueError as e:
            flash(str(e), 'modal_type=error')
            return render_template('search_rooms.html', form=form)
        rooms_by_category = {}
        for room in available_rooms:
            category = room.category.name
            if category not in rooms_by_category:
                rooms_by_category[category] = {
                    'category': room.category,
                    'rooms': [],
                    'nights': (check_out - check_in).days
                }
            rooms_by_category[category]['rooms'].append(room)
        # Shuffle rooms for each category
        for category_data in rooms_by_category.values():
            shuffle(category_data['rooms'])
        return render_template('search_rooms.html', form=form,
                               rooms_by_category=rooms_by_category,
                               check_in=check_in, check_out=check_out)
    return render_template('search_rooms.html', form=form)


@app.route('/book_room', methods=['POST'])
def book_room():
    form = BookingForm()
    if form.validate_on_submit():
        room_id = form.room_id.data
        check_in = datetime.strptime(form.check_in.data, '%Y-%m-%d').date()
        check_out = datetime.strptime(form.check_out.data, '%Y-%m-%d').date()

        # Start a transaction with row-level locking
        db.session.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ'))
        try:
            # Lock the room and check availability
            available_rooms = get_available_rooms(check_in, check_out)
            if not any(room.id == int(room_id) for room in available_rooms):
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'errors': {'room_id': ['Selected room is not available for the specified dates.']}
                }), 400

            guest = Guest.query.filter(
                or_(
                    Guest.email == form.guest_email.data if form.guest_email.data else False,
                    Guest.phone == form.guest_phone.data
                )
            ).first()
            if not guest:
                guest = Guest(
                    name=form.guest_name.data,
                    email=form.guest_email.data,
                    phone=form.guest_phone.data
                )
                db.session.add(guest)
                db.session.flush()

            room = Room.query.get(room_id)
            nights = (check_out - check_in).days
            total_price = room.category.base_price * nights
            deposit_amount = total_price * 0.5 if form.payment_method.data == 'in_person' else total_price

            booking = Booking(
                reference=Booking.generate_reference(),
                guest_id=guest.id,
                room_id=room.id,
                check_in=check_in,
                check_out=check_out,
                total_price=total_price,
                payment_method=form.payment_method.data,
                auto_cancel_time=datetime.utcnow() + timedelta(hours=1)
            )
            db.session.add(booking)
            db.session.commit()

            # Send confirmation email
            booking_data = {
                'id': booking.id,
                'reference': booking.reference,
                'room_type': room.category.name,
                'check_in': booking.check_in.strftime('%Y-%m-%d'),
                'check_out': booking.check_out.strftime('%Y-%m-%d'),
                'total_price': booking.total_price,
                'payment_method': booking.payment_method,
                'deposit_amount': deposit_amount,
                'auto_cancel_time': booking.auto_cancel_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            email_result = send_booking_confirmation(booking_data, guest.email)
            logging.info(f"Email send result for {guest.email}, booking {booking.reference}: {email_result}")

            return jsonify({
                'success': True,
                'booking_reference': booking.reference,
                'total_price': booking.total_price,
                'payment_method': booking.payment_method,
                'deposit_amount': deposit_amount,
                'momo_number': os.getenv("MOMO_NUMBER"),
                'auto_cancel_time': booking.auto_cancel_time.strftime('%Y-%m-%d %H:%M:%S'),
                'admin_email': os.getenv("ADMIN_EMAIL")
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Booking error: {str(e)}")
            return jsonify({
                'success': False,
                'errors': {'general': ['An error occurred while processing the booking.']}
            }), 500
    return jsonify({'success': False, 'errors': form.errors}), 400


@app.route('/booking_lookup', methods=['GET', 'POST'])
def booking_lookup():
    form = BookingLookupForm()
    booking = None
    can_modify_or_cancel = False
    can_check_in = False
    can_check_out = False

    if form.validate_on_submit():
        guest_query = Guest.query
        if form.search_type.data == 'email':
            guest_query = guest_query.filter_by(email=form.search_value.data)
        else:
            guest_query = guest_query.filter_by(phone=form.search_value.data)
        guest = guest_query.first()
        if guest:
            booking = Booking.query.filter_by(
                reference=form.booking_reference.data,
                guest_id=guest.id
            ).first()
            if booking:
                # Check if booking can be modified or cancelled
                if (booking.status not in ['checked_in', 'checked_out', 'cancelled'] and
                        booking.payment_status == 'paid' and
                        (booking.check_in - date.today()).days > 2):
                    can_modify_or_cancel = True
                # Check if booking can be checked in
                if (booking.payment_status == 'paid' and
                        booking.status == 'confirmed' and
                        booking.check_in == date.today()):
                    can_check_in = True
                # Check if booking can be checked out
                if (booking.status == 'checked_in' and
                        booking.check_out >= date.today()):
                    can_check_out = True
            else:
                flash('Booking not found with the provided details.', 'modal_type=error')
        else:
            flash('No guest found with the provided contact information.', 'modal_type=error')

    return render_template('booking_lookup.html', form=form, booking=booking,
                           can_modify_or_cancel=can_modify_or_cancel,
                           can_check_in=can_check_in,
                           can_check_out=can_check_out)


@app.route('/modify_booking/<booking_reference>', methods=['GET', 'POST'])
def modify_booking(booking_reference):
    booking = Booking.query.filter_by(reference=booking_reference).first_or_404()
    if booking.status not in ['pending', 'confirmed']:
        flash('Only pending or confirmed bookings can be modified.', 'modal_type=error')
        return redirect(url_for('booking_lookup'))
    if booking.payment_status != 'paid' or (booking.check_in - date.today()).days <= 2:
        flash('Modifications require payment to be completed and must be done more than 48 hours before check-in.', 'modal_type=error')
        return redirect(url_for('booking_lookup'))
    form = ModifyBookingForm()
    form.room_category.choices = [(0, 'Keep Current Room')] + [
        (category.id, category.name) for category in RoomCategory.query.order_by(RoomCategory.name).all()
    ]
    if form.validate_on_submit():
        new_check_in = form.check_in.data
        new_check_out = form.check_out.data
        try:
            available_rooms = get_available_rooms(new_check_in, new_check_out, booking.id)
        except ValueError as e:
            flash(str(e), 'modal_type=error')
            return redirect(url_for('modify_booking', booking_reference=booking_reference))
        new_room = booking.room
        if form.room_category.data and form.room_category.data != 0:
            category_rooms = [r for r in available_rooms if r.category_id == form.room_category.data]
            if category_rooms:
                new_room = category_rooms[0]
            else:
                flash('No rooms available in selected category for the new dates.', 'modal_type=error')
                return redirect(url_for('modify_booking', booking_reference=booking_reference))
        else:
            if booking.room not in available_rooms:
                flash('Current room is not available for the new dates.', 'modal_type=error')
                return redirect(url_for('modify_booking', booking_reference=booking_reference))
        nights = (new_check_out - new_check_in).days
        total_price = new_room.category.base_price * nights

        booking.check_in = new_check_in
        booking.check_out = new_check_out
        booking.room_id = new_room.id
        booking.total_price = total_price
        booking.modified_at = datetime.utcnow()
        db.session.commit()

        # Send modification email
        booking_data = {
            'id': booking.id,
            'reference': booking.reference,
            'room_type': new_room.category.name,
            'check_in': booking.check_in.strftime('%Y-%m-%d'),
            'check_out': booking.check_out.strftime('%Y-%m-%d'),
            'total_price': booking.total_price,
            'payment_method': booking.payment_method,
            'payment_status': booking.payment_status
        }
        email_result = send_booking_modification(booking_data, booking.guest.email)
        logging.info(f"Modification email send result for {booking.guest.email}, booking {booking.reference}: {email_result}")

        flash('Booking modified successfully. A confirmation email has been sent.', 'modal_type=success')
        return redirect(url_for('booking_lookup'))
    form.check_in.data = booking.check_in
    form.check_out.data = booking.check_out
    form.room_category.data = 0
    return render_template('modify_booking.html', form=form, booking=booking)


@app.route('/api/available_rooms', methods=['GET'])
def api_available_rooms():
    from datetime import date
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    exclude_booking_id = request.args.get('exclude_booking_id', type=int)

    try:
        check_in = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out, '%Y-%m-%d').date()
        available_rooms = get_available_rooms(check_in, check_out, exclude_booking_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format or parameters'}), 400

    # Group rooms by category and select one random room per category
    from random import choice
    rooms_by_category = {}
    for room in available_rooms:
        category_id = room.category_id
        if category_id not in rooms_by_category:
            rooms_by_category[category_id] = []
        rooms_by_category[category_id].append(room)

    # Format response with one random room per category
    result = [
        {
            'category_id': category_id,
            'category_name': Room.query.filter_by(category_id=category_id).first().category.name,
            'room_number': choice(rooms).room_number
        }
        for category_id, rooms in rooms_by_category.items()
    ]

    return jsonify({'rooms': result})


@app.route('/cancel_booking/<booking_reference>')
def cancel_booking(booking_reference):
    booking = Booking.query.filter_by(reference=booking_reference).first_or_404()
    cancellation_deadline = booking.check_in - timedelta(days=2)
    if not (
            booking.payment_status == 'paid' and
            booking.status != 'cancelled' and
            datetime.utcnow().date() <= cancellation_deadline):
        flash('This booking cannot be cancelled. Cancellations require payment to be completed and must be done more than 48 hours before check-in.', 'modal_type=error')
        return redirect(url_for('booking_lookup'))

    booking.status = 'cancelled'
    booking.payment_status = 'cancelled'
    booking.cancelled_at = datetime.utcnow()
    if booking.payment_status == 'paid':
        payment = Payment(
            booking_id=booking.id,
            amount=-booking.total_price,
            method=booking.payment_method,
            status='completed',
            processed_at=datetime.utcnow()
        )
        db.session.add(payment)
    db.session.commit()

    # Send cancellation email
    booking_data = {
        'id': booking.id,
        'reference': booking.reference,
        'room_type': booking.room.category.name,
        'check_in': booking.check_in.strftime('%Y-%m-%d'),
        'check_out': booking.check_out.strftime('%Y-%m-%d'),
        'total_price': booking.total_price,
        'payment_method': booking.payment_method
    }
    email_result = send_booking_cancellation(booking_data, booking.guest.email)
    logging.info(f"Cancellation email send result for {booking.guest.email}, booking {booking.reference}: {email_result}")

    flash('Booking cancelled successfully. A refund will be processed promptly if applicable.', 'modal_type=success')
    return redirect(url_for('booking_lookup'))

@app.route('/receptionist/cancel_booking/<int:booking_id>', methods=['GET'])
@login_required
@staff_required
def receptionist_cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    cancellation_deadline = booking.check_in - timedelta(days=2)
    if booking.status == 'cancelled':
        flash('Booking already cancelled.', 'modal_type=error')
    elif booking.status == 'checked_out':
        flash('Cannot cancel a checked-out booking.', 'modal_type=error')
    elif booking.check_in < date.today():
        flash('Cannot cancel past bookings.', 'modal_type=error')
    elif booking.payment_status == 'paid' and datetime.utcnow().date() > cancellation_deadline:
        flash('Paid bookings cannot be cancelled within 48 hours of check-in.', 'modal_type=error')
    else:
        booking.status = 'cancelled'
        booking.payment_status = 'cancelled'
        booking.cancelled_at = datetime.utcnow()
        if booking.payment_status == 'paid':
            payment = Payment(
                booking_id=booking.id,
                amount=-booking.total_price,
                method=booking.payment_method,
                status='completed',
                processed_at=datetime.utcnow()
            )
            db.session.add(payment)
        db.session.commit()

        # Send cancellation email
        booking_data = {
            'id': booking.id,
            'reference': booking.reference,
            'room_type': booking.room.category.name,
            'check_in': booking.check_in.strftime('%Y-%m-%d'),
            'check_out': booking.check_out.strftime('%Y-%m-%d'),
            'total_price': booking.total_price,
            'payment_method': booking.payment_method
        }
        email_result = send_booking_cancellation(booking_data, booking.guest.email)
        logging.info(f"Cancellation email send result for {booking.guest.email}, booking {booking.reference}: {email_result}")

        flash('Booking cancelled successfully. A refund will be processed promptly if applicable.', 'modal_type=success')
    return redirect(url_for('receptionist_manage_bookings'))


@app.route('/cancel_booking_admin/<int:booking_id>', methods=['GET'])
@login_required
@admin_required
def cancel_booking_admin(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    cancellation_deadline = booking.check_in - timedelta(days=2)
    if booking.status == 'cancelled':
        flash('Booking already cancelled.', 'modal_type=error')
    elif booking.status == 'checked_out':
        flash('Cannot cancel a checked-out booking.', 'modal_type=error')
    elif booking.check_in < date.today():
        flash('Cannot cancel past bookings.', 'modal_type=error')
    elif booking.payment_status == 'paid' and datetime.utcnow().date() > cancellation_deadline:
        flash('Paid bookings cannot be cancelled within 48 hours of check-in.', 'modal_type=error')
    else:
        booking.status = 'cancelled'
        booking.payment_status = 'cancelled'
        booking.cancelled_at = datetime.utcnow()
        if booking.payment_status == 'paid':
            payment = Payment(
                booking_id=booking.id,
                amount=-booking.total_price,
                method=booking.payment_method,
                status='completed',
                processed_at=datetime.utcnow()
            )
            db.session.add(payment)
        db.session.commit()

        # Send cancellation email
        booking_data = {
            'id': booking.id,
            'reference': booking.reference,
            'room_type': booking.room.category.name,
            'check_in': booking.check_in.strftime('%Y-%m-%d'),
            'check_out': booking.check_out.strftime('%Y-%m-%d'),
            'total_price': booking.total_price,
            'payment_method': booking.payment_method
        }
        email_result = send_booking_cancellation(booking_data, booking.guest.email)
        logging.info(f"Cancellation email send result for {booking.guest.email}, booking {booking.reference}: {email_result}")

        flash('Booking cancelled successfully. A refund will be processed promptly if applicable.', 'modal_type=success')
    return redirect(url_for('manage_bookings'))


@app.route('/admin/room/change_state/<int:room_id>', methods=['POST'])
@login_required
@admin_required
def change_room_state(room_id):
    room = Room.query.get_or_404(room_id)
    new_state = request.form.get('status')
    valid_states = ['available', 'occupied', 'dirty', 'maintenance']

    if new_state not in valid_states:
        flash('Invalid room status.', 'modal_type=error')
        return redirect(url_for('manage_rooms'))

    # Validation checks
    if new_state == 'occupied':
        active_booking = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.status == 'checked_in'
        ).first()
        if not active_booking:
            flash('Cannot set room to occupied without an active checked-in booking.', 'modal_type=error')
            return redirect(url_for('manage_rooms'))
    elif new_state == 'dirty':
        room.dirty_until = datetime.utcnow() + timedelta(hours=2)  # Set 2-hour cleaning window
    elif new_state == 'available' and room.status == 'dirty':
        room.dirty_until = None  # Clear cleaning timer

    room.status = new_state
    db.session.commit()
    flash(f'Room {room.room_number} status updated to {new_state}.', 'modal_type=success')
    return redirect(url_for('manage_rooms'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('receptionist_dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        staff = Staff.query.filter_by(username=form.username.data).first()
        if staff and staff.is_active and check_password_hash(staff.password_hash, form.password.data):
            login_user(staff, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page:
                if staff.role == 'admin':
                    next_page = url_for('admin_dashboard')
                else:
                    next_page = url_for('receptionist_dashboard')
            return redirect(next_page)
        flash('Invalid username or password.', 'modal_type=error')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_bookings = Booking.query.count()
    active_bookings = Booking.query.filter_by(status='confirmed').count()
    total_revenue = db.session.query(func.sum(Booking.total_price)).filter_by(payment_status='paid').scalar() or 0
    occupancy_rate = (active_bookings / Room.query.count() * 100) if Room.query.count() > 0 else 0
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           total_bookings=total_bookings,
                           active_bookings=active_bookings,
                           total_revenue=total_revenue,
                           occupancy_rate=occupancy_rate,
                           recent_bookings=recent_bookings)


@app.route('/admin/staff', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_staff():
    form = StaffForm()
    staff_members = Staff.query.all()
    if form.validate_on_submit():
        staff = Staff(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
            password_hash=generate_password_hash(form.password.data),
            is_active=form.is_active.data
        )
        db.session.add(staff)
        db.session.commit()
        flash('Staff member created successfully!', 'modal_type=success')
        return redirect(url_for('manage_staff'))
    return render_template('admin/manage_staff.html', form=form, staff_members=staff_members)


@app.route('/admin/staff/edit/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def edit_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    form = StaffForm(staff=staff)
    if form.validate_on_submit():
        staff.username = form.username.data
        staff.email = form.email.data
        staff.full_name = form.full_name.data
        staff.role = form.role.data
        staff.is_active = form.is_active.data
        if form.password.data:
            staff.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Staff member updated successfully!', 'modal_type=success')
    return redirect(url_for('manage_staff'))


@app.route('/admin/staff/delete/<int:staff_id>')
@login_required
@admin_required
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    if staff.id == current_user.id:
        flash('You cannot delete your own account.', 'modal_type=error')
    else:
        db.session.delete(staff)
        db.session.commit()
        flash('Staff member deleted successfully!', 'modal_type=success')
    return redirect(url_for('manage_staff'))


@app.route('/admin/bookings')
@login_required
@admin_required
def manage_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/manage_bookings.html', bookings=bookings, today=date.today())


@app.route('/api/booking_details/<int:booking_id>')
@login_required
@admin_required
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return jsonify({
        'payment_status': booking.payment_status,
        'check_in': booking.check_in.strftime('%Y-%m-%d')
    })


@app.route('/admin/rooms', methods=['GET'])
@login_required
@admin_required
def manage_rooms():
    # Get filter parameters for reserved rooms (default to today)
    filter_type = request.args.get('filter', 'today')
    custom_start = request.args.get('start_date')
    custom_end = request.args.get('end_date')

    # Determine date range based on filter
    today = date.today()
    if filter_type == 'today':
        start_date = today
        end_date = today
    elif filter_type == 'tomorrow':
        start_date = today + timedelta(days=1)
        end_date = start_date
    elif filter_type == 'this_week':
        start_date = today
        end_date = today + timedelta(days=6)
    elif filter_type == 'custom' and custom_start and custom_end:
        try:
            start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
            if end_date < start_date:
                flash('End date must be after start date.', 'modal_type=error')
                return redirect(url_for('manage_rooms'))
        except ValueError:
            flash('Invalid date format.', 'modal_type=error')
            return redirect(url_for('manage_rooms'))
    else:
        start_date = today
        end_date = today

    # Query bookings for the date range
    reserved_bookings = Booking.query.join(Room).join(RoomCategory).join(Guest).filter(
        Booking.status.in_(['pending', 'confirmed', 'checked_in']),
        Booking.payment_status != 'cancelled',
        Booking.check_in <= end_date,
        Booking.check_out > start_date
    ).all()

    # Existing room and category data
    categories = RoomCategory.query.order_by(RoomCategory.name).all()
    rooms = Room.query.order_by(Room.room_number).all()
    category_form = RoomCategoryForm()
    room_form = RoomForm()
    room_form.category_id.choices = [(c.id, c.name) for c in categories]

    return render_template(
        'admin/manage_rooms.html',
        categories=categories,
        rooms=rooms,
        category_form=category_form,
        room_form=room_form,
        reserved_bookings=reserved_bookings,
        filter_type=filter_type,
        start_date=start_date,
        end_date=end_date,
        today=today
    )


@app.route('/admin/add_room', methods=['POST'])
@login_required
@admin_required
def add_room():
    form = RoomForm()
    categories = RoomCategory.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    if form.validate_on_submit() and request.form.get('form_type') == 'room':
        existing_room = Room.query.filter_by(room_number=form.room_number.data).first()
        if existing_room:
            flash('Room number already exists.', 'modal_type=error')
        else:
            room = Room(
                room_number=form.room_number.data,
                category_id=form.category_id.data,
                status=form.status.data,
                maintenance_notes=form.maintenance_notes.data
            )
            db.session.add(room)
            db.session.commit()
            flash('Room added successfully!', 'modal_type=success')
        return redirect(url_for('manage_rooms'))
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field}: {error}", 'modal_type=error')
    return redirect(url_for('manage_rooms'))


@app.route('/admin/room/edit/<int:room_id>', methods=['POST'])
@login_required
@admin_required
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    form = RoomForm()
    categories = RoomCategory.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    if form.validate_on_submit() and request.form.get('form_type') == 'room':
        existing_room = Room.query.filter(Room.room_number == form.room_number.data, Room.id != room_id).first()
        if existing_room:
            flash('Room number already exists.', 'modal_type=error')
        else:
            room.room_number = form.room_number.data
            room.category_id = form.category_id.data
            room.status = form.status.data
            room.maintenance_notes = form.maintenance_notes.data
            db.session.commit()
            flash('Room updated successfully!', 'modal_type=success')
        return redirect(url_for('manage_rooms'))
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field}: {error}", 'modal_type=error')
    return redirect(url_for('manage_rooms'))


@app.route('/admin/room/delete/<int:room_id>')
@login_required
@admin_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    active_booking = Booking.query.filter(
        Booking.room_id == room.id,
        Booking.status.in_(['confirmed', 'checked_in'])
    ).first()
    if active_booking:
        flash('Cannot delete room with active bookings.', 'modal_type=error')
    elif room.status in ['occupied', 'dirty']:
        flash('Cannot delete room in occupied or dirty state.', 'modal_type=error')
    else:
        db.session.delete(room)
        db.session.commit()
        flash('Room deleted successfully!', 'modal_type=success')
    return redirect(url_for('manage_rooms'))


@app.route('/admin/reports')
@login_required
@admin_required
def reports():
    monthly_revenue = db.session.query(
        extract('year', Booking.created_at).label('year'),
        extract('month', Booking.created_at).label('month'),
        func.sum(Booking.total_price).label('revenue')
    ).filter_by(payment_status='paid').group_by('year', 'month').order_by('year', 'month').all()
    booking_status = db.session.query(
        Booking.status,
        func.count(Booking.id).label('count')
    ).group_by(Booking.status).all()
    category_bookings = db.session.query(
        RoomCategory.name,
        func.count(Booking.id).label('bookings')
    ).join(Room, Booking.room_id == Room.id).join(RoomCategory, Room.category_id == RoomCategory.id).group_by(
        RoomCategory.name).all()
    current_date = datetime.utcnow().strftime('%Y-%m')
    return render_template('admin/reports.html',
                           monthly_revenue=monthly_revenue,
                           booking_status=booking_status,
                           category_bookings=category_bookings,
                           current_date=current_date)


@app.route('/receptionist/dashboard')
@login_required
def receptionist_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    today = date.today()
    checkins_today = Booking.query.filter_by(check_in=today, status='confirmed').count()
    checkouts_today = Booking.query.filter_by(check_out=today, status='checked_in').count()
    pending_payments = Booking.query.filter_by(payment_status='unpaid').count()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    todays_checkins = [booking for booking in recent_bookings if
                       booking.check_in == today and booking.status == 'confirmed']
    return render_template('receptionist/dashboard.html',
                           checkins_today=checkins_today,
                           checkouts_today=checkouts_today,
                           pending_payments=pending_payments,
                           recent_bookings=recent_bookings,
                           todays_checkins=todays_checkins)


@app.route('/receptionist/bookings', methods=['GET'])
@login_required
def receptionist_manage_bookings():
    from datetime import date, timedelta, datetime
    if current_user.role == 'admin':
        return redirect(url_for('manage_bookings'))

    # Get filter parameters for reserved rooms (default to today)
    filter_type = request.args.get('filter', 'today')
    custom_start = request.args.get('start_date')
    custom_end = request.args.get('end_date')

    # Determine date range
    today = date.today()
    if filter_type == 'today':
        start_date = today
        end_date = today
    elif filter_type == 'tomorrow':
        start_date = today + timedelta(days=1)
        end_date = start_date
    elif filter_type == 'this_week':
        start_date = today
        end_date = today + timedelta(days=6)
    elif filter_type == 'custom' and custom_start and custom_end:
        try:
            start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
            if end_date < start_date:
                flash('End date must be after start date.', 'modal_type=error')
                return redirect(url_for('receptionist_manage_bookings'))
        except ValueError:
            flash('Invalid date format.', 'modal_type=error')
            return redirect(url_for('receptionist_manage_bookings'))
    else:
        start_date = today
        end_date = today

    # Query bookings for the date range
    reserved_bookings = Booking.query.join(Room).join(RoomCategory).join(Guest).filter(
        Booking.status.in_(['pending', 'confirmed', 'checked_in']),
        Booking.payment_status != 'cancelled',
        Booking.check_in <= end_date,
        Booking.check_out > start_date
    ).all()

    # Existing bookings data
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    today_checkins_count = len(
        [booking for booking in bookings if booking.check_in == today and booking.status == 'confirmed'])
    today_checkouts_count = len(
        [booking for booking in bookings if booking.check_out == today and booking.status == 'checked_in'])

    # Fetch categories for room category filter
    categories = RoomCategory.query.order_by(RoomCategory.name).all()

    return render_template(
        'receptionist/manage_bookings.html',
        bookings=bookings,
        today_checkins_count=today_checkins_count,
        today_checkouts_count=today_checkouts_count,
        today=today,
        tomorrow=today + timedelta(days=1),
        reserved_bookings=reserved_bookings,
        filter_type=filter_type,
        start_date=start_date,
        end_date=end_date,
        categories=categories
    )


@app.route('/receptionist/room_status', methods=['GET'])
@login_required
def receptionist_room_status():
    from datetime import date
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    today = date.today()
    active_bookings = Booking.query.filter(
        Booking.check_in <= today,
        Booking.check_out >= today,
        Booking.status.in_(['confirmed', 'checked_in'])
    ).all()
    booked_room_ids = {booking.room_id for booking in active_bookings}
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(status='available').count()
    occupied_rooms = Room.query.filter_by(status='occupied').count()
    dirty_rooms = Room.query.filter_by(status='dirty').count()
    maintenance_rooms = Room.query.filter_by(status='maintenance').count()

    return jsonify({
        'total': {
            'available': available_rooms,
            'occupied': occupied_rooms,
            'dirty': dirty_rooms,
            'maintenance': maintenance_rooms}
    })


@app.route('/admin/category/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    form = RoomCategoryForm()
    if form.validate_on_submit() and request.form.get('form_type') == 'category':
        category = RoomCategory(
            name=form.name.data,
            base_price=form.base_price.data,
            capacity=form.capacity.data,
            description=form.description.data,
            amenities=form.amenities.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'modal_type=success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'modal_type=error')
    return redirect(url_for('manage_rooms'))


@app.route('/admin/category/edit/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def edit_category(category_id):
    category = RoomCategory.query.get_or_404(category_id)
    form = RoomCategoryForm()
    if form.validate_on_submit() and request.form.get('form_type') == 'category':
        category.name = form.name.data
        category.base_price = form.base_price.data
        category.capacity = form.capacity.data
        category.description = form.description.data
        category.amenities = form.amenities.data
        db.session.commit()
        flash('Category updated successfully!', 'modal_type=success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'modal_type=error')
    return redirect(url_for('manage_rooms'))


@app.route('/admin/category/delete/<int:category_id>')
@login_required
@admin_required
def delete_category(category_id):
    category = RoomCategory.query.get_or_404(category_id)
    if category.rooms:
        flash('Cannot delete category with associated rooms.', 'modal_type=error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'modal_type=success')
    return redirect(url_for('manage_rooms'))


@app.route('/api/reserved_rooms', methods=['GET'])
@login_required
@staff_required
def api_reserved_rooms():
    from datetime import date, timedelta, datetime
    # Get filter parameters
    filter_type = request.args.get('filter', 'today')
    custom_start = request.args.get('start_date')
    custom_end = request.args.get('end_date')
    category_id = request.args.get('category_id', type=int)

    # Determine date range
    today = date.today()
    if filter_type == 'today':
        start_date = today
        end_date = today
    elif filter_type == 'tomorrow':
        start_date = today + timedelta(days=1)
        end_date = start_date
    elif filter_type == 'this_week':
        start_date = today
        end_date = today + timedelta(days=6)
    elif filter_type == 'custom' and custom_start and custom_end:
        try:
            start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
            if end_date < start_date:
                return jsonify({'error': 'End date must be after start date'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    else:
        start_date = today
        end_date = today

    # Build query
    query = Booking.query.join(Room).join(RoomCategory).join(Guest).filter(
        Booking.status.in_(['pending', 'confirmed', 'checked_in']),
        Booking.payment_status != 'cancelled',
        Booking.check_in <= end_date,
        Booking.check_out > start_date
    )
    if category_id:
        query = query.filter(Room.category_id == category_id)

    reserved_bookings = query.all()

    # Format response
    bookings_data = [
        {
            'room_number': booking.room.room_number,
            'category': booking.room.category.name,
            'guest': booking.guest.name,
            'reference': booking.reference,
            'check_in': booking.check_in.strftime('%d %B %Y'),
            'check_out': booking.check_out.strftime('%d %B %Y'),
            'status': booking.status.replace('_', ' ').title()
        } for booking in reserved_bookings
    ]

    return jsonify({
        'bookings': bookings_data,
        'filter_type': filter_type,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    })


@app.route('/receptionist/mark_room_clean/<int:room_id>')
@login_required
@staff_required
def mark_room_clean(room_id):
    room = Room.query.get_or_404(room_id)
    if room.status == 'dirty':
        room.status = 'available'
        room.dirty_until = None  # Reset timer
        db.session.commit()
        flash('Room marked as clean.', 'modal_type=success')
    else:
        flash('Room is not in a dirty state.', 'modal_type=error')
    return redirect(url_for('receptionist_room_status'))


@app.route('/mark_paid/<int:booking_id>')
@login_required
@staff_required
def mark_paid(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.status in ['cancelled', 'checked_out']:
        flash('Cannot mark payment for cancelled or checked-out bookings.', 'modal_type=error')
    elif booking.payment_status == 'paid':
        flash('Booking is already paid.', 'modal_type=error')
    else:
        deposit_amount = booking.total_price * 0.5 if booking.payment_method == 'in-person' else booking.total_price
        booking.payment_status = 'paid'
        booking.status = 'confirmed'
        payment = Payment(
            booking_id=booking.id,
            amount=deposit_amount,
            method=booking.payment_method,
            status='completed',
            processed_at=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()

        # Send payment confirmation email
        booking_data = {
            'id': booking.id,
            'reference': booking.reference,
            'room_type': booking.room.category.name,
            'check_in': booking.check_in.strftime('%Y-%m-%d'),
            'check_out': booking.check_out.strftime('%Y-%m-%d'),
            'total_price': booking.total_price,
            'amount_paid': deposit_amount,
            'payment_method': booking.payment_method
        }
        email_result = send_payment_confirmation(booking_data, booking.guest.email)
        logging.info(f"Payment confirmation email send result for {booking.guest.email}, booking {booking.reference}: {email_result}")

        flash('Payment updated successfully. A confirmation email has been sent.', 'modal_type=success')
    return redirect(request.referrer or url_for('receptionist_dashboard'))


@app.route('/check_in/<int:booking_id>')
@login_required
@staff_required
def check_in(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    today = date.today()
    if booking.payment_status != 'paid' or booking.status != 'confirmed':
        flash('Booking must be paid and confirmed.', 'modal_type=error')
    elif booking.check_in != today:
        flash('Check-in is only allowed on the booking’s check-in date.', 'modal_type=error')
    else:
        active_check_in = Booking.query.filter(
            Booking.room_id == booking.room_id,
            Booking.status == 'checked_in'
        ).count()
        if active_check_in > 0:
            flash('Room is already checked in by another booking.', 'modal_type=error')
        else:
            booking.status = 'checked_in'
            room = Room.query.get(booking.room_id)
            room.status = 'occupied'
            db.session.commit()
            flash('Guest checked in successfully!', 'modal_type=success')
    return redirect(request.referrer or url_for('receptionist_dashboard'))


@app.route('/check_out/<int:booking_id>')
@login_required
@staff_required
def check_out(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    today = date.today()
    if booking.status != 'checked_in':
        flash('Guest must be checked in first.', 'modal_type=error')
    elif booking.check_out < today:
        flash('Check-out date has passed. Please contact management.', 'modal_type=error')
    else:
        booking.status = 'checked_out'
        room = Room.query.get(booking.room_id)
        room.status = 'dirty'
        room.dirty_until = datetime.utcnow() + timedelta(hours=CLEANING_DURATION_HOURS)
        db.session.commit()
        flash('Guest checked out successfully!', 'modal_type=success')
    return redirect(request.referrer or url_for('receptionist_dashboard'))


@app.route('/api/revenue_data')
@login_required
@admin_required
def revenue_data():
    date_range = request.args.get('date_range', 'last_30_days')
    custom_month = request.args.get('custom_month')
    end_date = datetime.utcnow()
    if date_range == 'custom' and custom_month:
        year, month = map(int, custom_month.split('-'))
        start_date = datetime(year, month, 1)
        end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
    else:
        if date_range == 'last_30_days':
            start_date = end_date - timedelta(days=30)
        elif date_range == 'last_3_months':
            start_date = end_date - timedelta(days=90)
        elif date_range == 'last_6_months':
            start_date = end_date - timedelta(days=180)
        elif date_range == 'last_year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = datetime.min
    monthly_revenue = db.session.query(
        extract('year', Booking.created_at).label('year'),
        extract('month', Booking.created_at).label('month'),
        func.sum(Booking.total_price).label('revenue')
    ).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= start_date,
        Booking.created_at <= end_date
    ).group_by('year', 'month').order_by('year', 'month').all()
    data = {
        'labels': [f"{int(r.year)}-{int(r.month):02d}" for r in monthly_revenue],
        'data': [float(r.revenue) for r in monthly_revenue]
    }
    return jsonify(data)


@app.route('/api/booking_status_data')
@login_required
@admin_required
def booking_status_data():
    date_range = request.args.get('date_range', 'last_30_days')
    custom_month = request.args.get('custom_month')
    end_date = datetime.utcnow()
    if date_range == 'custom' and custom_month:
        year, month = map(int, custom_month.split('-'))
        start_date = datetime(year, month, 1)
        end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
    else:
        if date_range == 'last_30_days':
            start_date = end_date - timedelta(days=30)
        elif date_range == 'last_3_months':
            start_date = end_date - timedelta(days=90)
        elif date_range == 'last_6_months':
            start_date = end_date - timedelta(days=180)
        elif date_range == 'last_year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = datetime.min
    booking_status = db.session.query(
        Booking.status,
        func.count(Booking.id).label('count')
    ).filter(
        Booking.created_at >= start_date,
        Booking.created_at <= end_date
    ).group_by(Booking.status).all()
    data = {
        'labels': [s.status.replace('_', ' ').title() for s in booking_status],
        'data': [s.count for s in booking_status]
    }
    return jsonify(data)


@app.route('/api/occupancy_data')
@login_required
@admin_required
def occupancy_data():
    date_range = request.args.get('date_range', 'last_30_days')
    custom_month = request.args.get('custom_month')
    print(f"Occupancy API called with date_range={date_range}, custom_month={custom_month}")
    end_date = datetime.utcnow()
    total_rooms = db.session.query(Room).count()
    print(f"Total rooms: {total_rooms}")
    if date_range == 'custom' and custom_month:
        try:
            year, month = map(int, custom_month.split('-'))
            start_date = datetime(year, month, 1)
            end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
            days_in_month = (end_date - start_date).days + 1
            labels = [(start_date + timedelta(days=i)).strftime('%d %b %Y') for i in range(days_in_month)]
            data = []
            for i in range(days_in_month):
                day = start_date + timedelta(days=i)
                occupied_rooms = db.session.query(Booking).filter(
                    Booking.check_in <= day,
                    Booking.check_out > day,
                    Booking.status.in_(['confirmed', 'checked_in'])
                ).count()
                print(f"Day {day.strftime('%Y-%m-%d')}: {occupied_rooms} occupied rooms")
                occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
                data.append(round(occupancy_rate, 1))
        except Exception as e:
            print(f"Error in daily occupancy: {e}")
            labels = [(start_date + timedelta(days=i)).strftime('%d %b %Y') for i in range(days_in_month)]
            data = [0] * days_in_month
    else:
        if date_range == 'last_30_days':
            start_date = end_date - timedelta(days=30)
        elif date_range == 'last_3_months':
            start_date = end_date - timedelta(days=90)
        elif date_range == 'last_6_months':
            start_date = end_date - timedelta(days=180)
        elif date_range == 'last_year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = datetime.min
        monthly_occupancy = db.session.query(
            extract('year', Booking.check_in).label('year'),
            extract('month', Booking.check_in).label('month'),
            func.count(Booking.id).label('bookings')
        ).filter(
            Booking.check_in >= start_date,
            Booking.check_in <= end_date,
            Booking.status.in_(['confirmed', 'checked_in'])
        ).group_by('year', 'month').order_by('year', 'month').all()
        print(f"Monthly occupancy results: {[(m.year, m.month, m.bookings) for m in monthly_occupancy]}")
        labels = [f"{int(m.year)}-{int(m.month):02d}" for m in monthly_occupancy] if monthly_occupancy else [
            end_date.strftime('%Y-%m')]
        data = []
        for m in monthly_occupancy:
            days_booked = db.session.query(
                func.sum(func.datediff(Booking.check_out, Booking.check_in))
            ).filter(
                extract('year', Booking.check_in) == m.year,
                extract('month', Booking.check_in) == m.month,
                Booking.status.in_(['confirmed', 'checked_in'])
            ).scalar() or 0
            print(f"Month {m.year}-{m.month}: {days_booked} days booked")
            days_in_month = (datetime(int(m.year), int(m.month) + 1, 1) - datetime(int(m.year), int(m.month),
                                                                                   1)).days if m.month < 12 else 31
            occupancy_rate = (days_booked / (
                    total_rooms * days_in_month) * 100) if total_rooms > 0 and days_in_month > 0 else 0
            data.append(round(occupancy_rate, 1))
        if not monthly_occupancy:
            data = [0]
    return jsonify({'labels': labels, 'data': data})


@app.route('/api/category_revenue_data')
@login_required
@admin_required
def category_revenue_data():
    date_range = request.args.get('date_range', 'last_30_days')
    custom_month = request.args.get('custom_month')
    print(f"Category revenue API called with date_range={date_range}, custom_month={custom_month}")
    end_date = datetime.utcnow()
    if date_range == 'custom' and custom_month:
        year, month = map(int, custom_month.split('-'))
        start_date = datetime(year, month, 1)
        end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
    else:
        if date_range == 'last_30_days':
            start_date = end_date - timedelta(days=30)
        elif date_range == 'last_3_months':
            start_date = end_date - timedelta(days=90)
        elif date_range == 'last_6_months':
            start_date = end_date - timedelta(days=180)
        elif date_range == 'last_year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = datetime.min
    all_categories = db.session.query(RoomCategory.name).all()
    category_revenue = db.session.query(
        RoomCategory.name,
        func.sum(Booking.total_price).label('revenue')
    ).join(Room, Booking.room_id == Room.id).join(RoomCategory, Room.category_id == RoomCategory.id).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= start_date,
        Booking.created_at <= end_date
    ).group_by(RoomCategory.name).all()
    print(f"Category revenue results: {[(c.name, c.revenue) for c in category_revenue]}")
    category_map = {c.name: float(c.revenue or 0) for c in category_revenue}
    labels = [c[0] for c in all_categories]
    data = [category_map.get(c[0], 0) for c in all_categories]
    if not labels:
        labels = ['No Categories']
        data = [0]
        print("No room categories found")
    return jsonify({'labels': labels, 'data': data})
