from flask_mail import Mail, Message

mail = None


def init_mail(app):
    global mail
    mail = Mail(app)


def send_summary_email(to, subject, body, attachments=None):
    msg = Message(subject, recipients=[to], body=body)
    if attachments:
        for name, data, mimetype in attachments:
            msg.attach(name, mimetype, data)
    mail.send(msg)
