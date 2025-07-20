from dotenv import load_dotenv

load_dotenv()
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from config import Config
import stripe

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
stripe.api_key = app.config['STRIPE_SECRET_KEY']

from app.routes import auth, booking, admin
app.register_blueprint(auth.bp)
app.register_blueprint(booking.bp)
app.register_blueprint(admin.bp, url_prefix="/admin")




