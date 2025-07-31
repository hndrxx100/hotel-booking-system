from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func, extract
from app import app, db
from models import Staff, Guest, Booking, Room, RoomCategory, Payment
from forms import (RoomSearchForm, BookingForm, BookingLookupForm, ModifyBookingForm,
                  LoginForm, StaffForm, RoomCategoryForm, RoomForm)
import json

def admin_required(f):
    """Decorator to require admin role"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_available_rooms(check_in, check_out, exclude_booking_id=None):
    """Get available rooms for given date range"""
    query = db.session.query(Room).join(RoomCategory).filter(Room.is_available == True)
    
    # Exclude rooms with overlapping bookings
    overlapping_bookings = db.session.query(Booking.room_id).filter(
        and_(
            Booking.status.in_(['pending', 'confirmed', 'checked_in']),
            Booking.payment_status != 'cancelled',
            or_(
                and_(Booking.check_in <= check_in, Booking.check_out > check_in),
                and_(Booking.check_in < check_out, Booking.check_out >= check_out),
                and_(Booking.check_in >= check_in, Booking.check_out <= check_out)
            )
        )
    )
    
    if exclude_booking_id:
        overlapping_bookings = overlapping_bookings.filter(Booking.id != exclude_booking_id)
    
    query = query.filter(~Room.id.in_(overlapping_bookings))
    return query.all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search_rooms', methods=['GET', 'POST'])
def search_rooms():
    form = RoomSearchForm()
    available_rooms = []
    
    if form.validate_on_submit():
        check_in = form.check_in.data
        check_out = form.check_out.data
        
        available_rooms = get_available_rooms(check_in, check_out)
        
        # Group rooms by category
        rooms_by_category = {}
        for room in available_rooms:
            category = room.category.name
            if category not in rooms_by_category:
                rooms_by_category[category] = {
                    'category': room.category,
                    'rooms': [],
                    'nights': (check_out - check_in).days
                }
            rooms_by_category[category]['rooms'].append(room)
        
        return render_template('search_rooms.html', form=form, 
                             rooms_by_category=rooms_by_category,
                             check_in=check_in, check_out=check_out)
    
    return render_template('search_rooms.html', form=form)

@app.route('/book_room', methods=['POST'])
def book_room():
    form = BookingForm()
    
    if form.validate_on_submit():
        # Get or create guest
        guest = Guest.query.filter(
            or_(Guest.email == form.guest_email.data, Guest.phone == form.guest_phone.data)
        ).first()
        
        if not guest:
            guest = Guest(
                name=form.guest_name.data,
                email=form.guest_email.data,
                phone=form.guest_phone.data
            )
            db.session.add(guest)
            db.session.flush()
        
        # Create booking
        room = Room.query.get(form.room_id.data)
        check_in = datetime.strptime(form.check_in.data, '%Y-%m-%d').date()
        check_out = datetime.strptime(form.check_out.data, '%Y-%m-%d').date()
        nights = (check_out - check_in).days
        
        booking = Booking(
            reference=Booking.generate_reference(),
            guest_id=guest.id,
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            total_price=room.category.base_price * nights,
            payment_method=form.payment_method.data
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash(f'Booking created successfully! Reference: {booking.reference}', 'success')
        return jsonify({
            'success': True,
            'booking_reference': booking.reference,
            'total_price': booking.total_price,
            'payment_method': booking.payment_method,
            'auto_cancel_time': booking.auto_cancel_time.strftime('%Y-%m-%d %H:%M:%S') if booking.auto_cancel_time else None
        })
    
    return jsonify({'success': False, 'errors': form.errors})

@app.route('/booking_lookup', methods=['GET', 'POST'])
def booking_lookup():
    form = BookingLookupForm()
    booking = None
    
    if form.validate_on_submit():
        guest_query = Guest.query
        if form.search_type.data == 'email':
            guest_query = guest_query.filter_by(email=form.search_value.data)
        else:
            guest_query = guest_query.filter_by(phone=form.search_value.data)
        
        guest = guest_query.first()
        if guest:
            booking = Booking.query.filter_by(
                reference=form.booking_reference.data,
                guest_id=guest.id
            ).first()
            
            if not booking:
                flash('Booking not found with the provided details.', 'error')
        else:
            flash('No guest found with the provided contact information.', 'error')
    
    return render_template('booking_lookup.html', form=form, booking=booking)

@app.route('/modify_booking/<booking_reference>', methods=['GET', 'POST'])
def modify_booking(booking_reference):
    booking = Booking.query.filter_by(reference=booking_reference).first_or_404()
    
    if booking.payment_status != 'paid':
        flash('Only paid bookings can be modified.', 'error')
        return redirect(url_for('booking_lookup'))
    
    form = ModifyBookingForm()
    
    if form.validate_on_submit():
        new_check_in = form.check_in.data
        new_check_out = form.check_out.data
        
        # Check room availability for new dates
        available_rooms = get_available_rooms(new_check_in, new_check_out, booking.id)
        
        new_room = booking.room
        if form.room_category.data and form.room_category.data != 0:
            # Find available room in new category
            category_rooms = [r for r in available_rooms if r.category_id == form.room_category.data]
            if category_rooms:
                new_room = category_rooms[0]
            else:
                flash('No rooms available in selected category for the new dates.', 'error')
                return render_template('modify_booking.html', form=form, booking=booking)
        else:
            # Check if current room is available
            if booking.room not in available_rooms:
                flash('Current room is not available for the new dates.', 'error')
                return render_template('modify_booking.html', form=form, booking=booking)
        
        # Update booking
        nights = (new_check_out - new_check_in).days
        booking.check_in = new_check_in
        booking.check_out = new_check_out
        booking.room_id = new_room.id
        booking.total_price = new_room.category.base_price * nights
        
        db.session.commit()
        flash('Booking modified successfully!', 'success')
        return redirect(url_for('booking_lookup'))
    
    return render_template('modify_booking.html', form=form, booking=booking)

@app.route('/cancel_booking/<booking_reference>')
def cancel_booking(booking_reference):
    booking = Booking.query.filter_by(reference=booking_reference).first_or_404()
    
    if not booking.is_cancellable:
        flash('This booking cannot be cancelled.', 'error')
    else:
        booking.status = 'cancelled'
        booking.payment_status = 'cancelled'
        booking.cancelled_at = datetime.utcnow()
        db.session.commit()
        flash('Booking cancelled successfully.', 'success')
    
    return redirect(url_for('booking_lookup'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('receptionist_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        staff = Staff.query.filter_by(username=form.username.data).first()
        
        if staff and staff.is_active and check_password_hash(staff.password_hash, form.password.data):
            login_user(staff, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page:
                if staff.role == 'admin':
                    next_page = url_for('admin_dashboard')
                else:
                    next_page = url_for('receptionist_dashboard')
            return redirect(next_page)
        
        flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Admin Routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Get dashboard statistics
    total_bookings = Booking.query.count()
    active_bookings = Booking.query.filter_by(status='confirmed').count()
    total_revenue = db.session.query(func.sum(Booking.total_price)).filter_by(payment_status='paid').scalar() or 0
    occupancy_rate = (active_bookings / Room.query.count() * 100) if Room.query.count() > 0 else 0
    
    # Recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_bookings=total_bookings,
                         active_bookings=active_bookings,
                         total_revenue=total_revenue,
                         occupancy_rate=occupancy_rate,
                         recent_bookings=recent_bookings)

@app.route('/admin/staff', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_staff():
    form = StaffForm()
    staff_members = Staff.query.all()
    
    if form.validate_on_submit():
        staff = Staff(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
            password_hash=generate_password_hash(form.password.data),
            is_active=form.is_active.data
        )
        db.session.add(staff)
        db.session.commit()
        flash('Staff member created successfully!', 'success')
        return redirect(url_for('manage_staff'))
    
    return render_template('admin/manage_staff.html', form=form, staff_members=staff_members)

@app.route('/admin/staff/edit/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def edit_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    form = StaffForm(staff=staff)
    
    if form.validate_on_submit():
        staff.username = form.username.data
        staff.email = form.email.data
        staff.full_name = form.full_name.data
        staff.role = form.role.data
        staff.is_active = form.is_active.data
        
        if form.password.data:
            staff.password_hash = generate_password_hash(form.password.data)
        
        db.session.commit()
        flash('Staff member updated successfully!', 'success')
    
    return redirect(url_for('manage_staff'))

@app.route('/admin/staff/delete/<int:staff_id>')
@login_required
@admin_required
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    if staff.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
    else:
        db.session.delete(staff)
        db.session.commit()
        flash('Staff member deleted successfully!', 'success')
    
    return redirect(url_for('manage_staff'))

@app.route('/admin/bookings')
@login_required
@admin_required
def manage_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/manage_bookings.html', bookings=bookings)

@app.route('/admin/rooms', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_rooms():
    category_form = RoomCategoryForm()
    room_form = RoomForm()
    
    categories = RoomCategory.query.all()
    rooms = Room.query.join(RoomCategory).all()
    
    if request.form.get('form_type') == 'category' and category_form.validate_on_submit():
        category = RoomCategory(
            name=category_form.name.data,
            base_price=category_form.base_price.data,
            capacity=category_form.capacity.data,
            description=category_form.description.data,
            amenities=category_form.amenities.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Room category created successfully!', 'success')
        return redirect(url_for('manage_rooms'))
    
    if request.form.get('form_type') == 'room' and room_form.validate_on_submit():
        room = Room(
            room_number=room_form.room_number.data,
            category_id=room_form.category_id.data,
            floor=room_form.floor.data,
            is_available=room_form.is_available.data,
            maintenance_notes=room_form.maintenance_notes.data
        )
        db.session.add(room)
        db.session.commit()
        flash('Room created successfully!', 'success')
        return redirect(url_for('manage_rooms'))
    
    return render_template('admin/manage_rooms.html',
                         category_form=category_form,
                         room_form=room_form,
                         categories=categories,
                         rooms=rooms)

@app.route('/admin/reports')
@login_required
@admin_required
def reports():
    # Revenue by month (last 12 months)
    monthly_revenue = db.session.query(
        extract('year', Booking.created_at).label('year'),
        extract('month', Booking.created_at).label('month'),
        func.sum(Booking.total_price).label('revenue')
    ).filter_by(payment_status='paid').group_by('year', 'month').all()
    
    # Bookings by status
    booking_status = db.session.query(
        Booking.status,
        func.count(Booking.id).label('count')
    ).group_by(Booking.status).all()
    
    # Occupancy by room category
    category_bookings = db.session.query(
        RoomCategory.name,
        func.count(Booking.id).label('bookings')
    ).join(Room).join(Booking).filter_by(payment_status='paid').group_by(RoomCategory.name).all()
    
    return render_template('admin/reports.html',
                         monthly_revenue=monthly_revenue,
                         booking_status=booking_status,
                         category_bookings=category_bookings)

# Receptionist Routes
@app.route('/receptionist/dashboard')
@login_required
def receptionist_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    # Today's statistics
    today = date.today()
    checkins_today = Booking.query.filter_by(check_in=today, status='confirmed').count()
    checkouts_today = Booking.query.filter_by(check_out=today, status='checked_in').count()
    pending_payments = Booking.query.filter_by(payment_status='unpaid').count()
    
    # Recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    
    return render_template('receptionist/dashboard.html',
                         checkins_today=checkins_today,
                         checkouts_today=checkouts_today,
                         pending_payments=pending_payments,
                         recent_bookings=recent_bookings)

@app.route('/receptionist/bookings')
@login_required
def receptionist_manage_bookings():
    if current_user.role == 'admin':
        return redirect(url_for('manage_bookings'))
    
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('receptionist/manage_bookings.html', bookings=bookings)

@app.route('/mark_paid/<int:booking_id>')
@login_required
def mark_paid(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.payment_status = 'paid'
    booking.status = 'confirmed'
    
    # Create payment record
    payment = Payment(
        booking_id=booking.id,
        amount=booking.total_price,
        method=booking.payment_method,
        status='completed',
        processed_at=datetime.utcnow()
    )
    db.session.add(payment)
    db.session.commit()
    
    flash('Booking marked as paid successfully!', 'success')
    return redirect(request.referrer or url_for('receptionist_dashboard'))

@app.route('/check_in/<int:booking_id>')
@login_required
def check_in(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.payment_status == 'paid' and booking.status == 'confirmed':
        booking.status = 'checked_in'
        db.session.commit()
        flash('Guest checked in successfully!', 'success')
    else:
        flash('Cannot check in. Booking must be paid and confirmed.', 'error')
    
    return redirect(request.referrer or url_for('receptionist_dashboard'))

@app.route('/check_out/<int:booking_id>')
@login_required
def check_out(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.status == 'checked_in':
        booking.status = 'checked_out'
        db.session.commit()
        flash('Guest checked out successfully!', 'success')
    else:
        flash('Cannot check out. Guest must be checked in first.', 'error')
    
    return redirect(request.referrer or url_for('receptionist_dashboard'))

# API Endpoints for charts
@app.route('/api/revenue_data')
@login_required
@admin_required
def revenue_data():
    monthly_revenue = db.session.query(
        extract('year', Booking.created_at).label('year'),
        extract('month', Booking.created_at).label('month'),
        func.sum(Booking.total_price).label('revenue')
    ).filter_by(payment_status='paid').group_by('year', 'month').order_by('year', 'month').all()
    
    data = {
        'labels': [f"{int(r.year)}-{int(r.month):02d}" for r in monthly_revenue],
        'data': [float(r.revenue) for r in monthly_revenue]
    }
    return jsonify(data)

@app.route('/api/booking_status_data')
@login_required
@admin_required
def booking_status_data():
    booking_status = db.session.query(
        Booking.status,
        func.count(Booking.id).label('count')
    ).group_by(Booking.status).all()
    
    data = {
        'labels': [s.status.title() for s in booking_status],
        'data': [s.count for s in booking_status]
    }
    return jsonify(data)
