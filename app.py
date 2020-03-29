#!/usr/bin/env python3
import re
import urllib.request

from flask import Flask, render_template, redirect, url_for, request, Markup, make_response, session
import os
from flask_dance.contrib.google import make_google_blueprint, google 
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
import secrets
from schedule import Schedule, ScheduleManager, check_choate_email, check_teacher, block_iter

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
# app.config['SERVER_NAME'] = "demo.homelabs.space"
app.config['PREFERRED_URL_SCHEME'] = "https"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "true" 

google_bp = make_google_blueprint(scope=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"])
app.register_blueprint(google_bp, url_prefix="/login", reprompt_select_account=True, reprompt_consent=True)

@app.route('/search')
def search():
    """
    Searches for teacher meeting ids
    """

    query = request.args.get('search')

    email, name = get_profile()
    user_schedule = ScheduleManager().getSchedule(email)

    search_results = user_schedule.search_teacher(query)

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
    user_schedule = ScheduleManager().getSchedule(email)

    if course == "Office Hours":
        user_schedule.update_teacher_database(teacher_name, id_num)
    elif email:
        user_schedule.update_schedule(course, section, id_num)

    return str(id_num)

@app.route('/')
def index():
    """
    Will contain the default views for faculty, students, and teachers
    """
    # if email := get_email():
    email, name = get_profile()
    if email and name:
        ScheduleManager().createSchedule(email, name, check_teacher(email))
        user_schedule = ScheduleManager().getSchedule(email)

        # render_template here
        # print(Schedule().search_teacher("Guelakis Patrick"))

        user_schedule.fetch_schedule()

        card_script = ""
        cards = ""

        toc = {'A': '', 'B': '', 'C': '', 'D': '', 'E': '', 'F': '', 'G': ''}

        # print(block_iter())
        # if check_teacher(email):
            # uuid = secrets.token_hex(8)
            # cards += render_template("class_card.html")
            # card_script += render_template("card.js")

        top_label = "Today's Classes:"
        bottom_label = "Not Today"

        for block, time in block_iter(email):
            if block == "Not Today":
                top_label = time + "'s Classes"
                bottom_label = "Not On " + time
                continue

            if block == "Break":
                cards += "<br><br><hr><br><h4>" + bottom_label + "</h4><br>"
                continue

            uuid = secrets.token_hex(8)

            if block == "Office Hours":
                try:
                    schedule = {"block": "Office", "course": "Office Hours", "course_name": "Office Hours", "teacher_name": user_schedule.name, "meeting_id": user_schedule.search_teacher(user_schedule.name)[0]['office_id']}
                except IndexError as e:
                    print("Account created", e, user_schedule.name, email, name)
                    user_schedule.db["teachers"].insert(dict(name=user_schedule.name, office_id="0")) # prevent IndexError quickfix
                    schedule = {"block": "Office", "course": "Office Hours", "course_name": "Office Hours", "teacher_name": user_schedule.name, "meeting_id": user_schedule.search_teacher(user_schedule.name)[0]['office_id']}
            else:
                schedule = user_schedule.schedule[block]

            if schedule is None:
                continue
            elif not check_teacher(email):
                teacher = user_schedule.search_teacher(schedule["teacher_name"])[0]
                schedule["office_meeting_id"] = teacher['office_id']
                schedule["user_can_change"] = not bool(teacher[schedule['block'] + "_id"])
            else:
                schedule["user_can_change"] = True

            if len(block) == 1:
                # toc[block] = '<br><li><a href="#' + block + '-block">' + block + ' Block</a></li>'
                toc[block] = render_template("toc.html", block=block)

            schedule["uuid"] = uuid
            schedule["time"] = time

            cards += render_template("class_card.html", **schedule)
            card_script += render_template("card.js", **schedule)

        return render_template("index.html",
                               cards=Markup(cards),
                               card_js=Markup(card_script),
                               toc=Markup(toc['A'] + toc['B'] + toc['C'] + toc['D'] + toc['E'] + toc['F'] + toc['G']),
                               top_label=top_label)
    else:
        return redirect("/login")

@app.route('/login')
def login():
    """
    Redirects to the proper login page (right now /google/login), but may change
    """
    session.clear()
    if not google.authorized:
        return redirect(url_for("google.login"))
    else:
        resp = make_response("Invalid credentials! Make sure you're logging in with your Choate account. <a href=" + url_for("google.login") + ">Try again.</a>")
        resp.delete_cookie('username')
        resp.delete_cookie('session')
        return resp


def get_profile():
    """
    Checks and sanitizes email. 
    Returns false if not logged in or not choate email.
    """
    # return "pguelakis@choate.edu", "Guelakis Patrick"

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
