from flask import Blueprint, jsonify, request
from app.models import Booking, Room, Guest
from app import db
from datetime import date, datetime
from app.routes.dashboard_routes import has_overlapping_booking, update_room_status
import logging
import traceback
import time
from sqlalchemy.exc import IntegrityError, OperationalError

manage_booking_bp = Blueprint('manage_booking', __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@manage_booking_bp.route('/manage_booking', methods=['POST'])
def query_booking():
    data = request.get_json()
    logger.debug(f"query_booking received data: {data}")
    email = data.get('email')
    booking_reference = data.get('booking_reference')

    if not all([email, booking_reference]):
        return jsonify({'error': 'Email and booking reference are required', 'code': 'MISSING_DATA'}), 400

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with db.session.begin_nested():
                booking = Booking.query.filter_by(booking_reference=booking_reference).first()
                if not booking:
                    return jsonify({'error': 'Booking not found', 'code': 'BOOKING_NOT_FOUND'}), 404

                if booking.status in ['cancelled', 'checked-out']:
                    return jsonify(
                        {'error': 'This booking has been cancelled or checked out', 'code': 'BOOKING_CANCELLED'}), 404

                guest = Guest.query.get(booking.guest_id)
                if not guest or guest.email.lower() != email.lower():
                    return jsonify({'error': 'No guest found with that email', 'code': 'GUEST_NOT_FOUND'}), 401

                booking_data = {
                    'id': booking.id,
                    'booking_reference': booking.booking_reference,
                    'guest': {'full_name': guest.full_name, 'email': guest.email, 'phone': guest.phone},
                    'room': {
                        'id': booking.room_id,
                        'room_number': booking.room.room_number,
                        'room_type': booking.room.room_type,
                        'price': booking.room.price
                    },
                    'check_in_date': booking.check_in_date.isoformat(),
                    'check_out_date': booking.check_out_date.isoformat(),
                    'status': booking.status,
                    'payment_status': booking.payment_status
                }
            db.session.commit()
            logger.debug(f"Found booking: {booking_reference}")
            return jsonify({'message': 'Booking found', 'booking': booking_data, 'code': 'SUCCESS'}), 200
        except OperationalError as e:
            db.session.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying attempt {attempt + 1}/{max_retries}")
                time.sleep(0.1 * (2 ** attempt))
                continue
            logger.error(f"OperationalError in query_booking: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error in query_booking: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500
        finally:
            db.session.remove()

@manage_booking_bp.route('/available_rooms', methods=['POST'])
def available_rooms():
    data = request.get_json()
    logger.debug(f"available_rooms received data: {data}")
    check_in_date = data.get('check_in_date')
    check_out_date = data.get('check_out_date')
    exclude_booking_id = data.get('exclude_booking_id')
    current_room_id = data.get('current_room_id')
    room_type = data.get('room_type')

    if not all([check_in_date, check_out_date]):
        return jsonify({'error': 'Check-in and check-out dates are required', 'code': 'MISSING_DATA'}), 400

    try:
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        if check_in < date.today():
            return jsonify({'error': 'Check-in date must be today or in the future', 'code': 'INVALID_CHECK_IN'}), 400
        if check_out <= check_in:
            return jsonify({'error': 'Check-out date must be after check-in date', 'code': 'INVALID_CHECK_OUT'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)', 'code': 'INVALID_DATE_FORMAT'}), 400

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with db.session.begin_nested():
                overlapping_bookings = Booking.query.filter(
                    Booking.check_in_date <= check_out,
                    Booking.check_out_date >= check_in,
                    Booking.status.in_(['booked', 'checked-in'])
                )
                if exclude_booking_id:
                    overlapping_bookings = overlapping_bookings.filter(Booking.id != exclude_booking_id)
                overlapping_room_ids = [booking.room_id for booking in
                                        overlapping_bookings.with_entities(Booking.room_id).distinct().all()]
                logger.debug(f"Overlapping room IDs: {overlapping_room_ids}")

                query = Room.query.filter(
                    ~Room.id.in_(overlapping_room_ids),
                    Room.status == 'available'
                )
                if room_type:
                    query = query.filter(Room.room_type == room_type)
                available_rooms = query.all()

                room_list = [{
                    'id': room.id,
                    'room_number': room.room_number,
                    'room_type': room.room_type,
                    'price': room.price,
                    'status': room.status,
                    'is_current': room.id == current_room_id
                } for room in available_rooms]

                if current_room_id and not any(room['id'] == current_room_id for room in room_list):
                    current_room = Room.query.get(current_room_id)
                    if current_room and current_room.id not in overlapping_room_ids and current_room.room_type == room_type:
                        room_list.insert(0, {
                            'id': current_room.id,
                            'room_number': current_room.room_number,
                            'room_type': current_room.room_type,
                            'price': current_room.price,
                            'status': current_room.status,
                            'is_current': True
                        })
                        logger.debug(f"Added current room {current_room.room_number} to available rooms")

            db.session.commit()
            logger.debug(f"Available rooms: {[room['room_number'] for room in room_list]}")
            return jsonify({
                'rooms': room_list,
                'check_in': check_in.strftime('%d %B %Y'),
                'check_out': check_out.strftime('%d %B %Y'),
                'code': 'SUCCESS'
            }), 200
        except OperationalError as e:
            db.session.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying attempt {attempt + 1}/{max_retries}")
                time.sleep(0.1 * (2 ** attempt))
                continue
            logger.error(f"OperationalError in available_rooms: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error in available_rooms: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500
        finally:
            db.session.remove()

@manage_booking_bp.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    data = request.get_json()
    logger.debug(f"cancel_booking received data: {data}")
    email = data.get('email')
    booking_reference = data.get('booking_reference')

    if not all([email, booking_reference]):
        return jsonify({'error': 'Email and booking reference are required', 'code': 'MISSING_DATA'}), 400

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with db.session.begin_nested():
                booking = Booking.query.filter_by(booking_reference=booking_reference).first()
                if not booking:
                    return jsonify({'error': 'Booking not found', 'code': 'BOOKING_NOT_FOUND'}), 404

                guest = Guest.query.get(booking.guest_id)
                if not guest or guest.email.lower() != email.lower():
                    return jsonify({'error': 'No guest found with that email', 'code': 'GUEST_NOT_FOUND'}), 401

                if booking.status in ['checked-in', 'checked-out', 'cancelled']:
                    return jsonify({'error': 'Cannot cancel a checked-in, checked-out, or already cancelled booking',
                                    'code': 'INVALID_MODIFICATION'}), 400

                booking.status = 'cancelled'
                update_room_status(booking.room_id)
            db.session.commit()
            logger.debug(f"Cancelled booking: {booking_reference}")
            return jsonify({
                'message': 'Booking cancelled successfully',
                'booking_reference': booking_reference,
                'booking': {'id': booking.id, 'status': booking.status},
                'code': 'SUCCESS'
            }), 200
        except OperationalError as e:
            db.session.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying attempt {attempt + 1}/{max_retries}")
                time.sleep(0.1 * (2 ** attempt))
                continue
            logger.error(f"OperationalError in cancel_booking: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error in cancel_booking: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500
        finally:
            db.session.remove()

@manage_booking_bp.route('/modify_booking/<string:booking_reference>', methods=['POST'])
def modify_booking(booking_reference):
    data = request.get_json()
    logger.debug(f"modify_booking received data for booking_reference {booking_reference}: {data}")
    email = data.get('email')
    room_id = data.get('room_id')
    check_in_date = data.get('check_in_date')
    check_out_date = data.get('check_out_date')
    request_id = data.get('request_id')

    if not all([email, request_id]) or not any([room_id, check_in_date, check_out_date]):
        return jsonify(
            {'error': 'Email, request_id, and at least one of room_id, check_in_date, or check_out_date required',
             'code': 'MISSING_DATA'}), 400

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with db.session.begin_nested():
                booking = Booking.query.filter_by(booking_reference=booking_reference).first()
                if not booking:
                    return jsonify({'error': 'Booking not found', 'code': 'BOOKING_NOT_FOUND'}), 404

                guest = Guest.query.get(booking.guest_id)
                if not guest or guest.email.lower() != email.lower():
                    return jsonify({'error': 'No guest found with that email', 'code': 'GUEST_NOT_FOUND'}), 401

                if booking.status in ['checked-in', 'checked-out', 'cancelled']:
                    return jsonify({'error': 'Cannot modify a checked-in, checked-out, or cancelled booking',
                                    'code': 'INVALID_MODIFICATION'}), 400

                if booking.payment_status != 'paid':
                    return jsonify({'error': 'Payment must be completed before modification',
                                    'code': 'PAYMENT_REQUIRED'}), 400

                if room_id:
                    room = db.session.get(Room, room_id)
                    if not room:
                        return jsonify({'error': 'Room not found', 'code': 'ROOM_NOT_FOUND'}), 404
                    if has_overlapping_booking(room_id, check_in_date or booking.check_in_date,
                                               check_out_date or booking.check_out_date, booking.id):
                        return jsonify({'error': 'Room is booked for the selected dates', 'code': 'ROOM_BOOKED'}), 400

                old_room_id = booking.room_id
                if room_id:
                    booking.room_id = room_id
                if check_in_date:
                    try:
                        booking.check_in_date = datetime.strptime(check_in_date, '%Y-%m-%d').date()
                    except ValueError:
                        return jsonify(
                            {'error': 'Invalid date format (use YYYY-MM-DD)', 'code': 'INVALID_DATE_FORMAT'}), 400
                if check_out_date:
                    try:
                        booking.check_out_date = datetime.strptime(check_out_date, '%Y-%m-%d').date()
                    except ValueError:
                        return jsonify(
                            {'error': 'Invalid date format (use YYYY-MM-DD)', 'code': 'INVALID_DATE_FORMAT'}), 400

                if check_in_date or check_out_date:
                    if booking.check_in_date < date.today():
                        return jsonify(
                            {'error': 'Check-in date must be today or in the future', 'code': 'INVALID_CHECK_IN'}), 400
                    if booking.check_out_date <= booking.check_in_date:
                        return jsonify(
                            {'error': 'Check-out date must be after check-in date', 'code': 'INVALID_CHECK_OUT'}), 400
                    if has_overlapping_booking(booking.room_id, booking.check_in_date, booking.check_out_date,
                                               booking.id):
                        return jsonify({'error': 'Room is booked for the selected dates', 'code': 'ROOM_BOOKED'}), 400

                update_room_status(booking.room_id)
                if room_id and old_room_id != booking.room_id:
                    update_room_status(old_room_id)
            db.session.commit()
            logger.debug(f"Modified booking: {booking_reference}")
            return jsonify({
                'message': 'Booking modified successfully',
                'booking_reference': booking_reference,
                'booking': {
                    'id': booking.id,
                    'room_id': booking.room_id,
                    'check_in_date': booking.check_in_date.isoformat(),
                    'check_out_date': booking.check_out_date.isoformat()
                },
                'code': 'SUCCESS'
            }), 200
        except OperationalError as e:
            db.session.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying attempt {attempt + 1}/{max_retries}")
                time.sleep(0.1 * (2 ** attempt))
                continue
            logger.error(f"OperationalError in modify_booking: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'Database connection issue', 'code': 'DB_CONNECTION'}), 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error in modify_booking: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': f'Server error: {str(e)}', 'code': 'SERVER_ERROR'}), 500
        finally:
            db.session.remove()