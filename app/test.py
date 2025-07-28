from app import create_app
from app.extensions import db
from app.models import Booking, Room, Receptionist, Guest

app = create_app()


def create_receptionist_account():
    """Create a receptionist account with admin@pelican.com and Admin123!"""
    print("\n=== Creating Receptionist Account ===")
    existing_receptionist = Receptionist.query.filter_by(email='admin@pelican.com').first()
    if existing_receptionist:
        print("Receptionist with email 'admin@pelican.com' already exists!")
        print(f"Name: {existing_receptionist.name}")
        print(f"Email: {existing_receptionist.email}")
        print(f"Created: {existing_receptionist.created_at}")
        return existing_receptionist
    try:
        receptionist = Receptionist(name='Admin User', email='admin@pelican.com')
        receptionist.set_password('Admin123!')
        db.session.add(receptionist)
        db.session.commit()
        print("✅ Receptionist account created successfully!")
        print(f"Name: {receptionist.name}")
        print(f"Email: {receptionist.email}")
        print(f"Password: Admin123!")
        print(f"Created: {receptionist.created_at}")
        return receptionist
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating receptionist: {str(e)}")
        return None


def print_receptionist_data():
    print("\n=== Receptionist Data ===")
    receptionists = Receptionist.query.all()
    if not receptionists:
        print("No receptionists found.")
    else:
        for receptionist in receptionists:
            print(f"Receptionist ID: {receptionist.id}")
            print(f"  Name: {receptionist.name}")
            print(f"  Email: {receptionist.email}")
            print(f"  Created: {receptionist.created_at}")
            print("-" * 50)


def print_guest_data():
    print("\n=== Guest Data ===")
    guests = Guest.query.all()
    if not guests:
        print("No guests found.")
    else:
        for guest in guests:
            print(f"Guest ID: {guest.id}")
            print(f"  Full Name: {guest.full_name}")
            print(f"  Email: {guest.email}")
            print(f"  Phone: {guest.phone}")
            print(f"  Created: {guest.created_at}")
            print("-" * 50)


def print_booking_data():
    print("\n=== Booking Data ===")
    bookings = Booking.query.all()
    if not bookings:
        print("No bookings found.")
    else:
        for booking in bookings:
            print(f"Booking ID: {booking.id}")
            print(f"  Booking Reference: {booking.booking_reference}")
            print(f"  Guest ID: {booking.guest_id}")
            print(f"  Room ID: {booking.room_id}")
            print(f"  Check-In Date: {booking.check_in_date}")
            print(f"  Check-Out Date: {booking.check_out_date}")
            print(f"  Status: {booking.status}")
            print(f"  Payment Status: {booking.payment_status}")
            print(
                f"  Guest: {booking.guest.full_name if booking.guest else 'N/A'} ({booking.guest.email if booking.guest else 'N/A'})")
            print(
                f"  Room: {booking.room.room_number if booking.room else 'N/A'} ({booking.room.room_type if booking.room else 'N/A'})")
            print("-" * 50)


def print_room_data():
    print("\n=== Room Data ===")
    rooms = Room.query.all()
    if not rooms:
        print("No rooms found.")
    else:
        for room in rooms:
            print(f"Room ID: {room.id}")
            print(f"  Room Number: {room.room_number}")
            print(f"  Room Type: {room.room_type}")
            print(f"  Price: GHS {room.price:.2f}")
            print(f"  Status: {room.status}")
            print("-" * 50)


with app.app_context():
    try:
        create_receptionist_account()
        print_receptionist_data()
        print_guest_data()
        print_booking_data()
        print_room_data()
    except Exception as e:
        print(f"Error accessing database: {str(e)}")
