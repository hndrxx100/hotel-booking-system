from flask import Blueprint, render_template
from datetime import datetime

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
