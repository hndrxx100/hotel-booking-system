from app import create_app, db
from sqlalchemy import inspect
from app.models import Room

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    if 'room' not in inspector.get_table_names():
        print("❌ Table 'room' does not exist in the database.")
    else:
        rooms = Room.query.all()
        if not rooms:
            print("✅ Table 'room' exists but has no entries.")
        else:
            print("✅ Table 'room' found. Listing entries:\n")
            for room in rooms:
                print(f"ID: {room.id}")
                print(f"Room Number: {room.room_number}")
                print(f"Type: {room.room_type}")
                print(f"Price: GHS {room.price}")
                print(f"Available: {'Yes' if room.is_available else 'No'}")
                print(f"Description: {room.description or 'N/A'}")
                print("-" * 40)
