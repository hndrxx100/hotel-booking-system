from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin
from sqlalchemy import func
import random
import string


class Staff(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'receptionist'
    full_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


class RoomCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    amenities = db.Column(db.Text)
    rooms = db.relationship('Room', backref=db.backref('category', lazy='joined'), lazy=True)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('room_category.id'), nullable=False)
    status = db.Column(db.String(20), default='available')
    maintenance_notes = db.Column(db.Text)
    dirty_until = db.Column(db.DateTime, nullable=True)
    bookings = db.relationship('Booking', backref=db.backref('room', lazy='joined'), lazy=True)


class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref=db.backref('guest', lazy='joined'), lazy=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(10), unique=True, nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(20), default='unpaid')
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime)
    auto_cancel_time = db.Column(db.DateTime)

    @staticmethod
    def generate_reference():
        """Generate a unique booking reference with PL prefix"""
        while True:
            ref = 'PL' + ''.join(random.choices(string.digits, k=8))  # 6 digits + PL = 8 chars
            if not Booking.query.filter_by(reference=ref).first():
                return ref

    @property
    def nights(self):
        return (self.check_out - self.check_in).days

    @property
    def is_cancellable(self):
        cancellation_deadline = self.check_in - timedelta(days=2)
        return (self.payment_status == 'paid' and
                self.status != 'cancelled' and
                datetime.utcnow().date() <= cancellation_deadline)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(20), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending')
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    booking = db.relationship('Booking', backref=db.backref('payments', lazy='joined'), lazy=True)
