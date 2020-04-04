#!/usr/bin/env python3
import re
import urllib.request
import oauthlib

from flask import Flask, render_template, redirect, url_for, request, Markup, make_response, session, send_file, escape
import os
import git
import functools
from icalendar import Calendar, Event
from flask_dance.contrib.google import make_google_blueprint, google 
from config import *
import secrets
from schedule import Schedule, ScheduleManager, check_choate_email, check_teacher, block_iter
from ical import make_calendar
import auth
import config

from utils import *

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
app.config['SERVER_NAME'] = SERVER_NAME 
app.config['PREFERRED_URL_SCHEME'] = "https"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "true" 

google_bp = make_google_blueprint(scope=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"], offline=True)
# app.register_blueprint(google_bp, url_prefix="/login", reprompt_select_account=True, reprompt_consent=True)
app.register_blueprint(google_bp, url_prefix="/login")

@app.route('/admin/secure.log')
def secure():
    """
    Securely returns a log of all actions taken
    """
    # email, firstname, lastname = get_profile()
    # if email and firstname and lastname and check_choate_email(email):
        # log.info("here")
    token = request.args.get('token')
    if secrets.compare_digest(token,config.TOKEN):
        log_info("Log accessed "+ str(request.args))
        return send_file("live_detector.log")
    else:
        log_info("Log deny access "+ str(request.args))

    return redirect('/')

@app.route('/api/calendar.ics')
def cal():
    """
    Checks authorization of user to request ical file
    """
    # email, firstname, lastname = get_profile()
    # if email and firstname and lastname and check_choate_email(email):
        # log.info("here")
    token = request.args.get('token')
    email = request.args.get('email')
    firstname = request.args.get('first')
    lastname = request.args.get('last')
    authentication = auth.Auth()

    authentication.init_db_connection()
    email = authentication.get_email_from_token(token)

    authentication.end_db_connection()

    if email:

        cal = make_response(make_calendar(email, firstname, lastname).to_ical())
        cal.mimetype = 'text/calendar'
        return cal

    return redirect('/')

def get_calendar():
    email, firstname, lastname = get_profile()
    if email and firstname and lastname and check_choate_email(email):
        authentication = auth.Auth()
        authentication.init_db_connection()
        token = authentication.fetch_token(email)
        authentication.end_db_connection()
        return token
    return False

@app.route('/search')
def search():
    """
    Searches for teacher meeting ids
    """
    email, firstname, lastname = get_profile()
    if email and firstname and lastname:
        query = request.args.get('search')

        # ScheduleManager().createSchedule(email, firstname, lastname, check_teacher(email))
        user_schedule = ScheduleManager().getSchedule(email, firstname, lastname, check_teacher(email))
        user_schedule.init_db_connection()

        search_results = user_schedule.search_teacher(query)

        cards = ""

        for result in search_results:
            desc = result.get('office_desc')
            if desc is None:
                desc = ""

            result["office_desc"] = Markup(str(escape(desc)).replace("\n", "<br>"))

            cards += render_template("teacher_card.html", **result)

        commit = get_commit()
        calendar_token = get_calendar()
        user_schedule.end_db_connection()
        return render_template("index.html", cards=Markup(cards), card_js="", commit=commit, calendar_token=calendar_token, email=email, firstname=firstname, lastname=lastname)
    else:
        return redirect("/")


@app.route('/update', methods=['POST'])
def update():
    """
    Gets the Zoom meeting ids
    """
    course = request.form.get('course')
    section = request.form.get('section')
    meeting_id = str(request.form.get('meeting_id'))

    if course == "Office Hours" and section == "DESC":
        email, firstname, lastname = get_profile()
        if email and firstname and lastname:
            if meeting_id is None:
                meeting_id = ''

            user_schedule = ScheduleManager().getSchedule(email, firstname, lastname, check_teacher(email))
            user_schedule.init_db_connection()

            user_schedule.update_teacher_database_office_description(email, escape(meeting_id))

            return "Success"

        return "Error"

    if not(course and section and meeting_id):
        return "Error"

    lines = meeting_id.split("\n")

    for l in lines:
        id = str(re.sub(r"\D", "", l))
        if len(id) > 8 and len(id) < 12:
            id_num = int(id)

    if (id_num == -1):
        return "Error"

    # with urllib.request.urlopen('https://zoom.us/j/' + str(id_num)) as response:
        # html = response.read()
        # if "Invalid meeting ID." in str(html):
            # return "Error"

    email, firstname, lastname = get_profile()
    if course and section and meeting_id and email and firstname and lastname:
        user_schedule = ScheduleManager().getSchedule(email, firstname, lastname, check_teacher(email))
        user_schedule.init_db_connection()

        if course == "Office Hours":
            if section == "ID":
                user_schedule.update_teacher_database_office_id(email, id_num)
            if section == "DESC":
                user_schedule.update_teacher_database_office_description(email, id_num)
        elif email:
            user_schedule.update_schedule(course, section, id_num)

        user_schedule.end_db_connection()
        return str(id_num)
    return "Error"

@app.route('/')
def index():
    """
    Will contain the default views for faculty, students, and teachers
    """
    # if email := get_email():
    email, firstname, lastname = get_profile()
    if email and firstname and lastname:
        # ScheduleManager().createSchedule(email, firstname, lastname, check_teacher(email))
        user_schedule = ScheduleManager().getSchedule(email, firstname, lastname, check_teacher(email))
        user_schedule.init_db_connection()

        # render_template here
        # log.info(Schedule().search_teacher_exact("Guelakis Patrick"))

        user_schedule.fetch_schedule()

        card_script = ""
        cards = ""

        toc = {'A': '', 'B': '', 'C': '', 'D': '', 'E': '', 'F': '', 'G': ''}

        # log.info(block_iter())
        # if check_teacher(email):
            # uuid = secrets.token_hex(8)
            # cards += render_template("class_card.html")
            # card_script += render_template("card.js")

        top_label = "Today's Classes:"
        bottom_label = "Not Today"

        for block, start_time in block_iter(email, firstname, lastname, isTeacher=check_teacher(email)):
            if block == "Not Today":
                top_label = start_time + "'s Classes"
                bottom_label = "Not On " + start_time
                continue

            if block == "Break":
                cards += "<br><br><hr><br><h4>" + bottom_label + "</h4><br>"
                continue

            uuid = secrets.token_hex(8)

            schedule = None

            if block == "Office Hours":
                try:
                    teacher = user_schedule.search_teacher_email_with_creation(user_schedule.email, user_schedule.lastname, user_schedule.firstname)

                    schedule = {"block": "Office",
                                "course": "Office Hours",
                                "course_name": "Office Hours",
                                "teacher_name": str(user_schedule.firstname).title() + " " + str(user_schedule.lastname).title(),
                                "meeting_id": teacher['office_id'],
                                "teacher_email": 'placeholder',
                                "office_desc": teacher.get('office_desc')}

                    if schedule['office_desc'] is None:
                        schedule['office_desc'] = ''
                except TypeError as e:
                    log_error("Unable to create teacher schedule due to failed query")
            else:
                schedule = user_schedule.schedule[block]

            if schedule is None:
                continue
            elif not check_teacher(email):
                teacher = user_schedule.search_teacher_email(schedule["teacher_email"])
                schedule["office_meeting_id"] = teacher.get('office_id')

                desc = teacher.get('office_desc')
                if desc is None:
                    desc = ""

                schedule["office_desc"] = Markup(str(escape(desc)).replace("\n", "<br>"))
                schedule["user_can_change"] = not bool(teacher.get(schedule.get('block') + "_id"))
            else:
                schedule["user_can_change"] = True

            if len(block) == 1:
                # toc[block] = '<br><li><a href="#' + block + '-block">' + block + ' Block</a></li>'
                toc[block] = render_template("toc.html", block=block)

            schedule["uuid"] = uuid
            schedule["time"] = start_time

            if block == "Office Hours":
                schedule['office_desc'] = str(escape(str(schedule['office_desc']).replace('\\', '\\\\'))).replace('\n', '\\n')

                cards += render_template("office_hours_card.html", **schedule)
                card_script += render_template("office_hours.js", **schedule)
            else:
                cards += render_template("class_card.html", **schedule)
                card_script += render_template("card.js", **schedule)

        commit = get_commit()
        calendar_token = get_calendar()
        user_schedule.end_db_connection()
        return render_template("index.html",
                               cards=Markup(cards),
                               card_js=Markup(card_script),
                               toc=Markup(toc['A'] + toc['B'] + toc['C'] + toc['D'] + toc['E'] + toc['F'] + toc['G']),
                               top_label=top_label,
                               calendar_token=calendar_token,
                               email=email,
                               firstname=str(firstname).title(),
                               lastname=str(lastname).title(),
                               commit=commit)
    else:
        button = render_template("login.html")
        commit = get_commit()
        return render_template("landing.html", button=Markup(button), commit=commit)
        # return redirect("/login")

@app.route('/help')
def help():
    commit = get_commit()
    button = render_template("back.html")
    return render_template("landing.html", button=Markup(button), commit=commit)

@app.route('/login')
def login():
    """
    Redirects to the proper login page (right now /google/login), but may change
    """
    if not google.authorized:
        return redirect(url_for("google.login"))
    else:
        resp = make_response("Invalid credentials! Make sure you're logging in with your Choate account. <a href=\"/logout\">Try again.</a>")
        return resp

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

@functools.lru_cache()
def get_commit():
    """
    Returns latest commit hash
    """
    repo = git.Repo(search_parent_directories=True)
    return repo.head.object.hexsha

def get_profile(attempt=0):
    """
    Checks and sanitizes email. 
    Returns false if not logged in or not choate email.
    """
    # return "mfan21@choate.edu", "Fan Max"
    # return "echapman22@choate.edu", "Ethan", "Chapman"

    if attempt <= 0:
        try:
            if google.authorized:
                resp = google.get("/oauth2/v1/userinfo")
                if resp.ok and resp.text:
                    response = resp.json()
                    if response.get("verified_email") == True and response.get("hd") == "choate.edu":
                        email = str(response.get("email"))
                        first_name = str(response.get('given_name'))
                        last_name = str(response.get('family_name'))

                        if check_choate_email(email):
                            log_info("Profile received successfully", "[" + first_name + " " + last_name + "] ")
                            return email, first_name, last_name
                    else:
                        log_error("Profile retrieval failed with response " + str(response) + ", attempt" + str(attempt)) # log next
        except oauthlib.oauth2.rfc6749.errors.InvalidClientIdError:
            session.clear()
            log_info("Not Google authorized and InvalidClientIdError, attempt:" + str(attempt)) # log next
            return get_profile(attempt=attempt+1)
        except oauthlib.oauth2.rfc6749.errors.TokenExpiredError:
            session.clear()
            log_info("Not Google authorized and TokenExpiredError, attempt:" + str( attempt)) # log next
            return get_profile(attempt=attempt+1)

        log_info("Not Google authorized, attempt: " + str(attempt)) # log next
        return False, False, False
    else:
        log_info("Attempts exhausted: " + str(attempt)) # log next
        return False, False, False
