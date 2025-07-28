from flask import Blueprint, jsonify, request, session, redirect, render_template, url_for
from app import db
from app.models import Booking, Room, Guest, Receptionist
from sqlalchemy.exc import IntegrityError, OperationalError
import logging
import traceback
from datetime import date, datetime, timedelta
import time

dashboard_bp = Blueprint('dashboard', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def has_overlapping_booking(room_id, check_in, check_out, exclude_booking_id=None):
    query = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.status.in_(['booked', 'checked-in']),
        Booking.check_in_date < check_out,
        Booking.check_out_date > check_in
    )
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    logger.debug(
        f"Checking overlapping booking for room_id: {room_id}, check_in: {check_in}, check_out: {check_out}, exclude_booking_id: {exclude_booking_id}")
    return query.first()


def update_room_status(room_id):
    room = db.session.get(Room, room_id)
    if not room:
        logger.debug(f"Room not found for room_id: {room_id}")
        return
    active_bookings = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.status.in_(['booked', 'checked-in']),
        Booking.check_out_date >= date.today()
    ).first()
    new_status = 'available' if not active_bookings else 'booked'
    if room.status != new_status:
        logger.debug(f"Updating room_id: {room_id} status from {room.status} to {new_status}")
        room.status = new_status
    else:
        logger.debug(f"No status change needed for room_id: {room_id}, current status: {room.status}")


