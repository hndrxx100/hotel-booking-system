# 🏨 Online Hotel Room Booking System

An advanced web application for managing hotel room bookings, built with **Flask**, **MySQL**, and **HTML/CSS/JS**. It supports both **Customer** and **Admin** roles, dynamic search, payments, analytics, and more.

## 🚀 Features

### 👤 Customer Features

- Register/Login
- Browse rooms with filters (AJAX)
- View room details, reviews
- Book with check-in/check-out validation
- Mock payments (card/mobile)
- Download booking receipt (PDF)
- View/cancel bookings
- Leave ratings/reviews
- Save rooms to favorites

### 🔧 Admin Features

- Add/Edit/Delete rooms
- View/Confirm/Cancel bookings
- Promote/Demote users
- View analytics (Chart.js)
- Export bookings to CSV

---

## 🧰 Tech Stack

| Layer      | Technology         |
|------------|--------------------|
| Backend    | Python (Flask)     |
| Database   | MySQL + SQLAlchemy |
| Frontend   | HTML5, TailwindCSS, JS |
| Charts     | Chart.js           |
| Auth       | Flask-Login        |
| Email      | Flask-Mail         |
| PDF        | ReportLab          |
| AJAX       | JavaScript (Fetch) |

## 🗂 Folder Structure

```bash
project/
├── app/
│   ├── **init**.py
│   ├── models.py
│   ├── routes/
│   ├── static/
│   │   └── uploads/
│   ├── templates/
│   │   ├── admin/
│   │   └── ...
├── config.py
├── run.py
|── test.py
└── requirements.txt
```

## ⚙️ Setup Instructions

1. **Clone the repo:**

```bash
git clone https://github.com/yourusername/hotel-booking-system.git
cd hotel-booking-system
```

2. **Create virtual environment:**

```bash
    python -m venv venvvenv
    venv\Scripts\activate  # On Windows
```

3. **Install dependencies:**

```bash
    pip install -r requirements.txt
```

4. **Configure `.env`:**

```ini
    SECRET_KEY=your_secret_key
    DATABASE_URL=mysql+pymysql://username:password@localhost/hotel_db
    MAIL_SERVER=smtp.gmail.com
    MAIL_PORT=587
    MAIL_USE_TLS=true
    MAIL_USERNAME=your_email@gmail.com
    MAIL_PASSWORD=your_email_password
```

5. **Initialize DB:**

```bash
    python test.py
```

6. **Run the app:**

```bash
    python run.py
```

---

## 📦 Deploy

- Compatible with **Render**, **Heroku**, **VPS**, or **CPanel WSGI**.
- Ensure to configure environment variables and database connection in production.

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

## 🙌 Contributors

- [Johnson-Akwaboah](https://github.com/) – Backend Developer
