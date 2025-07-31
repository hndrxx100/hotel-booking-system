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
    name = db.Column(db.String(50), nullable=False)  # Single, Double, Suite
    base_price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    amenities = db.Column(db.Text)  # JSON string of amenities
    
    rooms = db.relationship('Room', backref='category', lazy=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('room_category.id'), nullable=False)
    floor = db.Column(db.Integer)
    is_available = db.Column(db.Boolean, default=True)
    maintenance_notes = db.Column(db.Text)
    
    bookings = db.relationship('Booking', backref='room', lazy=True)

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='guest', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(20), unique=True, nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # 'in_person' or 'momo'
    payment_status = db.Column(db.String(20), default='unpaid')  # 'unpaid', 'paid', 'cancelled'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    @staticmethod
    def generate_reference():
        """Generate a unique booking reference with PL prefix"""
        while True:
            ref = 'PL' + ''.join(random.choices(string.digits, k=8))
            if not Booking.query.filter_by(reference=ref).first():
                return ref
    
    @property
    def nights(self):
        return (self.check_out - self.check_in).days
    
    @property
    def is_cancellable(self):
        """Check if booking can be cancelled (only paid bookings)"""
        return self.payment_status == 'paid' and self.status != 'cancelled'
    
    @property
    def auto_cancel_time(self):
        """Get the time when unpaid booking will be auto-cancelled"""
        if self.payment_status == 'unpaid':
            return self.created_at + timedelta(hours=1)
        return None

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(20), nullable=False)
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    booking = db.relationship('Booking', backref='payments')
