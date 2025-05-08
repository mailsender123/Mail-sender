from flask import Flask, render_template, request, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
jobstores = {"default": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

def send_email(sender_email, sender_password, recipient_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return True
    except Exception as e:
        logging.error(f"Email send error: {e}")
        return False

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    if request.method == "POST":
        data = request.form
        try:
            time_parts = list(map(int, data['time'].split(':')))
            ampm = data['ampm'].lower()
            if ampm == 'pm' and time_parts[0] != 12:
                time_parts[0] += 12
            elif ampm == 'am' and time_parts[0] == 12:
                time_parts[0] = 0

            date_obj = datetime.strptime(data['date'], "%Y-%m-%d").replace(
                hour=time_parts[0], minute=time_parts[1], second=0
            )
            local_tz = pytz.timezone("Asia/Kolkata")
            date_obj = local_tz.localize(date_obj)

            if date_obj <= datetime.now(local_tz):
                return render_template("schedule.html", error="Choose a future time.")

            scheduler.add_job(
                send_email,
                DateTrigger(run_date=date_obj),
                args=[
                    data['sender_email'],
                    data['sender_password'],
                    data['recipient_email'],
                    data['subject'],
                    data['body']
                ],
                id=f"{data['sender_email']}_{date_obj.timestamp()}"
            )
            return redirect(url_for('success'))
        except Exception as e:
            return render_template("schedule.html", error=str(e))
    return render_template("schedule.html")

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)
