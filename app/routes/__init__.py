from .main_routes import main
from .booking_routes import booking_bp
from .auth_routes import auth_bp
from .dashboard_routes import dashboard_bp
from .receptionist import receptionist_bp


def register_routes(app):
    app.register_blueprint(main)
    app.register_blueprint(booking_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(receptionist_bp)
