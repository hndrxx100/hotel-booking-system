# # # test_env.py
# # import os
# # from dotenv import load_dotenv

# # load_dotenv()

# print("DATABASE_URL:", os.getenv("DATABASE_URL"))
# init_db.py or test.py

from app import app, db
from app.models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    print("✅ All tables created.")
    

    admin = User(
        username="Admin User",
        email="admin@example.com",
        password_hash=generate_password_hash("admin123"),
        role="admin"
    )

    db.session.add(admin)
    db.session.commit()


