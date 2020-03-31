import dataset
from typing import Union
from app import check_choate_email
import string
import secrets

class Auth:
    """
    Generates and validates user auth tokens
    """
    def __init__(self):
        self.db = dataset.connect('sqlite:///index.db')
        self.keys = self.db['auth']

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

            if self.check_token(email, token):
                return token

        return False

    def check_token(self, email: str, token: str) -> bool:
        """
        Checks if token matches expected value
        """
        if check_choate_email(email) and self.possible_token(token):
            if self.keys.find_one(email=str(email)):
                expected_token = self.keys.find_one(email=str(email)).get('token')
                if secrets.compare_digest(str(expected_token), str(token)):
                    return True
        return False

    def is_token(self, token: str) -> bool:
        """
        Checks if token exists and is valid
        """
        if token and self.possible_token(token):
            email = self.keys.find_one(token=str(token)).get('email')
            if check_choate_email(email) and self.check_token(email, token):
                return True
        return False

    def fetch_token(self, email: str) -> Union[str, bool]:
        """
        Tries to fetch or make a token for a user. If not successful, return False
        """
        if self.is_token(self.keys.find_one(email=str(email)).get('token')):
            token = self.keys.find_one(email=str(email)).get('token')
            if self.check_token(email, token):
                return token
        else:
            return self.create_token(str(email))
        return False

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

