from app import create_app, db
from sqlalchemy import inspect
from app.models import Guest, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)

    # --- Guest table check & creation ---
    if 'guest' not in inspector.get_table_names():
        print("❌ Table 'guest' does not exist in the database.")
    else:
        guest_email = "guest@example.com"
        existing_guest = Guest.query.filter_by(email=guest_email).first()
        if existing_guest:
            print(f"✅ Guest already exists: {guest_email}")
        else:
            new_guest = Guest(
                full_name="Test Guest",
                email=guest_email
            )
            new_guest.set_password("guestpass123")
            db.session.add(new_guest)
            db.session.commit()
            print(f"✅ Guest account created: {guest_email} / guestpass123")

    # --- User (staff) table check & creation ---
    if 'user' not in inspector.get_table_names():
        print("❌ Table 'user' does not exist in the database.")
    else:
        receptionist_username = "reception1"
        existing_staff = User.query.filter_by(username=receptionist_username).first()
        if existing_staff:
            print(f"✅ Receptionist already exists: {receptionist_username}")
        else:
            new_receptionist = User(
                username=receptionist_username,
                role="Receptionist"
            )
            new_receptionist.set_password("receptionpass123")
            db.session.add(new_receptionist)
            db.session.commit()
            print(f"✅ Receptionist account created: {receptionist_username} / receptionpass123")

    # --- List all users in the User table ---
    print("\n📋 All Users in the 'user' table:")
    users = User.query.all()
    if not users:
        print("No users found.")
    else:
        for user in users:
            print(f"- ID: {user.id}, Username: {user.username}, Role: {user.role}")

    # --- Room table check & dump ---
    if 'room' not in inspector.get_table_names():
        print("❌ Table 'room' does not exist in the database.")
    else:
        print("\n📋 All Rooms in the 'room' table:")
        from app.models import Room

        rooms = Room.query.all()
        if not rooms:
            print("No rooms found.")
        else:
            for r in rooms:
                print(f"- ID: {r.id}, Number: {r.room_number}, Type: {r.room_type}, "
                      f"Price: {r.price}, Available: {r.is_available}, Desc: {r.description or 'N/A'}")

