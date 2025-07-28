from flask import Blueprint, render_template
from datetime import datetime

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html', now=datetime.now())


@main.route('/manage_booking')
def manage_booking():
    return render_template('guest/manage_booking.html')


@main.route('/booking')
def booking():
    return render_template('guest/booking.html')

