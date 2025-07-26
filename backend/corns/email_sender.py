import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_otp(sender_email, sender_password, receiver_email, otp_string):
    """
    Sends an OTP (One-Time Password) email with a clear template.

    Args:
        sender_email (str): The email address of the sender.
        sender_password (str): The password for the sender's email account.
                                For Gmail, this should be an App Password.
        receiver_email (str): The email address of the recipient.
        otp_string (str): The One-Time Password to be sent.
    """
    subject = "Your One-Time Password (OTP)"
    body = f"""
    Hello,

    Your One-Time Password (OTP) for verification is:

    {otp_string}

    Please use this OTP to complete your action. This OTP is valid for a short period.
    Do not share this OTP with anyone.

    If you did not request this OTP, please ignore this email.

    Thank you,
    [Your Application/Service Name]
    """

    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        print(f"Attempting to connect to SMTP server for OTP...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            print(f"Logging in as {sender_email}...")
            server.login(sender_email, sender_password)
            print(f"Sending OTP to {receiver_email}...")
            server.send_message(msg)
            print("OTP email sent successfully!")

    except smtplib.SMTPAuthenticationError:
        print(
            "Error: Could not authenticate for OTP. Please check your email and app password."
        )
        print(
            "If using Gmail, ensure you've generated an 'App password' for your account."
        )
    except Exception as e:
        print(f"An error occurred while sending OTP: {e}")


if __name__ == "__main__":
    SENDER_EMAIL = "kdhakal1510@gmail.com"
    SENDER_PASSWORD = os.environ.get("SMTP_PASSWORD", None)
    if not SENDER_PASSWORD:
        raise ValueError(
            "Please provide password in environment varibale SMTP_PASSWORD"
        )
    RECEIVER_EMAIL = "leyuskc@gmail.com"

    send_otp(
        SENDER_EMAIL,
        SENDER_PASSWORD,
        RECEIVER_EMAIL,
        "213dawd",
    )
