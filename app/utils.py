import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

def send_otp_email(recipient_email, otp_code, expiry_time):
    """Send OTP code via Gmail SMTP. Returns True on success, False on failure."""
    # Pull values directly out of the running Flask context configuration map
    sender_email = current_app.config.get("SMTP_EMAIL")
    sender_password = current_app.config.get("SMTP_PASSWORD")
    smtp_server = current_app.config.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = current_app.config.get("SMTP_PORT", 587)

    if not sender_email or not sender_password:
        print("[EMAIL ERROR] SMTP variables missing inside system config runtime context.")
        return False  # SMTP not configured, caller should fallback to terminal printing

    subject = "Botanica - Your Password Reset Code"

    html_body = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #2f855a, #1a3a2a); padding: 30px 24px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 700;">Botanica</h1>
            <p style="color: #c6f6d5; margin: 6px 0 0; font-size: 14px;">Herbal Marketplace</p>
        </div>
        <div style="padding: 32px 24px;">
            <h2 style="color: #1a202c; margin: 0 0 12px; font-size: 20px;">Password Reset Request</h2>
            <p style="color: #4a5568; font-size: 14px; line-height: 1.6; margin: 0 0 24px;">
                We received a request to reset your password. Use the verification code below to proceed:
            </p>
            <div style="background: #f0fff4; border: 2px dashed #2f855a; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 24px;">
                <span style="font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #2f855a;">{otp_code}</span>
            </div>
            <p style="color: #718096; font-size: 13px; margin: 0 0 8px;">
                This code expires at <strong>{expiry_time}</strong> (10 minutes from now).
            </p>
            <p style="color: #a0aec0; font-size: 12px; margin: 24px 0 0; border-top: 1px solid #e2e8f0; padding-top: 16px;">
                If you did not request this, please ignore this email. Your password will remain unchanged.
            </p>
        </div>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Botanica <{sender_email}>"
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"[EMAIL] OTP sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send OTP email: {e}")
        return False


def image_or_default(image_path, default_type='herb'):
    import os
    if not image_path:
        return get_default_image(default_type)
    
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    
    clean_path = image_path
    if clean_path.startswith('/static/'):
        clean_path = clean_path[8:]
    elif clean_path.startswith('static/'):
        clean_path = clean_path[7:]
        
   