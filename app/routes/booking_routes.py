from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask import current_app
from app.models import Booking, Room, Guest
from datetime import datetime
from app.extensions import db

booking_bp = Blueprint('booking', __name__)


@booking_bp.route('/get_available_rooms')
def get_available_rooms():
    checkin = request.args.get('checkin')
    checkout = request.args.get('checkout')

    try:
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d').date()
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'error': 'Invalid date format'}), 400

    booked_rooms = db.session.query(Booking.room_id).filter(
        Booking.check_in_date < checkout_date,
        Booking.check_out_date > checkin_date
    ).subquery()

    available_rooms = Room.query.filter(~Room.id.in_(booked_rooms)).all()

    # Define a default icon for unlisted room types
    default_icon = 'https://static.thenounproject.com/png/1562134-200.png'

    icon_map = {
        'Single': 'https://static.thenounproject.com/png/hotel-room-icon-1562134-512.png',
        'Double': 'https://static.thenounproject.com/png/hotel-room-icon-1851727-512.png',
        'Suite':  'https://static.thenounproject.com/png/hotel-room-icon-6469206-512.png',
    }

    rooms_data = [
        {
            'id': room.id,
            'name': f'{room.room_type} Room {room.room_number}',
            'category': room.room_type,
            'price_per_night': room.price,
            'description': room.description,
            'image_url': icon_map.get(room.room_type, default_icon)
        }
        for room in available_rooms
    ]

    return jsonify({'rooms': rooms_data})



@booking_bp.route('/submit_booking', methods=['POST'])
def submit_booking():
    data = request.form

    guest = Guest.query.filter_by(email=data.get('guest_email')).first()
    if not guest:
        guest = Guest(
            full_name=data.get('guest_name'),
            email=data.get('guest_email'),
            phone=data.get('guest_phone')
        )
        db.session.add(guest)
        db.session.commit()

    booking = Booking(
        guest_id=guest.id,
        room_id=data.get('room_id'),
        check_in_date=datetime.strptime(data.get('check_in'), '%Y-%m-%d').date(),
        check_out_date=datetime.strptime(data.get('check_out'), '%Y-%m-%d').date(),
        status='Pending'
    )

    db.session.add(booking)
    db.session.commit()

    return jsonify({'success': True})


@booking_bp.route('/add_room', methods=['POST'])
def add_room():
    # your existing add room logic
    ...


@booking_bp.route('/get_all_rooms')
def get_all_rooms():
    rooms = Room.query.all()

    data = [
        {
            'id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'price': room.price,
            'description': room.description
        }
        for room in rooms
    ]

    return jsonify({'rooms': data})


@booking_bp.route('/my_bookings')
def my_bookings():
    if 'guest_id' not in session:
        flash('Please log in to view your bookings.', 'error')
        return redirect(url_for('auth.guest_login'))

    bookings = Booking.query.filter_by(guest_id=session['guest_id']).all()

    return render_template('guest_dashboard.html', bookings=bookings)

