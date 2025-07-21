from flask import Blueprint, render_template, request, jsonify, redirect
from datetime import datetime
from app import db
from app.models import Room, Guest, Booking, User
from werkzeug.security import generate_password_hash
from flask import session, flash, redirect, url_for
from werkzeug.security import check_password_hash

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html', now=datetime.now())


@main.route('/rooms')
def rooms():
    return render_template('rooms.html')


@main.route('/booking')
def booking():
    return render_template('booking.html')


# ✅ GET available rooms
@main.route('/get_available_rooms')
def get_available_rooms():
    checkin = request.args.get('checkin')
    checkout = request.args.get('checkout')

    try:
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d').date()
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'error': 'Invalid date format'}), 400

    booked_rooms = db.session.query(Booking.room_id).filter(
        Booking.check_in_date < checkout_date,
        Booking.check_out_date > checkin_date
    ).subquery()

    available_rooms = Room.query.filter(~Room.id.in_(booked_rooms)).all()

    rooms_data = [
        {
            'id': room.id,
            'name': f'{room.room_type} Room {room.room_number}',
            'category': room.room_type,
            'price_per_night': room.price,
            'description': room.description,
            'image_url': f"/static/images/rooms/{room.room_type.lower()}.jpg"
        }
        for room in available_rooms
    ]

    return jsonify({'rooms': rooms_data})


# ✅ Handle booking submission
@main.route('/submit_booking', methods=['POST'])
def submit_booking():
    data = request.form

    guest = Guest.query.filter_by(email=data.get('guest_email')).first()
    if not guest:
        guest = Guest(
            full_name=data.get('guest_name'),
            email=data.get('guest_email'),
            phone=data.get('guest_phone')
        )
        db.session.add(guest)
        db.session.commit()

    booking = Booking(
        guest_id=guest.id,
        room_id=data.get('room_id'),
        check_in_date=datetime.strptime(data.get('check_in'), '%Y-%m-%d').date(),
        check_out_date=datetime.strptime(data.get('check_out'), '%Y-%m-%d').date(),
        status='Pending'
    )

    db.session.add(booking)
    db.session.commit()

    return jsonify({'success': True})


# ✅ Handle account creation
@main.route('/create_account', methods=['POST'])
def create_account():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Missing credentials'})

    username = email.split('@')[0]
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Account already exists'})

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role='Guest'
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({'success': True})


# ✅ Create a new room
@main.route('/add_room', methods=['POST'])
def add_room():
    room_number = request.form.get('room_number')
    room_type = request.form.get('room_type')
    price = request.form.get('price')
    description = request.form.get('description')
    print("🔧 Room data received:", room_number, room_type, price)

    if not all([room_number, room_type, price]):
        return jsonify({'success': False, 'message': 'Missing fields'}), 400

    if Room.query.filter_by(room_number=room_number).first():
        return jsonify({'success': False, 'message': 'Room number already exists'}), 409

    new_room = Room(
        room_number=room_number,
        room_type=room_type,
        price=float(price),
        description=description
    )

    db.session.add(new_room)
    db.session.commit()
    print("✅ Room saved to database.")

    return jsonify({'success': True})


# ✅ Get all rooms
@main.route('/get_all_rooms')
def get_all_rooms():
    rooms = Room.query.all()

    data = [
        {
            'id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'price': room.price,
            'description': room.description
        }
        for room in rooms
    ]

    return jsonify({'rooms': data})


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_role'] = user.role
            flash('Login successful!', 'info')
            return redirect(url_for('main.manage_rooms'))
        else:
            flash('Invalid credentials. Try again.', 'error')

    return render_template('staff_login.html')


@main.route('/manage_rooms')
def manage_rooms():
    if 'user_id' not in session or session.get('user_role') not in ['Admin', 'Receptionist']:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.login'))  # ✅ corrected here as well

    return render_template('manage_rooms.html')

