import dataset
import pytz
import validators
import time
from datetime import datetime, timedelta

from preprocess import DB_LOC
from fuzzysearch import find_near_matches

CLASS_SCHEDULE = {
    "Monday": "ABCDE",
    "Tuesday": "FGAB",
    "Wednesday": "ECD",
    "Thursday": "FAGB",
    "Friday": "CDEFG",
    "Saturday": "",
    "Sunday": ""
}

OFFSETS = {
    "Monday": [timedelta(hours=10), timedelta(hours=11), timedelta(hours=13), timedelta(hours=14), timedelta(hours=15)],
    "Tuesday": [timedelta(hours=10), timedelta(hours=11), timedelta(hours=13), timedelta(hours=14)],
    "Wednesday": [timedelta(hours=10), timedelta(hours=11), timedelta(hours=13)],
    "Thursday": [timedelta(hours=10), timedelta(hours=11), timedelta(hours=13), timedelta(hours=14)],
    "Friday": [timedelta(hours=10), timedelta(hours=11), timedelta(hours=13), timedelta(hours=14), timedelta(hours=15)],
    "Saturday": [],
    "Sunday": []
}

def block_iter(email):
    current_time = time.time() - (4.0 * 3600.0)
    weekday = datetime.fromtimestamp(current_time).strftime("%A")
    # weekday = "Monday"
    current_datetime = (datetime.now(pytz.timezone('EST')) + timedelta(hours=1)).replace(second=0, microsecond=0)
    midnight = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)

    classes_not_today = False

    if weekday == "Saturday":
        weekday = "Monday"
        midnight += timedelta(hours=48)
        classes_not_today = True

    elif weekday == "Sunday":
        weekday = "Monday"
        midnight += timedelta(hours=48)
        classes_not_today = True

    elif current_datetime > midnight + OFFSETS[weekday][-1] + timedelta(minutes=50):
        midnight += timedelta(hours=24)
        weekday = (current_datetime + timedelta(hours=24)).strftime("%A")
        classes_not_today = True

        if weekday == "Saturday":
            weekday = "Monday"
            midnight += timedelta(hours=48)

    blocks_today = CLASS_SCHEDULE[weekday]

    in_progress = []
    completed = []
    upcoming = []
    tomorrow = []

    schedule = ScheduleManager().getSchedule(email)

    if schedule.isTeacher:
        office_hours = [("Office Hours", "N/A")]
    else:
        office_hours = []

    class_num = 0

    if classes_not_today:
        upcoming += [("Not Today", weekday)]

    for b in "ABCDEFG":
        if b in blocks_today:
            class_time = midnight + OFFSETS[weekday][class_num]
            time_str = class_time.strftime("%I:%M %p EDT")
            time_from_now = class_time - current_datetime
            class_num += 1

            if classes_not_today:
                upcoming += [(b, time_str + " (on " + weekday + ")")]

            elif time_from_now < timedelta(minutes=-50):
                completed += [(b, time_str + " (completed)")]

            elif time_from_now < timedelta(hours=0):
                in_progress += [(b, time_str + " (in progress)")]

            elif time_from_now < timedelta(hours=15):
                upcoming += [(b, time_str + " (" + str(time_from_now)[:-3] + " from now)")]

            else:
                tomorrow += [(b, "Not Today")]
        else:
            if classes_not_today:
                tomorrow += [(b, "Not On " + weekday)]
            else:
                tomorrow += [(b, "Not Today")]

    if len(in_progress) + len(upcoming) + len(completed) > 0 and len(tomorrow) != 0:
        line_break = [("Break", "")]
    else:
        line_break = []

    return tuple(office_hours + in_progress + upcoming + completed + line_break + tomorrow)

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

class ScheduleManager(metaclass=SingletonMeta):
    def __init__(self):
        self.schedules = {}

        self.db = dataset.connect(DB_LOC)
        self.courses_database = self.db['courses']
        self.teachers_database = self.db['teachers']

    def createSchedule(self, email, name, isTeacher):
        if not self.schedules.get(email):
            self.schedules.update({email: Schedule(self.db, self.courses_database, self.teachers_database, email, name, isTeacher)})

    def getSchedule(self, email):
        return self.schedules[email]


