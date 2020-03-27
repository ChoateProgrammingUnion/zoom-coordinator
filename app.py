#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for, request, Markup
import os
from flask_dance.contrib.google import make_google_blueprint, google 
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
import time
import secrets
from schedule import ScheduleStudent, ScheduleTeacher, check_choate_email, check_teacher

# Temp (INSECURE, REMOVE IN PROD)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)

random_secret_key = secrets.token_urlsafe(32)
app.config.update(
    DEBUG=False,
    SECRET_KEY=random_secret_key
)

# Credit: oauth boilerplate stuff from library documentation
app.config["GOOGLE_OAUTH_CLIENT_ID"] = GOOGLE_CLIENT_ID 
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = GOOGLE_CLIENT_SECRET 
app.config["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "true"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "true" 

google_bp = make_google_blueprint(scope=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"])
app.register_blueprint(google_bp, url_prefix="/login")

@app.route('/restricted')
def restricted():
    """
    Example of a restricted endpoint
    """
    email, name = get_profile()
    if email and name:
        return "Hello, world!"

@app.route('/update', methods=['POST'])
def update():
    """
    Gets the Zoom meeting ids
    """
    course = request.args.get('course')
    section = request.args.get('section')
    meeting_id = request.args.get('section')

    if not meeting_id.isdigit():
        return False

    email, teacher_name = get_profile()
    if email and teacher_name:
        return ScheduleStudent(email).update_schedule(teacher_name, course, section, meeting_id)

@app.route('/')
def index():
    """
    Will contain the default views for faculty, students, and teachers
    """
    # if email := get_email():
    email, name = get_profile()
    if email and name:
        # render_template here
        ScheduleStudent(email).update_schedule("", "SP250S-HO", 11, 100)
        ScheduleStudent(email).fetch_schedule()

        cards = ""
        for block in "ABCDEFG":
            if check_teacher(email): # if teacher
                schedule = ScheduleTeacher(name).schedule[block]
            else: # if student
                schedule = ScheduleStudent(email).schedule[block]

            if schedule is None:
                continue

            cards += render_template("cardStudent.html", **schedule)

        return render_template("index.html", cards=Markup(cards))
    else:
        return redirect("/login")

@app.route('/login')
def login():
    """
    Redirects to the proper login page (right now /google/login), but may change
    """
    if not google.authorized:
        return redirect(url_for("google.login"))

def get_profile():
    """
    Checks and sanitizes email. 
    Returns false if not logged in or not choate email.
    """
    try:
        if google.authorized:
            resp = google.get("/oauth2/v1/userinfo")
            if resp.ok and resp.text:
                response = resp.json()
                if response.get("verified_email") == True and response.get("hd") == "choate.edu":
                    email = str(response.get("email"))
                    name = str(response.get("name"))
                    if check_choate_email(email):
                        return email, name
                else:
                    print(response) # log next
    except:
        pass
    return False, False
