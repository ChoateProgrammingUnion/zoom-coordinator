#!/usr/bin/env python3
import re

from flask import Flask, render_template, redirect, url_for, request, Markup
import os
from flask_dance.contrib.google import make_google_blueprint, google 
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
import time
import secrets
from schedule import Schedule, check_choate_email, check_teacher, block_iter

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
    print(request.form)
    course = request.form.get('course')
    section = request.form.get('section')
    meeting_id = str(request.form.get('meeting_id'))
    print(meeting_id)
    id_num = -1

    lines = meeting_id.split("\n")

    for l in lines:
        id = str(re.sub(r"\D", "", l))
        if len(id) > 8 and len(id) < 12:
            id_num = int(id)

    if (id_num == -1):
        return "Error"

    email, teacher_name = get_profile()
    if email and teacher_name:
        Schedule().update_schedule(course, section, id_num)

    return "Success!"

@app.route('/')
def index():
    """
    Will contain the default views for faculty, students, and teachers
    """
    # if email := get_email():
    email, name = get_profile()
    if email and name:
        if (check_teacher(email)):
            Schedule(name=name)
        else:
            Schedule(email=email)

        # render_template here
        # print(Schedule().search_teacher("Guelakis Patrick"))

        Schedule().fetch_schedule()

        card_script = ""
        cards = ""
        # print(block_iter())
        for block, time in block_iter():
            if block == "Break":
                cards += "<hr>"
                continue

            uuid = secrets.token_hex(8)
            if check_teacher(email): # if teacher
                schedule = Schedule().schedule[block]
            else: # if student
                schedule = Schedule().schedule[block]

            if schedule is None:
                continue

            schedule["uuid"] = uuid
            schedule["time"] = time

            if schedule["meeting_id"] and schedule["meeting_id"] != "0":
                schedule["display_meeting_id"] = schedule["meeting_id"]
            else:
                schedule["display_meeting_id"] = ""


            print("Schedule", schedule) # debug

            cards += render_template("card.html", **schedule)
            card_script += render_template("card.js", **schedule)

        return render_template("index.html", cards=Markup(cards), card_js=Markup(card_script))
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
