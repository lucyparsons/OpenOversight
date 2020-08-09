from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    msg = Message(current_app.config['OO_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=current_app.config['OO_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    # Only send email if we're in prod or staging, otherwise log it so devs can see it
    if current_app.env in ("staging", "production"):
        thr = Thread(target=send_async_email, args=[current_app, msg])
        thr.start()
        return thr
    else:
        current_app.logger.info("simulated email:\n%s\n%s", subject, msg.body)
