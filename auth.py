import dataset
from typing import Union
from app import check_choate_email
import string
import secrets
from config import *
from utils import *

class Auth(metaclass=SingletonMeta):
    """
    Generates and validates user auth tokens
    """
    def __init__(self):
        self.init_db_connection()
        self.end_db_connection()
        self.init_db_connection()
        self.keys = self.db['auth']

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
        # del self.db
        self.log_info("Disconnected From Database")

    def create_token(self, email: str) -> str:
        """
        Creates token. If creation was successful, return token. If not, return False
        """
        if check_choate_email(email):
            user = {}
            user['email'] = str(email)

            token = secrets.token_hex(16)
            user['token'] = token
            self.keys.upsert(user, ['email'])

            if self.get_email_from_token(token):
                return token

        return False

    def get_email_from_token(self, token: str) -> str:
        """
        Checks if token matches expected value
        """
        if self.possible_token(token):
            key = self.keys.find_one(token=str(token))
            if secrets.compare_digest(self.fetch_token(key['email']), token):
                return key['email']
        return ''

    def is_token(self, token: str) -> bool:
        """
        Checks if token exists and is valid
        """
        if token and self.possible_token(token):
            email = self.keys.find_one(token=str(token)).get('email')
            if check_choate_email(email):
                return True
        return False

    def fetch_token(self, email: str) -> Union[str, bool]:
        """
        Tries to fetch or make a token for a user. If not successful, return False
        """
        if self.keys.find_one(email=str(email)) and self.is_token(self.keys.find_one(email=str(email)).get('token')): # change when switch to 3.8
            token = self.keys.find_one(email=str(email)).get('token')
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

