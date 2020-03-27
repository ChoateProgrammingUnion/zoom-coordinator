from app import check_choate_email
import datset

class Schedule:
    """
    Schedule will fetch the student's schedule and pass it back as a dict. 
    Students are identified by their Choate email address.
    """
    def __init__(self, email):
        if check_choate_email(email):
            self.email = email
        else:
            raise ValueError(email + " is not a valid Choate provided email address")
    
    def fetch_schedule(self):
        pass