def custom_paginate(query, page, per_page):
    """Custom pagination to avoid 404 for empty pages."""
    total = query.count()
    start = (page - 1) * per_page
    end = start + per_page
    items = query.slice(start, end).all()
    return {
        'items': items,
        'page': page,
        'total': total,
        'pages': max(1, (total + per_page - 1) // per_page)
    }


@dashboard_bp.route('/receptionist/rooms/search', methods=['POST'])
def search_rooms():
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    data = request.get_json()
    logger.debug(f"search_rooms received data: {data}")
    check_in_date = data.get('check_in_date')
    check_out_date = data.get('check_out_date')
    room_type = data.get('room_type')

    try:
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        if check_in < date.today():
            return jsonify({'error': 'Check-in date must be today or in the future', 'code': 'INVALID_CHECK_IN'}), 400
        if check_out <= check_in:
            return jsonify({'error': 'Check-out date must be after check-in date', 'code': 'INVALID_CHECK_OUT'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)', 'code': 'INVALID_DATE_FORMAT'}), 400

    try:
        query = Room.query
        if room_type and room_type in ['Single', 'Double', 'Suite']:
            query = query.filter(Room.room_type == room_type)
        all_rooms = query.all()

        available_rooms = []
        for room in all_rooms:
            if not has_overlapping_booking(room.id, check_in, check_out):
                available_rooms.append({
                    'id': room.id,
                    'room_number': room.room_number,
                    'room_type': room.room_type,
                    'price': float(room.price),
                    'status': room.status
                })

        logger.debug(f"Found {len(available_rooms)} available rooms")
        return jsonify(available_rooms), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in search_rooms: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in search_rooms: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in search_rooms: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/bookings/walkin', methods=['POST'])
def create_walkin_booking():
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    data = request.get_json()
    logger.debug(f"create_walkin_booking received data: {data}")
    full_name = data.get('full_name')
    email = data.get('email')
    phone = data.get('phone')
    room_id = data.get('room_id')
    check_in_date = data.get('check_in_date')
    check_out_date = data.get('check_out_date')
    request_id = data.get('request_id')
    if not all([full_name, email, phone, room_id, check_in_date, check_out_date, request_id]):
        return jsonify({'error': 'Missing required fields, including request_id', 'code': 'MISSING_DATA'}), 400
    try:
        room_id = int(room_id)
        if room_id <= 0:
            return jsonify({'error': 'Invalid room ID', 'code': 'INVALID_ROOM_ID'}), 400
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        if check_in < date.today():
            return jsonify({'error': 'Check-in date must be today or in the future', 'code': 'INVALID_CHECK_IN'}), 400
        if check_out <= check_in:
            return jsonify({'error': 'Check-out date must be after check-in date', 'code': 'INVALID_CHECK_OUT'}), 400
    except ValueError as e:
        logger.error(f"Invalid input: {str(e)}")
        return jsonify({'error': 'Invalid room ID or date format (use YYYY-MM-DD)', 'code': 'INVALID_DATE_FORMAT'}), 400
    room = db.session.get(Room, room_id)
    if not room:
        return jsonify({'error': 'Room not found', 'code': 'ROOM_NOT_FOUND'}), 404
    existing_booking = Booking.query.filter_by(booking_reference=f"PL{request_id[-5:]}").first()
    if existing_booking:
        logger.warning(f"Duplicate booking request detected: request_id={request_id}")
        return jsonify({'error': 'Duplicate booking request', 'code': 'DUPLICATE_REQUEST'}), 400
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with db.session.begin_nested():
                if has_overlapping_booking(room_id, check_in, check_out):
                    return jsonify({'error': 'Room is booked for the selected dates', 'code': 'ROOM_BOOKED'}), 400
                guest = Guest.query.filter_by(email=email).first()
                if not guest:
                    guest = Guest(full_name=full_name, email=email, phone=phone)
                    db.session.add(guest)
                    db.session.flush()
                    logger.debug(f"Created new guest: {email}")
                booking = Booking(
                    guest_id=guest.id,
                    room_id=room_id,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    status='booked',
                    payment_status='pending'
                )
                db.session.add(booking)
                db.session.flush()
                booking_reference = booking.booking_reference
                logger.debug(
                    f"Created walk-in booking for guest: {email}, room_id: {room_id}, booking_reference: {booking_reference}")
                update_room_status(room_id)
            db.session.commit()
            return jsonify({
                'message': 'Booking created',
                'booking_reference': booking_reference,
                'booking': booking.to_dict(),
                'code': 'SUCCESS'
            }), 200
        except OperationalError as e:
            db.session.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying attempt {attempt + 1}/{max_retries}")
                time.sleep(0.1 * (2 ** attempt))
                continue
            logger.error(f"OperationalError in create_walkin_booking: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"IntegrityError in create_walkin_booking: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error in create_walkin_booking: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/priorities', methods=['GET'])
def get_priorities():
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    logger.debug("Fetching priorities data")
    try:
        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        seven_days_later = today + timedelta(days=7)
        check_ins_today = Booking.query.filter(
            Booking.check_in_date == today,
            Booking.status == 'booked'
        ).count()
        check_outs_today = Booking.query.filter(
            Booking.check_out_date == today,
            Booking.status == 'checked-in'
        ).count()
        overdue_payments = Booking.query.filter(
            Booking.payment_status == 'pending',
            Booking.check_in_date <= today,
            Booking.status.in_(['booked', 'checked-in'])
        ).count()
        recent_bookings = Booking.query.filter(
            Booking.created_at >= seven_days_ago
        ).count()
        upcoming_checkins = Booking.query.filter(
            Booking.check_in_date.between(today, seven_days_later),
            Booking.status == 'booked'
        ).count()
        total_bookings_today = Booking.query.filter(
            Booking.check_in_date <= today,
            Booking.check_out_date >= today,
            Booking.status.in_(['booked', 'checked-in'])
        ).count()
        logger.debug(
            f"Fetched priorities: check_ins={check_ins_today}, check_outs={check_outs_today}, "
            f"overdue_payments={overdue_payments}, recent_bookings={recent_bookings}, "
            f"upcoming_checkins={upcoming_checkins}, total_bookings_today={total_bookings_today}")
        return jsonify({
            'check_ins_today': check_ins_today,
            'check_outs_today': check_outs_today,
            'overdue_payments': overdue_payments,
            'recent_bookings': recent_bookings,
            'upcoming_checkins': upcoming_checkins,
            'total_bookings_today': total_bookings_today
        }), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in get_priorities: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in get_priorities: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in get_priorities: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/dashboard', methods=['GET'])
def receptionist_dashboard():
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    logger.debug("Fetching receptionist dashboard data")
    bookings_page = request.args.get('bookings_page', 1, type=int)
    rooms_page = request.args.get('rooms_page', 1, type=int)
    status_filter = request.args.get('status', type=str)
    date_range = request.args.get('date_range', type=str)
    try:
        query = Booking.query.order_by(Booking.id.desc())
        if status_filter in ['booked', 'checked-in', 'checked-out', 'cancelled']:
            query = query.filter(Booking.status == status_filter)
        if date_range == 'today':
            query = query.filter(
                Booking.check_in_date <= date.today(),
                Booking.check_out_date >= date.today()
            )
        elif date_range == 'last_7_days':
            query = query.filter(Booking.created_at >= date.today() - timedelta(days=7))
        elif date_range == 'upcoming':
            query = query.filter(
                Booking.check_in_date.between(date.today(), date.today() + timedelta(days=7)),
                Booking.status == 'booked'
            )
        bookings_paginated = custom_paginate(query, bookings_page, 10)
        rooms_paginated = custom_paginate(Room.query.order_by(Room.id), rooms_page, 10)
        bookings = [b.to_dict() for b in bookings_paginated['items']]
        rooms = [{
            'id': r.id,
            'room_number': r.room_number,
            'room_type': r.room_type,
            'price': float(r.price),
            'status': r.status
        } for r in rooms_paginated['items']]
        logger.debug(f"Dashboard data fetched: {len(bookings)} bookings, {len(rooms)} rooms")
        return jsonify({
            'bookings': bookings,
            'rooms': rooms,
            'bookings_pagination': {
                'page': bookings_paginated['page'],
                'total': bookings_paginated['total'],
                'pages': bookings_paginated['pages']
            },
            'rooms_pagination': {
                'page': rooms_paginated['page'],
                'total': rooms_paginated['total'],
                'pages': rooms_paginated['pages']
            }
        }), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in receptionist_dashboard: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in receptionist_dashboard: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in receptionist_dashboard: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/guests', methods=['GET'])
def get_guests():
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    logger.debug("Fetching guests data")
    try:
        guests = Guest.query.all()
        guests_data = [{
            'id': g.id,
            'name': g.full_name,
            'email': g.email,
            'phone': g.phone
        } for g in guests]
        logger.debug(f"Fetched {len(guests_data)} guests")
        return jsonify({'guests': guests_data}), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in get_guests: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in get_guests: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in get_guests: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/booking/search/<string:reference>', methods=['GET'])
def search_booking(reference):
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    logger.debug(f"Searching booking with reference: {reference}")
    try:
        booking = Booking.query.filter_by(booking_reference=reference).first()
        if not booking:
            return jsonify({'error': 'Booking not found', 'code': 'BOOKING_NOT_FOUND'}), 404
        logger.debug(f"Found booking: {booking.to_dict()}")
        return jsonify({'booking': booking.to_dict()}), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in search_booking: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in search_booking: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in search_booking: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/booking/update_payment', methods=['POST'])
def update_payment_status():
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    data = request.get_json()
    logger.debug(f"update_payment_status received data: {data}")
    booking_id = data.get('booking_id')
    new_payment_status = data.get('payment_status')
    logger.debug(f"Processing booking_id: {booking_id}, payment_status: {new_payment_status}")
    if not booking_id or not isinstance(booking_id, int) or booking_id <= 0:
        return jsonify({'error': 'Invalid booking ID', 'code': 'INVALID_BOOKING_ID'}), 400
    if new_payment_status not in ['paid', 'pending']:
        return jsonify({'error': 'Invalid payment status', 'code': 'INVALID_PAYMENT_STATUS'}), 400
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found', 'code': 'BOOKING_NOT_FOUND'}), 404
    if new_payment_status == 'pending' and booking.status in ['checked-in', 'checked-out']:
        return jsonify({'error': 'Cannot set payment to pending for checked-in or checked-out booking',
                        'code': 'INVALID_PAYMENT_UPDATE'}), 400
    try:
        db.session.refresh(booking)
        booking.payment_status = new_payment_status
        db.session.commit()
        logger.debug(f"Payment status updated for booking_id: {booking_id}")
        return jsonify({'message': 'Payment status updated', 'booking': booking.to_dict()}), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in update_payment_status: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in update_payment_status: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in update_payment_status: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/room/add', methods=['POST'])
def add_room():
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    data = request.get_json()
    logger.debug(f"add_room received data: {data}")
    room_number = data.get('room_number')
    room_type = data.get('room_type')
    price = data.get('price')
    if not all([room_number, room_type, price]):
        return jsonify({'error': 'Missing required fields', 'code': 'MISSING_DATA'}), 400
    try:
        existing_room = Room.query.filter_by(room_number=room_number).first()
        if existing_room:
            logger.warning(f"Attempted to add duplicate room: {room_number}")
            return jsonify({'error': 'Room with this number already exists', 'code': 'ROOM_EXISTS'}), 400
        new_room = Room(room_number=room_number, room_type=room_type, price=price, status='available')
        db.session.add(new_room)
        db.session.commit()
        logger.debug(f"Added room: {room_number}")
        return jsonify({'message': 'Room added successfully', 'room': {
            'id': new_room.id,
            'room_number': new_room.room_number,
            'room_type': new_room.room_type,
            'price': float(new_room.price),
            'status': new_room.status
        }}), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in add_room: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Room with this number already exists', 'code': 'ROOM_EXISTS'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in add_room: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in add_room: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/booking/update_status', methods=['POST'])
def update_booking_status():
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    data = request.get_json()
    logger.debug(f"update_booking_status received data: {data}")
    booking_id = data.get('booking_id')
    new_status = data.get('status')
    logger.debug(f"Processing booking_id: {booking_id}, status: {new_status}")
    if not booking_id or not isinstance(booking_id, int) or booking_id <= 0:
        return jsonify({'error': 'Invalid booking ID', 'code': 'INVALID_BOOKING_ID'}), 400
    if new_status not in ['checked-in', 'cancelled']:
        return jsonify({'error': 'Invalid status', 'code': 'INVALID_STATUS'}), 400
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found', 'code': 'BOOKING_NOT_FOUND'}), 404
    if booking.status in ['checked-in', 'checked-out']:
        return jsonify(
            {'error': 'Cannot modify status of checked-in or checked-out booking', 'code': 'INVALID_MODIFICATION'}), 400
    if new_status == 'checked-in' and booking.check_in_date != date.today():
        return jsonify({'error': 'Check-in is only allowed on the check-in date', 'code': 'INVALID_CHECK_IN_DATE'}), 400
    if new_status == 'checked-in' and booking.payment_status != 'paid':
        return jsonify({'error': 'Payment must be completed before check-in', 'code': 'PAYMENT_REQUIRED'}), 400
    try:
        db.session.refresh(booking)
        booking.status = new_status
        if new_status == 'cancelled':
            update_room_status(booking.room_id)
        db.session.commit()
        logger.debug(f"Status updated for booking_id: {booking_id}")
        return jsonify({'message': 'Status updated', 'booking': booking.to_dict()}), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in update_booking_status: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in update_booking_status: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in update_booking_status: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/bookings/checkout', methods=['POST'])
def checkout_guest():
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    data = request.get_json()
    logger.debug(f"checkout_guest received data: {data}")
    booking_id = data.get('booking_id')
    logger.debug(f"Processing booking_id: {booking_id}")
    if not booking_id or not isinstance(booking_id, int) or booking_id <= 0:
        return jsonify({'error': 'Invalid booking ID', 'code': 'INVALID_BOOKING_ID'}), 400
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found', 'code': 'BOOKING_NOT_FOUND'}), 404
    if booking.status != 'checked-in':
        return jsonify({'error': 'Booking must be checked-in to check out', 'code': 'INVALID_CHECKOUT'}), 400
    if booking.payment_status != 'paid':
        return jsonify({'error': 'Payment must be completed before check-out', 'code': 'PAYMENT_REQUIRED'}), 400
    try:
        db.session.refresh(booking)
        booking.status = 'checked-out'
        update_room_status(booking.room_id)
        db.session.commit()
        logger.debug(f"Checked out booking: {booking_id}")
        return jsonify({'message': 'Guest checked out', 'booking': booking.to_dict()}), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in checkout_guest: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in checkout_guest: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in checkout_guest: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/booking/modify/<int:booking_id>', methods=['POST'])
def manage_booking(booking_id):
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    data = request.get_json()
    logger.debug(f"manage_booking received data for booking_id {booking_id}: {data}")
    email = data.get('email')
    room_id = data.get('room_id')
    check_in_date = data.get('check_in_date')
    check_out_date = data.get('check_out_date')
    if not booking_id or not isinstance(booking_id, int) or booking_id <= 0:
        return jsonify({'error': 'Invalid booking ID', 'code': 'INVALID_BOOKING_ID'}), 400
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found', 'code': 'BOOKING_NOT_FOUND'}), 404
    if booking.status in ['checked-in', 'checked-out']:
        return jsonify(
            {'error': 'Cannot modify a checked-in or checked-out booking', 'code': 'INVALID_MODIFICATION'}), 400
    if email:
        guest = db.session.query(Guest).filter_by(email=email).first()
        if not guest:
            return jsonify({'error': 'No guest found with that email', 'code': 'GUEST_NOT_FOUND'}), 404
    if room_id:
        room = db.session.get(Room, room_id)
        if not room:
            return jsonify({'error': 'Room not found', 'code': 'ROOM_NOT_FOUND'}), 404
        if has_overlapping_booking(room_id, check_in_date or booking.check_in_date,
                                   check_out_date or booking.check_out_date, booking_id):
            return jsonify({'error': 'Room is booked for the selected dates', 'code': 'ROOM_BOOKED'}), 400
    try:
        db.session.refresh(booking)
        if email:
            booking.guest_id = guest.id
        if room_id:
            old_room_id = booking.room_id
            booking.room_id = room_id
        if check_in_date:
            try:
                booking.check_in_date = datetime.strptime(check_in_date, '%Y-%m-%d').date()
                if booking.check_in_date < date.today():
                    return jsonify(
                        {'error': 'Check-in date must be today or in the future', 'code': 'INVALID_CHECK_IN'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)', 'code': 'INVALID_DATE_FORMAT'}), 400
        if check_out_date:
            try:
                booking.check_out_date = datetime.strptime(check_out_date, '%Y-%m-%d').date()
                if booking.check_out_date <= booking.check_in_date:
                    return jsonify(
                        {'error': 'Check-out date must be after check-in date', 'code': 'INVALID_CHECK_OUT'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)', 'code': 'INVALID_DATE_FORMAT'}), 400
        if check_in_date or check_out_date:
            if has_overlapping_booking(booking.room_id, booking.check_in_date, booking.check_out_date, booking.id):
                return jsonify({'error': 'Room is booked for the selected dates', 'code': 'ROOM_BOOKED'}), 400
        update_room_status(booking.room_id)
        if room_id and old_room_id != booking.room_id:
            update_room_status(old_room_id)
        db.session.commit()
        logger.debug(f"Modified booking_id: {booking_id}")
        return jsonify({
            'message': 'Booking modified',
            'booking_reference': booking.booking_reference,
            'booking': booking.to_dict(),
            'code': 'SUCCESS'
        }), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in manage_booking: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in manage_booking: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in manage_booking: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/room/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    logger.debug(f"Attempting to delete room_id: {room_id}")
    room = db.session.get(Room, room_id)
    if not room:
        return jsonify({'error': 'Room not found', 'code': 'ROOM_NOT_FOUND'}), 404
    active_bookings = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.status.in_(['booked', 'checked-in']),
        Booking.check_out_date >= date.today()
    ).count()
    if active_bookings > 0:
        logger.warning(f"Cannot delete room_id {room_id}: {active_bookings} active bookings found")
        return jsonify({'error': 'Cannot delete room with active bookings', 'code': 'ROOM_ACTIVE'}), 400
    try:
        db.session.delete(room)
        db.session.commit()
        logger.debug(f"Deleted room_id: {room_id}")
        return jsonify({'message': 'Room deleted successfully', 'room_id': room_id}), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in delete_room: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in delete_room: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in delete_room: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/booking/delete/<int:booking_id>', methods=['POST'])
def delete_booking(booking_id):
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    logger.debug(f"Attempting to delete booking_id: {booking_id}")
    if not booking_id or not isinstance(booking_id, int) or booking_id <= 0:
        return jsonify({'error': 'Invalid booking ID', 'code': 'INVALID_BOOKING_ID'}), 400
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found', 'code': 'BOOKING_NOT_FOUND'}), 404
    if booking.status not in ['checked-out', 'cancelled']:
        return jsonify(
            {'error': 'Can only delete checked-out or cancelled bookings', 'code': 'INVALID_BOOKING_STATUS'}), 400
    try:
        room_id = booking.room_id
        db.session.delete(booking)
        update_room_status(room_id)
        db.session.commit()
        logger.debug(f"Deleted booking_id: {booking_id}")
        return jsonify({'message': 'Booking deleted successfully', 'booking_id': booking_id, 'code': 'SUCCESS'}), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in delete_booking: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in delete_booking: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in delete_booking: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/bookings', methods=['GET'])
def get_bookings():
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    logger.debug("Fetching bookings data")
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    filter_type = request.args.get('filter', 'all')  # Maps to date_range
    search_reference = request.args.get('search_reference', '')

    try:
        query = Booking.query.order_by(Booking.id.desc())
        if status_filter != 'all' and status_filter in ['booked', 'checked-in', 'checked-out', 'cancelled']:
            query = query.filter(Booking.status == status_filter)
        if filter_type == 'today':
            query = query.filter(
                Booking.check_in_date <= date.today(),
                Booking.check_out_date >= date.today()
            )
        elif filter_type == 'week':
            query = query.filter(Booking.created_at >= date.today() - timedelta(days=7))
        elif filter_type == 'upcoming':
            query = query.filter(
                Booking.check_in_date.between(date.today(), date.today() + timedelta(days=7)),
                Booking.status == 'booked'
            )
        if search_reference:
            query = query.filter(Booking.booking_reference.ilike(f'%{search_reference}%'))

        bookings_paginated = custom_paginate(query, page, 10)
        bookings = [b.to_dict() for b in bookings_paginated['items']]

        logger.debug(f"Fetched {len(bookings)} bookings")
        return jsonify({
            'bookings': bookings,
            'pagination': {
                'current_page': bookings_paginated['page'],
                'total_pages': bookings_paginated['pages'],
                'total_items': bookings_paginated['total']
            }
        }), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in get_bookings: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in get_bookings: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in get_bookings: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/rooms', methods=['GET'])
def get_rooms():
    if session.get('role') != 'receptionist':
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    logger.debug("Fetching rooms data")
    page = request.args.get('page', 1, type=int)

    try:
        rooms_paginated = custom_paginate(Room.query.order_by(Room.id), page, 10)
        rooms = [{
            'id': r.id,
            'room_number': r.room_number,
            'room_type': r.room_type,
            'price': float(r.price),
            'status': r.status
        } for r in rooms_paginated['items']]

        logger.debug(f"Fetched {len(rooms)} rooms")
        return jsonify({
            'rooms': rooms,
            'pagination': {
                'current_page': rooms_paginated['page'],
                'total_pages': rooms_paginated['pages'],
                'total_items': rooms_paginated['total']
            }
        }), 200
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError in get_rooms: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database constraint violated', 'code': 'DB_CONSTRAINT'}), 400
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"OperationalError in get_rooms: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in get_rooms: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500


@dashboard_bp.route('/receptionist/dashboard/html')
def receptionist_dashboard_html():
    if session.get('role') != 'receptionist':
        return redirect(url_for('dashboard.login'))
    return render_template('receptionist/receptionist_dashboard.html', today=date.today().isoformat())
