from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
from app.models import Booking, Room, Guest
from app.extensions import db

receptionist_bp = Blueprint('receptionist', __name__)


# ---------------------------- BOOKING MANAGEMENT ----------------------------

@receptionist_bp.route('/receptionist/bookings')
def view_bookings():
    if session.get('role') != 'Receptionist':
        return redirect(url_for('auth.login'))

    bookings = Booking.query.order_by(Booking.check_in_date.desc()).all()
    data = [
        {
            'id': b.id,
            'guest_id': b.guest.id,
            'guest_name': b.guest.full_name,
            'room_number': b.room.room_number,
            'room_type': b.room.room_type,
            'check_in_date': b.check_in_date.strftime('%Y-%m-%d'),
            'check_out_date': b.check_out_date.strftime('%Y-%m-%d'),
            'status': b.status,
            'payment_method': b.payment.payment_method if b.payment else None,
            'is_paid': b.payment.is_successful if b.payment else False
        } for b in bookings
    ]
    return jsonify({'bookings': data})


@receptionist_bp.route('/receptionist/booking/update_status', methods=['POST'])
def update_booking_status():
    booking_id = request.form.get('booking_id')
    status = request.form.get('status')

    booking = Booking.query.get(booking_id)
    if booking:
        booking.status = status
        db.session.commit()
        return jsonify({'success': True, 'message': 'Status updated'})
    return jsonify({'success': False, 'message': 'Booking not found'})


# ---------------------------- ROOM MANAGEMENT ----------------------------

@receptionist_bp.route('/receptionist/rooms')
def get_rooms():
    if session.get('role') != 'Receptionist':
        return redirect(url_for('auth.login'))

    rooms = Room.query.all()
    data = [
        {
            'id': r.id,
            'room_number': r.room_number,
            'room_type': r.room_type,
            'price': r.price,
            'description': r.description
        } for r in rooms
    ]
    return jsonify({'rooms': data})


@receptionist_bp.route('/receptionist/room/add', methods=['POST'])
def add_room():
    number = request.form.get('room_number')
    room_type = request.form.get('room_type')
    price = request.form.get('price')
    desc = request.form.get('description')

    # Validate required fields
    if not number or not room_type or not price:
        return jsonify({'success': False, 'message': 'All required fields must be filled'}), 400

    # Check for duplicate room number
    if Room.query.filter_by(room_number=number).first():
        return jsonify({'success': False, 'message': 'Room number already exists'}), 409

    try:
        new_room = Room(
            room_number=number,
            room_type=room_type,
            price=float(price),
            description=desc,
            is_available=True  # default
        )
        db.session.add(new_room)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Room added successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@receptionist_bp.route('/receptionist/room/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    room = Room.query.get(room_id)
    if room:
        db.session.delete(room)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Room not found'})


# ---------------------------- GUEST MANAGEMENT ----------------------------

@receptionist_bp.route('/receptionist/guests')
def view_guests():
    if session.get('role') != 'Receptionist':
        return redirect(url_for('auth.login'))

    guests = Guest.query.all()
    data = [
        {
            'id': g.id,
            'name': g.full_name,
            'email': g.email,
            'phone': g.phone
        } for g in guests
    ]
    return jsonify({'guests': data})
