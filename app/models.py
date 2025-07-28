from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import string
import random


def generate_booking_reference():
    """Generate a unique booking reference like PL00001."""
    prefix = "PL"
    while True:
        number = ''.join(random.choices(string.digits, k=5))
        reference = f"{prefix}{number}"
        if not Booking.query.filter_by(booking_reference=reference).first():
            return reference


class Receptionist(db.Model):
    __tablename__ = 'receptionists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.Date, default=date.today)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Guest(db.Model):
    __tablename__ = 'guests'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Changed to unique
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.Date, default=date.today)

    bookings = db.relationship('Booking', backref='guest', lazy=True)


class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='available', nullable=False)

    bookings = db.relationship('Booking', backref='room', lazy=True)

    __table_args__ = (
        db.CheckConstraint('price > 0', name='check_positive_price'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'room_number': self.room_number,
            'room_type': self.room_type,
            'price': self.price,
            'status': self.status
        }


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(10), unique=True, nullable=False, default=generate_booking_reference)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id', ondelete='SET NULL'))
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='booked', nullable=False)
    payment_status = db.Column(db.String(20), default='pending', nullable=False)
    created_at = db.Column(db.Date, default=date.today)

    __table_args__ = (
        db.CheckConstraint('check_out_date > check_in_date', name='check_date_order'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'booking_reference': self.booking_reference,
            'guest': {
                'full_name': self.guest.full_name if self.guest else 'Unknown',
                'email': self.guest.email if self.guest else ''
            },
            'room': {
                'id': self.room.id if self.room else None,
                'room_number': self.room.room_number if self.room else 'N/A',
                'room_type': self.room.room_type if self.room else 'N/A'  # Added room_type
            },
            'check_in_date': self.check_in_date.isoformat() if self.check_in_date else '',
            'check_out_date': self.check_out_date.isoformat() if self.check_out_date else '',
            'status': self.status,
            'payment_status': self.payment_status
        }
