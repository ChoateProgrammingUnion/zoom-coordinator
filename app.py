#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for
import os
from flask_dance.contrib.google import make_google_blueprint, google 
from flask_caching import Cache
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
import time
import secrets

# Temp (INSECURE, REMOVE IN PROD)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
random_secret_key = secrets.token_urlsafe(32)
app.config.update(
    DEBUG=False,
    SECRET_KEY=random_secret_key
)

cache = Cache(app, config={
    'CACHE_TYPE': 'simple'
})


# Credit: oauth boilerplate stuff from library documentation
app.config["GOOGLE_OAUTH_CLIENT_ID"] = GOOGLE_CLIENT_ID 
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = GOOGLE_CLIENT_SECRET 
app.config["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "true"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "true" 

google_bp = make_google_blueprint(scope=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"])
app.register_blueprint(google_bp, url_prefix="/login")

@google_bp.session.authorization_required
@app.route('/restricted')
def restricted():
    """
    Example of a restricted endpoint
    """
    email = get_email()
    if email:
        return "Hello, world!"

@app.route('/')
def index():
    """
    Will contain the default views for faculty, students, and teachers
    """
    # if email := get_email():
    email = get_email()
    if email:
        # render_template here
        return email
    else:
        return redirect("/login")

@app.route('/login')
def login():
    """
    Redirects to the proper login page (right now /google/login), but may change
    """
    if not google.authorized:
        return redirect(url_for("google.login"))

def get_email():
    """
    Checks and sanitizes email. 
    Returns false if not logged in or not choate email.
    """
    try:
        if google.authorized:
            resp = google.get("/oauth2/v1/userinfo")
            if resp.ok and resp.text:
                response = resp.json()
                email = str(response.get("email"))
                if check_choate_email(email):
                    return email
    except:
        pass
    return False


def check_choate_email(email: str) -> bool:
    """
    Checks to make sure that it is a valid email from Choate
    TODO: improve email validation

    The email validation should not be necessary since this is coming from 
    Google, but it also comes from client side, so we gotta check and sanitize.
    """
    if email.endswith("@choate.edu") and email.count("@") == 1 and email.count(".") == 1:
        return True
    else:
        return False
