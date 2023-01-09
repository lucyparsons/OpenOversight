from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from . import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(
        app.config["OO_MAIL_SUBJECT_PREFIX"] + " " + subject,
        sender=app.config["OO_MAIL_SENDER"],
        recipients=[to],
    )
    msg.body = render_template(template + ".txt", **kwargs)
    msg.html = render_template(template + ".html", **kwargs)
    # Only send email if we're in prod or staging, otherwise log it so devs can see it
    if app.env in ("staging", "production"):
        thr = Thread(target=send_async_email, args=[app, msg])
        app.logger.info("Sent email.")
        thr.start()
        return thr
    else:
        app.logger.info("simulated email:\n%s\n%s", subject, msg.body)
