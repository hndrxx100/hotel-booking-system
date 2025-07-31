from datetime import datetime, timedelta
from app import app, db
from models import Booking
import logging

def cancel_unpaid_bookings():
    """Cancel bookings that are unpaid for more than 1 hour"""
    with app.app_context():
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        unpaid_bookings = Booking.query.filter(
            Booking.payment_status == 'unpaid',
            Booking.created_at <= cutoff_time,
            Booking.status != 'cancelled'
        ).all()
        
        for booking in unpaid_bookings:
            booking.status = 'cancelled'
            booking.payment_status = 'cancelled'
            booking.cancelled_at = datetime.utcnow()
            logging.info(f"Auto-cancelled booking {booking.reference}")
        
        if unpaid_bookings:
            db.session.commit()
            logging.info(f"Auto-cancelled {len(unpaid_bookings)} unpaid bookings")

# Set up APScheduler for periodic tasks
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=cancel_unpaid_bookings,
    trigger="interval",
    minutes=15,  # Check every 15 minutes
    id='cancel_unpaid_bookings'
)

scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
