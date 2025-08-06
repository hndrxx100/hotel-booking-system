from datetime import datetime, timedelta
from app import app, db
from models import Booking, Room
from sqlalchemy import or_  # Add this import
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Duration for how long a room remains dirty (in hours)
CLEANING_DURATION_HOURS = 0.033  # Change this for testing (e.g., set to 0.033 for 2 minutes)


def cancel_unpaid_bookings():
    """Cancel bookings that are unpaid for more than 1 hour"""
    with app.app_context():
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        unpaid_bookings = Booking.query.filter(
            Booking.payment_status == 'unpaid',
            Booking.created_at <= cutoff_time,
            Booking.status != 'cancelled'
        ).all()
        logging.info(f"Found {len(unpaid_bookings)} unpaid bookings to cancel")
        for booking in unpaid_bookings:
            booking.status = 'cancelled'
            booking.payment_status = 'cancelled'
            booking.cancelled_at = datetime.utcnow()
            logging.info(f"Auto-cancelled booking {booking.reference}")
        if unpaid_bookings:
            db.session.commit()
            logging.info(f"Auto-cancelled {len(unpaid_bookings)} unpaid bookings")


def clean_rooms():
    """Mark dirty rooms as available after dirty_until time expires"""
    with app.app_context():
        now = datetime.utcnow()
        logging.info(f"Running clean_rooms at {now}")
        expired_dirty_rooms = Room.query.filter(
            Room.status == 'dirty',
            or_(
                Room.dirty_until <= now,
                Room.dirty_until.is_(None)  # Handle NULL dirty_until
            )
        ).all()
        logging.info(f"Found {len(expired_dirty_rooms)} dirty rooms to clean")
        for room in expired_dirty_rooms:
            logging.info(f"Processing room {room.room_number}, dirty_until: {room.dirty_until}")
            room.status = 'available'
            room.dirty_until = None
            logging.info(f"Auto-cleaned room {room.room_number}")
        if expired_dirty_rooms:
            db.session.commit()
            logging.info(f"Auto-cleaned {len(expired_dirty_rooms)} rooms")
        else:
            logging.info("No rooms to clean")


# Set up APScheduler for periodic tasks
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=cancel_unpaid_bookings,
    trigger="interval",
    minutes=15,  # Runs every 1 minute as per your change
    id='cancel_unpaid_bookings'
)
scheduler.add_job(
    func=clean_rooms,
    trigger="interval",
    minutes=15,  # Runs every 1 minute
    id='clean_rooms'
)

scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
