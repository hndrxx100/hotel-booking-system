from flask import Blueprint, jsonify, request
from app.models import Booking, Room, Guest
from app import db
from sqlalchemy.exc import OperationalError
from datetime import date, datetime
from app.routes.dashboard_routes import has_overlapping_booking, update_room_status
import logging
import traceback
import time

booking_bp = Blueprint('booking', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@booking_bp.route('/create_booking', methods=['POST'])
def create_booking():
    data = request.get_json()
    logger.debug(f"create_booking received data: {data}")
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
        return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)', 'code': 'INVALID_DATE_FORMAT'}), 400

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
                    f"Created booking for guest: {email}, room_id: {room_id}, booking_reference: {booking_reference}")
                update_room_status(room_id)
            db.session.commit()
            return jsonify(
                {'message': 'Booking created', 'booking_reference': booking_reference, 'code': 'SUCCESS'}), 200
        except OperationalError as e:
            db.session.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying attempt {attempt + 1}/{max_retries}")
                time.sleep(0.1 * (2 ** attempt))
                continue
            logger.error(f"OperationalError in create_booking: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error in create_booking: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500
        finally:
            db.session.remove()


@booking_bp.route('/search_rooms', methods=['POST'])
def search_available_rooms():
    try:
        data = request.get_json()
        logger.debug(f"search_available_rooms received data: {data}")
        check_in_date = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
        check_out_date = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()

        if check_in_date < date.today():
            return jsonify({'error': 'Check-in date must be today or in the future', 'code': 'INVALID_CHECK_IN'}), 400
        if check_out_date <= check_in_date:
            return jsonify({'error': 'Check-out date must be after check-in date', 'code': 'INVALID_CHECK_OUT'}), 400

        max_retries = 3
        for attempt in range(max_retries):
            try:
                with db.session.begin_nested():
                    # Find rooms with overlapping bookings
                    overlapping_bookings = Booking.query.filter(
                        Booking.check_in_date < check_out_date,
                        Booking.check_out_date > check_in_date,
                        Booking.status.in_(['booked', 'checked-in'])
                    ).with_entities(Booking.room_id).distinct().all()

                    overlapping_room_ids = [booking.room_id for booking in overlapping_bookings]
                    logger.debug(f"Overlapping room IDs: {overlapping_room_ids}")

                    # Get all rooms that are not in overlapping bookings
                    available_rooms = Room.query.filter(
                        ~Room.id.in_(overlapping_room_ids)
                    ).all()

                    logger.debug(
                        f"Available rooms: {[{'id': r.id, 'room_number': r.room_number} for r in available_rooms]}")
                    room_list = [room.to_dict() for room in available_rooms]
                db.session.commit()
                return jsonify({
                    'rooms': room_list,
                    'check_in': check_in_date.strftime('%d %B %Y'),
                    'check_out': check_out_date.strftime('%d %B %Y'),
                    'code': 'SUCCESS'
                }), 200
            except OperationalError as e:
                db.session.rollback()
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying attempt {attempt + 1}/{max_retries}")
                    time.sleep(0.1 * (2 ** attempt))
                    continue
                logger.error(f"OperationalError in search_rooms: {str(e)}\n{traceback.format_exc()}")
                return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
            except Exception as e:
                db.session.rollback()
                logger.error(f"Unexpected error in search_rooms: {str(e)}\n{traceback.format_exc()}")
                return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500
            finally:
                db.session.remove()
    finally:
        print()
