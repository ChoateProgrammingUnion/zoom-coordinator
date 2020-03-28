#!/usr/bin/env python3
import re
import urllib.request

from flask import Flask, render_template, redirect, url_for, request, Markup
import os
from flask_dance.contrib.google import make_google_blueprint, google 
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
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

@app.route('/search')
def search():
    """
    Searches for teacher meeting ids
    """

    query = request.args.get('search')

    search_results = Schedule().search_teacher(query)

    cards = ""

    for result in search_results:
        cards += render_template("teacher_card.html", **result)

    return render_template("index.html", cards=Markup(cards), card_js="")


@app.route('/update', methods=['POST'])
def update():
    """
    Gets the Zoom meeting ids
    """
    course = request.form.get('course')
    section = request.form.get('section')
    meeting_id = str(request.form.get('meeting_id'))
    id_num = -1

    lines = meeting_id.split("\n")

    for l in lines:
        id = str(re.sub(r"\D", "", l))
        if len(id) > 8 and len(id) < 12:
            id_num = int(id)

    if (id_num == -1):
        return "Error"

    with urllib.request.urlopen('https://zoom.us/j/' + str(id_num)) as response:
        html = response.read()
        if "Invalid meeting ID." in str(html):
            return "Error"

    email, teacher_name = get_profile()

    if course == "Office Hours":
        Schedule().update_teacher_database(teacher_name, id_num)
    elif email:
        Schedule().update_schedule(course, section, id_num)

    return str(id_num)

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

        toc = {'A': '', 'B': '', 'C': '', 'D': '', 'E': '', 'F': '', 'G': ''}

        # print(block_iter())
        # if check_teacher(email):
            # uuid = secrets.token_hex(8)
            # cards += render_template("class_card.html")
            # card_script += render_template("card.js")

        
        for block, time in block_iter():
            if block == "Break":
                cards += "<br><br><hr><br><br>"
                continue

            uuid = secrets.token_hex(8)

            if block == "Office Hours":
                schedule = {"block": "Office", "course": "Office Hours", "course_name": "Office Hours", "teacher_name": Schedule().name, "meeting_id": Schedule().search_teacher(Schedule().name)[0]['office_id']}
            else:
                schedule = Schedule().schedule[block]

            if schedule is None:
                continue

            if len(block) == 1:
                toc[block] = '<li><a href="#' + block + '-block">' + block + ' Block</a></li>'

            schedule["uuid"] = uuid
            schedule["time"] = time

            cards += render_template("class_card.html", **schedule)
            card_script += render_template("card.js", **schedule)

        return render_template("index.html", cards=Markup(cards), card_js=Markup(card_script), toc=Markup(toc['A'] + toc['B'] + toc['C'] + toc['D'] + toc['E'] + toc['F'] + toc['G']))
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
    # return "jpfeil@choate.edu", "Pfeil Jessica"

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
