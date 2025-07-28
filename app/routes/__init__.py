from .main_routes import main
from .dashboard_routes import dashboard_bp
from .receptionist import receptionist_bp
from .booking import booking_bp
from .manage_booking import manage_booking_bp


def register_routes(app):
    app.register_blueprint(main)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(receptionist_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(manage_booking_bp)