class Schedule():
    """
    Schedule will fetch the student's schedule and pass it back as a dict. 
    Students are identified by their Choate email address.
    """

    def __init__(self, db, courses, teachers, email, name, isTeacher=False):
        self.db = db
        self.courses_database = courses
        self.teachers_database = teachers

        self.email = email
        self.name = name
        self.isTeacher = isTeacher

        self.schedule = {'A': None, 'B': None, 'C': None, 'D': None, 'E': None, 'F': None, 'G': None}

    def fetch_schedule(self):
        self.schedule = {'A': None, 'B': None, 'C': None, 'D': None, 'E': None, 'F': None, 'G': None}

        if self.isTeacher: return self.fetch_schedule_teacher()

        # Fetch the schedule and store in dictionary

        classes = self.courses_database.find(student_email=self.email)

        for c in classes:
            c = dict(c)
            block = c['block']

            if (len(block) > 1):
                block = block.replace("Fri", "fri")

                for b in "ABCDEFG":
                    if b in block:
                        c['block'] = b
                        self.schedule[b] = c.copy()
            else:
                self.schedule[block] = c


        # Represent schedule as string
        #
        # out = ""
        #
        # for block in "ABCDEFG":
        #     course = self.schedule[block]
        #
        #     if course is None:
        #         out += block + " Block: FREE<br>"
        #     elif course['meeting_id'] != 0:
        #         out += block + " Block: " + course['course_name'] + " (" + course['course'] + " " + course['sec'] + ") with " + course['teacher_name'] + ' (Meeting id ' + str(course['meeting_id']) + ')<br>'
        #     else:
        #         out += block + " Block: " + course['course_name'] + " (" + course['course'] + " " + course['sec'] + ") with " + course['teacher_name'] + '<br>'
        #
        # return out

    def fetch_schedule_teacher(self):
        # Fetch the schedule and store in dictionary

        classes = self.courses_database.find(teacher_name=self.name)

        for c in classes:
            c = dict(c)
            block = c['block']

            if block == '':
                continue

            if (len(block) > 1):
                block = block.replace("Fri", "fri")

                for b in "ABCDEFG":
                    if b in block:
                        c['block'] = b
                        self.schedule[b] = c.copy()
                        self.schedule[b]['meeting_id'] = self.teachers_database.find_one(name=self.name)[b + '_id']
            else:
                self.schedule[block] = c
                self.schedule[block]['meeting_id'] = self.teachers_database.find_one(name=self.name)[block + '_id']

    def update_schedule(self, course, section, meeting_id):
        if (self.isTeacher):
            classes_to_update = list(self.courses_database.find(course=course, sec=section))

            t = self.teachers_database.find_one(name=self.name)
            t[classes_to_update[0]['block'] + "_id"] = meeting_id
            self.teachers_database.upsert(t, ['id'])

            self.fetch_schedule_teacher()
        else:
            classes_to_update = list(self.courses_database.find(course=course, sec=section, student_email=self.email))

        print(str(len(classes_to_update)) + " entries to update")

        for c in classes_to_update:
            print("Updated " + c['student_name'])

            c['meeting_id'] = meeting_id
            self.courses_database.upsert(c, ['id'])

    def update_teacher_database(self, name, office_id):
        t = self.teachers_database.find_one(name=name)
        t['office_id'] = office_id

        self.teachers_database.upsert(t, ['id'])

    def search_teacher(self, teacher_name):
        teacher_name = teacher_name.replace(".", "").replace(",", "")
        matched_teachers = []
        all_teachers = self.teachers_database.find()

        for teacher in all_teachers:
            # if (len(find_near_matches(teacher_name, teacher['name'], max_l_dist=1)) > 0):
            if all([(len(find_near_matches(each_sub, teacher['name'], max_l_dist=1)) > 0) for each_sub in teacher_name.split(" ")]):
                matched_teachers += [teacher]

        return matched_teachers
