import dataset
from flask_dance.contrib.google import make_google_blueprint, google 
from typing import Union
from app import check_choate_email
import string
import secrets
import inspect
from config import *
from utils import *
import oauthlib
import urllib.request

class Auth():
    """
    Generates and validates user auth tokens
    """
    def __init__(self):
        self.logheader = ""
        self.init_db_connection()
        self.end_db_connection()

    def init_db_connection(self, attempt=0):
        try:
            self.db = dataset.connect(DB, engine_kwargs={'pool_recycle': 3600, 'pool_pre_ping': True})
            self.log_info("New Database Connection")
        except ConnectionResetError as e:
            self.log_info("ConnectionResetError " + str(e) + ", attempt: " + str(attempt))
            if attempt <= 3:
                self.db.close()
                self.init_db_connection(attempt=attempt+1)
        except AttributeError as e:
            self.log_info("AttributeError " + str(e) + ", attempt: " + str(attempt))
            if attempt <= 3:
                self.db.close()
                self.init_db_connection(attempt=attempt+1)

    def end_db_connection(self):
        self.db.close()
        self.log_info("Disconnected From Database")
        # del self.db

    def create_token(self, email: str) -> str:
        """
        Creates token. If creation was successful, return token. If not, return False
        """
        if check_choate_email(email):
            user = {}
            user['email'] = str(email)

            token = secrets.token_hex(16)
            user['token'] = token
            self.db['auth'].upsert(user, ['email'])

            if self.get_email_from_token(token):
                return token

        return False

    def get_email_from_token(self, token: str) -> str:
        """
        Checks if token matches expected value
        """
        if self.possible_token(token):
            key = self.db['auth'].find_one(token=str(token))
            if secrets.compare_digest(self.fetch_token(key['email']), token):
                return key['email']
        return ''

    def email_token_pair_check(self, email: str, token: str) -> bool:
        expected_email = self.get_email_from_token(token)
        if self.is_token(token) and secrets.compare_digest(email, expected_email) and secrets.compare_digest(token, self.fetch_token(expected_email)):
            return True
        return False


    def is_token(self, token: str) -> bool:
        """
        Checks if token exists and is valid
        """
        if token and self.possible_token(token):
            email = self.db['auth'].find_one(token=str(token)).get('email')
            if check_choate_email(email):
                return True
        return False

    def fetch_token(self, email: str) -> Union[str, bool]:
        """
        Tries to fetch or make a token for a user. If not successful, return False
        """
        if self.db['auth'].find_one(email=str(email)) and self.is_token(self.db['auth'].find_one(email=str(email)).get('token')): # change when switch to 3.8
            token = self.db['auth'].find_one(email=str(email)).get('token')
            return token
        else:
            return self.create_token(str(email))

    def possible_token(self, token: str) -> str:
        """
        Validates if the input is a valid 128-bit token (16 byte)
        """
        try:
            if isinstance(int(str(token), 16), int) and all(c in string.hexdigits for c in str(token)):
                if len(str(token)) == 32:
                    if not "/" in token:  # extra validation
                        return True
        except:
            return False
        return False
    def log_info(self, msg):
        log_info(msg, self.logheader, frame=inspect.currentframe().f_back)

    def log_error(self, msg):
        log_error(msg, self.logheader, frame=inspect.currentframe().f_back)

def check_login(request) -> str:
    """
    Returns tuple of email, firstname, and lastname
    """
    token = request.cookies.get('token')
    email = request.cookies.get('email')
    firstname = request.cookies.get('firstname')
    lastname = request.cookies.get('lastname')

    authentication = Auth()

    authentication.init_db_connection()
    if authentication.email_token_pair_check(email, token):
        authentication.end_db_connection()
        log_info("Successfully checked cookie login for " + email)
        return email, firstname, lastname
    else:
        authentication.end_db_connection()
        log_info("Unsuccessfully checked cookie login for " + str(email))
        return get_profile()

def set_login(response, request) -> str:
    """
    Here, we assume that users are already authenticated
    """
    email, firstname, lastname = check_login(request)
    if email and firstname and lastname:
        response.set_cookie('email', email)
        response.set_cookie('firstname', firstname)
        response.set_cookie('lastname', lastname)

        token = get_token(request)
        response.set_cookie('token', token)
        log_info("Set login for " + email)
        return response
    return response

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

def get_token(request):
    email, firstname, lastname = check_login(request)
    if email and firstname and lastname and check_choate_email(email):
        authentication = Auth()
        authentication.init_db_connection()
        token = authentication.fetch_token(email)
        authentication.end_db_connection()
        return token
    return False
