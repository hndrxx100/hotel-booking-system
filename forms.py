from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, FloatField, IntegerField, PasswordField, \
    BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length, ValidationError
from datetime import datetime, date
from models import Room, RoomCategory, Staff


class RoomSearchForm(FlaskForm):
    check_in = DateField('Check-in Date', validators=[DataRequired()])
    check_out = DateField('Check-out Date', validators=[DataRequired()])

    def validate_check_in(self, field):
        if field.data < date.today():
            raise ValidationError('Check-in date cannot be in the past.')

    def validate_check_out(self, field):
        if field.data <= self.check_in.data:
            raise ValidationError('Check-out date must be after check-in date.')


class BookingForm(FlaskForm):
    guest_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    guest_email = StringField('Email', validators=[Optional(), Email()])
    guest_phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    payment_method = SelectField('Payment Method', choices=[
        ('in_person', 'Pay in Person'),
        ('momo', 'MoMo Payment')
    ], validators=[DataRequired()])
    room_id = HiddenField(validators=[DataRequired()])
    check_in = HiddenField(validators=[DataRequired()])
    check_out = HiddenField(validators=[DataRequired()])


class BookingLookupForm(FlaskForm):
    search_type = SelectField('Search By', choices=[
        ('email', 'Email'),
        ('phone', 'Phone Number')
    ], validators=[DataRequired()])
    search_value = StringField('Email or Phone', validators=[DataRequired()])
    booking_reference = StringField('Booking Reference', validators=[DataRequired(), Length(min=10, max=10)])


class ModifyBookingForm(FlaskForm):
    check_in = DateField('New Check-in Date', validators=[DataRequired()])
    check_out = DateField('New Check-out Date', validators=[DataRequired()])
    room_category = SelectField('Room Category', coerce=int, validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_category.choices = [(0, 'Keep Current Room')] + [
            (cat.id, f"{cat.name} - GH₵ {cat.base_price}/night")
            for cat in RoomCategory.query.all()
        ]


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')


class StaffForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    role = SelectField('Role', choices=[
        ('receptionist', 'Receptionist'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    is_active = BooleanField('Active')

    def __init__(self, staff=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.staff = staff

    def validate_username(self, field):
        if self.staff and self.staff.username == field.data:
            return
        if Staff.query.filter_by(username=field.data).first():
            raise ValidationError('Username already exists.')

    def validate_email(self, field):
        if self.staff and self.staff.email == field.data:
            return
        if Staff.query.filter_by(email=field.data).first():
            raise ValidationError('Email already exists.')


class RoomCategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(min=2, max=50)])
    base_price = FloatField('Base Price per Night', validators=[DataRequired(), NumberRange(min=0)])
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1, max=10)])
    description = TextAreaField('Description')
    amenities = TextAreaField('Amenities (one per line)')


class RoomForm(FlaskForm):
    room_number = StringField('Room Number', validators=[DataRequired(), Length(min=1, max=10)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[('available', 'Available'), ('maintenance', 'Maintenance')],
                         validators=[DataRequired()])
    maintenance_notes = TextAreaField('Maintenance Notes')

    def __init__(self, room=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room = room
        self.category_id.choices = [
            (cat.id, cat.name) for cat in RoomCategory.query.all()
        ]

    def validate_room_number(self, field):
        if self.room and self.room.room_number == field.data:
            return
        if Room.query.filter_by(room_number=field.data).first():
            raise ValidationError('Room number already exists.')