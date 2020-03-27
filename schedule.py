import dataset
import validators

from preprocess import DB_LOC
from fuzzysearch import find_near_matches

def check_choate_email(email: str) -> bool:
    """
    Checks to make sure that it is a valid email from Choate.
    Rely on this for email validation
    TODO: improve email validation

    The email validation should not be necessary since this is coming from
    Google, but it also comes from client side, so we gotta check and sanitize.
    """
    if validators.email(email) and email.endswith("@choate.edu") and email.count("@") == 1 and email.count(".") == 1:
        return True
    else:
        return False

def check_teacher(email: str) -> bool:
    """
    Checks if the person is a teacher (do not rely upon this, no security guarantees).
    Superset of check_choate_email.
    """
    if check_choate_email(email) and not any(char.isdigit() for char in email):
        return True
    else:
        return False

class SingletonMeta(type):
    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, '_obj'):
            cls._obj = cls.__new__(cls)
            cls._obj.__init__(*args, **kwargs)
        return cls._obj

class Schedule(metaclass=SingletonMeta):
    """
    Schedule will fetch the student's schedule and pass it back as a dict. 
    Students are identified by their Choate email address.
    """

    db = dataset.connect(DB_LOC)
    courses_database = db['courses']
    teachers_database = db['teachers']

    schedule = {'A': None,
                'B': None,
                'C': None,
                'D': None,
                'E': None,
                'F': None,
                'G': None}

    def __init__(self, email):
        if check_choate_email(email):
            self.email = email
        else:
            raise ValueError(email + " is not a valid Choate provided email address")

    def fetch_schedule(self):
        # Fetch the schedule and store in dictionary

        #  Deal with srp
        c = self.courses_database.find_one(student_email=self.email, block="A and B on Mon")
        if c is not None:
            self.schedule['A'] = c
            self.schedule['B'] = c

        for block in "ABCDEFG":
            c = self.courses_database.find_one(student_email=self.email, block=block)
            self.schedule[block] = c


        # Represent schedule as string

        out = ""

        for block in "ABCDEFG":
            course = self.schedule[block]

            if course is None:
                out += block + " Block: FREE<br>"
            elif course['meeting_id'] != 0:
                out += block + " Block: " + course['course_name'] + " (" + course['course'] + " " + course['sec'] + ") with " + course['teacher_name'] + ' (Meeting id ' + str(course['meeting_id']) + ')<br>'
            else:
                out += block + " Block: " + course['course_name'] + " (" + course['course'] + " " + course['sec'] + ") with " + course['teacher_name'] + '<br>'

        return out

    def update_schedule(self, teacher_name, course, section, meeting_id):
        classes_to_update = list(self.courses_database.find(course=course, sec=section))  # TODO Teacher name

        print(str(len(classes_to_update)) + " entries to update")

        for c in classes_to_update:
            print("Updated " + c['student_name'])

            c['meeting_id'] = meeting_id
            self.courses_database.upsert(c, ['id'])

    def search_teacher(self, teacher_name):
        matched_teachers = []
        all_teachers = self.teachers_database.find()

        for teacher in all_teachers:
            if (len(find_near_matches(teacher_name, teacher['name'], max_l_dist=1)) > 0):
                matched_teachers += [teacher]

        return matched_teachers