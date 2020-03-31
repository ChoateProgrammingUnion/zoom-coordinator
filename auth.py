import dataset
from app import check_choate_email
import secrets

class Auth:
    def __init__(self):
        self.db = dataset.connect('index.db')
        self.auth = self.db['auth']

    def create_token(self, email):
        if check_choate_email(email):
            user = {}
            user['email'] = str(email)
            user['token'] = secrets.token_hex(16)
            self.auth.upsert(user, ['email'])

    def check_token(self, email, token):
        if check_choate_email(email):
            if self.auth.find_one(email=str(email)):
                expected_token = self.auth.find_one(email=email)
                if secrets.compare_digest(str(expected_token), str(token)):
                    return True

        return False
