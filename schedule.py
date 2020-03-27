import dataset

from preprocess import DB_LOC

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

class Schedule:
    """
    Schedule will fetch the student's schedule and pass it back as a dict. 
    Students are identified by their Choate email address.
    """

    db = dataset.connect(DB_LOC)
    courses_database = db['courses']

    def __init__(self, email):
        if check_choate_email(email):
            self.email = email
        else:
            raise ValueError(email + " is not a valid Choate provided email address")
    
    def fetch_schedule(self):
        # return type(self.courses_database)
        return "hello"
