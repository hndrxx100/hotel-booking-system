import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Gmail SMTP configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_EMAIL_APP_PASS = os.getenv("SENDER_EMAIL_APP_PASS")
MOMO_NUMBER = os.getenv("MOMO_NUMBER")
SUPPORT_EMAIL = os.getenv("ADMIN_EMAIL")


def strip_leading_zero(day_str):
    """Remove leading zero from day string (e.g., '05' → '5')."""
    return str(int(day_str))


def format_date(date_str, include_time=False):
    """Convert YYYY-MM-DD or YYYY-MM-DD HH:MM:SS to D MMMM YYYY or D MMMM YYYY, HH:MM."""
    logging.info(f"Formatting date: {date_str}, include_time={include_time}")
    if not date_str:
        logging.warning("Empty date string provided")
        return "N/A"
    try:
        if len(date_str) > 10:
            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            day = strip_leading_zero(dt.strftime('%d'))
            month = dt.strftime('%B')
            year = dt.strftime('%Y')
            if include_time:
                time = dt.strftime('%H:%M')
                formatted = f"{day} {month} {year}, {time}"
            else:
                formatted = f"{day} {month} {year}"
        else:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            day = strip_leading_zero(dt.strftime('%d'))
            month = dt.strftime('%B')
            year = dt.strftime('%Y')
            formatted = f"{day} {month} {year}"
        logging.info(f"Formatted date: {formatted}")
        return formatted
    except ValueError as e:
        logging.error(f"Date format error: {str(e)} for date {date_str}")
        return date_str


def send_booking_confirmation(booking, user_email):
    """Send booking confirmation email with payment instructions."""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = user_email
    msg['Subject'] = f"Booking Confirmation - Ref #{booking['reference']}"

    check_in = format_date(booking['check_in'])
    check_out = format_date(booking['check_out'])
    auto_cancel_time = format_date(booking.get('auto_cancel_time', ''), include_time=True)

    cancellation_note = ""
    if auto_cancel_time != "N/A":
        cancellation_note = f"<p><strong>Important:</strong> Your booking will be automatically cancelled by {auto_cancel_time} if payment is not completed.</p>"
    else:
        cancellation_note = "<p><strong>Important:</strong> Your booking will be automatically cancelled within 1 hour if payment is not completed.</p>"

    if booking["payment_method"] == "momo":
        body = f"""
        <h2>Booking Confirmation</h2>
        <p>Thank you for your booking! Please complete payment within 1 hour to avoid cancellation.</p>
        {cancellation_note}
        <p><strong>Booking Reference:</strong> {booking['reference']}</p>
        <p><strong>Room Type:</strong> {booking['room_type']}</p>
        <p><strong>Check-in:</strong> {check_in}</p>
        <p><strong>Check-out:</strong> {check_out}</p>
        <p><strong>Total Amount:</strong> GHS {booking['total_price']:.2f}</p>
        <p><strong>Payment Instructions:</strong> Send payment of GHS {booking['total_price']:.2f} to Momo number {MOMO_NUMBER} with payment reference as {booking['reference']} within 1 hour.</p>
        <p>Contact {SUPPORT_EMAIL} for assistance.</p>
        """
    else:  # in-person
        body = f"""
        <h2>Booking Confirmation</h2>
        <p>Thank you for your booking! Please pay a 50% deposit within 1 hour to secure your room.</p>
        {cancellation_note}
        <p><strong>Booking Reference:</strong> {booking['reference']}</p>
        <p><strong>Room Type:</strong> {booking['room_type']}</p>
        <p><strong>Check-in:</strong> {check_in}</p>
        <p><strong>Check-out:</strong> {check_out}</p>
        <p><strong>Total Amount:</strong> GHS {booking['total_price']:.2f}</p>
        <p><strong>Deposit Required:</strong> GHS {booking['deposit_amount']:.2f}</p>
        <p><strong>Payment Instructions:</strong> Send deposit of GHS {booking['deposit_amount']:.2f} to Momo number {MOMO_NUMBER} with payment reference as {booking['reference']} within 1 hour. Remaining balance due at check-in.</p>
        <p>Contact {SUPPORT_EMAIL} for assistance.</p>
        """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_EMAIL_APP_PASS)
        server.send_message(msg)
        server.quit()
        logging.info(f"Booking confirmation email sent to {user_email} for booking {booking['reference']}")
        return True
    except Exception as e:
        logging.error(f"Error sending booking confirmation email to {user_email}: {str(e)}")
        return False


