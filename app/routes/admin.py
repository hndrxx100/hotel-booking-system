import os
from werkzeug.utils import secure_filename
from flask import current_app, Response
import csv

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Room, User, Booking

bp = Blueprint('admin', __name__, url_prefix='/admin')


# Decorator to restrict access to admins only
def admin_required(view_func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Admin access required.", "danger")
            return redirect(url_for('auth.login'))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)