def send_payment_confirmation(booking, user_email):
    """Send payment confirmation email."""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = user_email
    msg['Subject'] = f"Payment Confirmation - Ref #{booking['reference']}"

    check_in = format_date(booking['check_in'])
    check_out = format_date(booking['check_out'])
    amount_paid = booking.get('amount_paid', booking['total_price'])

    body = f"""
    <h2>Payment Confirmation</h2>
    <p>Your payment for the following booking has been successfully received.</p>
    <p><strong>Booking Reference:</strong> {booking['reference']}</p>
    <p><strong>Room Type:</strong> {booking['room_type']}</p>
    <p><strong>Check-in:</strong> {check_in}</p>
    <p><strong>Check-out:</strong> {check_out}</p>
    <p><strong>Amount Paid:</strong> GHS {amount_paid:.2f}</p>
    <p>Your booking is now confirmed. We look forward to welcoming you!</p>
    <p>Contact {SUPPORT_EMAIL} for assistance.</p>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_EMAIL_APP_PASS)
        server.send_message(msg)
        server.quit()
        logging.info(f"Payment confirmation email sent to {user_email} for booking {booking['reference']}")
        return True
    except Exception as e:
        logging.error(f"Error sending payment confirmation email to {user_email}: {str(e)}")
        return False


def send_booking_modification(booking, user_email):
    """Send booking modification confirmation email."""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = user_email
    msg['Subject'] = f"Booking Modified - Ref #{booking['reference']}"

    check_in = format_date(booking['check_in'])
    check_out = format_date(booking['check_out'])

    if booking.get('payment_status') == 'paid':
        body = f"""
        <h2>Booking Modification Confirmation</h2>
        <p>Your booking has been successfully modified.</p>
        <p><strong>Booking Reference:</strong> {booking['reference']}</p>
        <p><strong>Room Type:</strong> {booking['room_type']}</p>
        <p><strong>Check-in:</strong> {check_in}</p>
        <p><strong>Check-out:</strong> {check_out}</p>
        <p><strong>Total Amount:</strong> GHS {booking['total_price']:.2f}</p>
        <p>Your payment has been applied to the modified booking. No further action is required.</p>
        <p>Contact {SUPPORT_EMAIL} for assistance.</p>
        """
    else:
        auto_cancel_time = format_date(booking.get('auto_cancel_time', ''), include_time=True)
        cancellation_note = ""
        if auto_cancel_time != "N/A":
            cancellation_note = f"<p><strong>Important:</strong> Your booking will be automatically cancelled by {auto_cancel_time} if payment is not completed.</p>"
        else:
            cancellation_note = "<p><strong>Important:</strong> Your booking will be automatically cancelled within 1 hour if payment is not completed.</p>"

        if booking["payment_method"] == "momo":
            body = f"""
            <h2>Booking Modification Confirmation</h2>
            <p>Your booking has been modified. Please ensure payment is completed within 1 hour if not already paid.</p>
            {cancellation_note}
            <p><strong>Booking Reference:</strong> {booking['reference']}</p>
            <p><strong>Room Type:</strong> {booking['room_type']}</p>
            <p><strong>Check-in:</strong> {check_in}</p>
            <p><strong>Check-out:</strong> {check_out}</p>
            <p><strong>Total Amount:</strong> GHS {booking['total_price']:.2f}</p>
            <p><strong>Payment Instructions:</strong> Send payment of GHS {booking['total_price']:.2f} to Momo number {MOMO_NUMBER} with payment reference as {booking['reference']} within 1 hour.</p>
            <p>Contact {SUPPORT_EMAIL} for assistance.</p>
            """
        else:  # in-person
            body = f"""
            <h2>Booking Modification Confirmation</h2>
            <p>Your booking has been modified. Please pay a 50% deposit within 1 hour to secure your room.</p>
            {cancellation_note}
            <p><strong>Booking Reference:</strong> {booking['reference']}</p>
            <p><strong>Room Type:</strong> {booking['room_type']}</p>
            <p><strong>Check-in:</strong> {check_in}</p>
            <p><strong>Check-out:</strong> {check_out}</p>
            <p><strong>Total Amount:</strong> GHS {booking['total_price']:.2f}</p>
            <p><strong>Deposit Required:</strong> GHS {booking['deposit_amount']:.2f}</p>
            <p><strong>Payment Instructions:</strong> Send deposit of GHS {booking['deposit_amount']:.2f} to Momo number {MOMO_NUMBER} with payment reference as {booking['reference']} within 1 hour. Remaining balance due at check-in.</p>
            <p>Contact {SUPPORT_EMAIL} for assistance.</p>
            """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_EMAIL_APP_PASS)
        server.send_message(msg)
        server.quit()
        logging.info(f"Modification email sent to {user_email} for booking {booking['reference']}")
        return True
    except Exception as e:
        logging.error(f"Error sending modification email to {user_email}: {str(e)}")
        return False


def send_booking_cancellation(booking, user_email):
    """Send booking cancellation confirmation email."""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = user_email
    msg['Subject'] = f"Booking Cancelled - Ref #{booking['reference']}"

    check_in = format_date(booking['check_in'])
    check_out = format_date(booking['check_out'])

    body = f"""
    <h2>Booking Cancellation Confirmation</h2>
    <p>Your booking has been successfully cancelled, and any applicable refunds will be processed promptly.</p>
    <p><strong>Booking Reference:</strong> {booking['reference']}</p>
    <p><strong>Room Type:</strong> {booking['room_type']}</p>
    <p><strong>Check-in:</strong> {check_in}</p>
    <p><strong>Check-out:</strong> {check_out}</p>
    <p><strong>Total Amount:</strong> GHS {booking['total_price']:.2f}</p>
    <p>Contact {SUPPORT_EMAIL} for assistance with refunds or other inquiries.</p>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_EMAIL_APP_PASS)
        server.send_message(msg)
        server.quit()
        logging.info(f"Cancellation email sent to {user_email} for booking {booking['reference']}")
        return True
    except Exception as e:
        logging.error(f"Error sending cancellation email to {user_email}: {str(e)}")
        return False
