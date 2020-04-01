from __future__ import annotations

import dataset
import copy
from filelock import Timeout, FileLock

import pytz
import functools
import validators
import time
from datetime import datetime, timedelta

from config import  DB as DB_LOC
from rapidfuzz import fuzz

from utils import *

CLASS_SCHEDULE = {
    "Monday": "ABCDE",
    "Tuesday": "FGBA",
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

def block_iter(email, datetime_needed=False, weekday=False):
    current_datetime = datetime.now(pytz.timezone('US/Eastern')).replace(second=0, microsecond=0)
    midnight = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)

    if not weekday:
        weekday = current_datetime.strftime("%A")

    if datetime_needed:
        current_datetime = current_datetime.replace(hour=1, minute=0, second=0, microsecond=0)

    # else:
        # current_datetime = current_datetime.replace(month=day=

    classes_not_today = False

    if weekday == "Saturday":
        weekday = "Monday"
        midnight += timedelta(hours=48)
        classes_not_today = True

    elif weekday == "Sunday":
        weekday = "Monday"
        midnight += timedelta(hours=48)
        classes_not_today = True

    elif current_datetime > midnight + OFFSETS[weekday][-1] + timedelta(minutes=50) and not datetime_needed:
        midnight += timedelta(hours=24)
        weekday = midnight.strftime("%A")
        classes_not_today = True

        if weekday == "Saturday":
            weekday = "Monday"
            midnight += timedelta(hours=48)

    blocks_today = CLASS_SCHEDULE[weekday]
    all_blocks = blocks_today + "".join([i for i in "ABCDEFG" if i not in blocks_today])

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

    for b in all_blocks:
        if b in blocks_today:
            class_time = midnight + OFFSETS[weekday][class_num]
            time_str = class_time.strftime("%I:%M %p EDT")
            time_from_now = class_time - current_datetime
            class_num += 1

            if not datetime_needed:
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
                tomorrow += [(b, class_time)]
        else:
            if not datetime_needed:
                if classes_not_today:
                    tomorrow += [(b, "Not On " + weekday)]
                else:
                    tomorrow += [(b, "Not Today")]

    if len(in_progress) + len(upcoming) + len(completed) > 0 and len(tomorrow) != 0:
        line_break = [("Break", "")]
    else:
        line_break = []

    if not datetime_needed:
        return tuple(office_hours + in_progress + upcoming + completed + line_break + tomorrow)
    else:
        return tuple(tomorrow)

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

class ScheduleManager(metaclass=SingletonMeta):
    def __init__(self):
        self.schedules = {}

    def createSchedule(self, email, firstname, lastname, isTeacher):
        if not self.schedules.get(email):
            self.schedules.update({email: Schedule(email, firstname, lastname, isTeacher)})

    def getSchedule(self, email) -> Schedule:
        return self.schedules[email]


class Schedule():
    """
    Schedule will fetch the student's schedule and pass it back as a dict. 
    Students are identified by their Choate email address.
    """

    def __init__(self, email, firstname, lastname, isTeacher=False):
        self.logheader = "[" + firstname + " " + lastname + "] "

        log.info(self.logheader + "Called Schedule.__init__ with paramaters: " + str((email, firstname, lastname, isTeacher)))

        sanitize = lambda name: str(name).replace(' ', '').replace(',', '').replace('.', '').replace('-', '').lower().rstrip()

        self.email = email
        self.firstname = sanitize(firstname)
        self.lastname = sanitize(lastname)
        self.isTeacher = isTeacher

        self.schedule = {'A': None, 'B': None, 'C': None, 'D': None, 'E': None, 'F': None, 'G': None}

    def fetch_schedule(self):
        log.info(self.logheader + "Called Schedule.fetch_schedule")

        self.schedule = {'A': None, 'B': None, 'C': None, 'D': None, 'E': None, 'F': None, 'G': None}

        if self.isTeacher: return self.fetch_schedule_teacher()

        # Fetch the schedule and store in dictionary

        classes = self.courses_database_find(student_email=self.email, caller='(fetch_schedule) ')

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

    def fetch_schedule_teacher(self):
        log.info(self.logheader + "Called Schedule.fetch_schedule_teacher")

        # Fetch the schedule and store in dictionary

        classes = self.courses_database_find(teacher_email=self.email, caller='(fetch_schedule_teacher) ')

        teacher = self.search_teacher_email(self.email, caller='(fetch_schedule_teacher) ')

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
                        self.schedule[b]['meeting_id'] = teacher[b + '_id']
            else:
                self.schedule[block] = c
                self.schedule[block]['meeting_id'] = teacher[block + '_id']

    def update_schedule(self, course, section, meeting_id):
        log.info(self.logheader + "Called Schedule.update_schedule with paramaters: " + str((course, section, meeting_id)))

        self.init_db_connection(caller + '(update_schedule) ')
        if (self.isTeacher):
            classes_to_update = list(self.courses_database_find(course=course, sec=section, caller='(update_schedule) '))

            self.update_teacher_database_block_id(course + " " + str(section), meeting_id)

            self.fetch_schedule_teacher()
        else:
            classes_to_update = list(self.courses_database_find(course=course, sec=section, student_email=self.email, caller='(update_schedule) '))

        log.info(self.logheader + "(update_schedule) " + str(len(classes_to_update)) + " entries to update")

        for c in classes_to_update:
            log.info(self.logheader + "(update_schedule) Updated " + c['student_name'])

            c['meeting_id'] = meeting_id
            self.course_database_upsert(c, caller='(update_schedule) ')

        self.end_db_connection(caller + '(update_schedule) ')

    def update_teacher_database_office_id(self, firstname, lastname, office_id):
        log.info(self.logheader + "Called Schedule.update_teacher_database_office_id with paramaters: " + str((firstname, lastname, office_id)))

        sanitize = lambda name: str(name).replace(' ', '').replace(',', '').replace('.', '').replace('-', '').lower().rstrip()
        firstname = sanitize(firstname)
        lastname = sanitize(lastname)

        self.init_db_connection(caller + '(update_teacher_database_office_id) ')
        t = self.teacher_database_find_one(first_name=firstname, last_name=lastname, caller='(update_teacher_database_office_id) ')

        if t is None:
            log.error(self.logheader + "(update_teacher_database_office_id) Failed to query teacher database for " + str((firstname, lastname)))

        t['office_id'] = office_id

        self.teacher_database_upsert(t, caller='(update_teacher_database_office_id) ')
        self.end_db_connection(caller + '(update_teacher_database_office_id) ')

    def update_teacher_database_block_id(self, course, id, caller=''):
        log.info(self.logheader + caller + "Called Schedule.update_teacher_database_block_id with paramaters: " + str((course, id)))

        self.init_db_connection(caller + '(update_teacher_database_block_id) ')
        t = self.teacher_database_find_one(first_name=self.firstname, last_name=self.lastname, caller=caller+'(update_teacher_database_block_id) ')

        block = ""
        for b in "ABCDEFG":
            if t[b] == course:
                log.info(self.logheader + "(update_teacher_database_block_id) Updating " + b + " Block")
                block = b
                t[block + "_id"] = str(id)

        if block == "":
            log.info(self.logheader + "(update_teacher_database_block_id) Class Not Found")
            return

        self.teacher_database_upsert(t, caller=caller+'(update_teacher_database_block_id) ')
        self.end_db_connection(caller + '(update_teacher_database_block_id) ')

    # @functools.lru_cache(maxsize=1000)
    def search_teacher(self, teacher_name: str) -> list:
        log.info(self.logheader + "Called Schedule.search_teacher with paramaters: " + str((teacher_name)))

        teacher_name = teacher_name.replace(".", "").replace(",", "").replace("-", "").lower().rstrip()
        matched_teachers = []
        all_teachers = self.get_all_teachers(caller='(search_teacher) ')

        # if self.search_teacher_exact(teacher_name):
        #     exact_teacher = self.search_teacher_exact(teacher_name)
        #     matched_teachers += [exact_teacher]
        #     all_teachers.remove(exact_teacher)

        for teacher in all_teachers:
            teacher_lower = teacher['name'].replace(".", "").replace(",", "").replace("-", "").lower().rstrip()
            # if (len(find_near_matches(teacher_name, teacher['name'], max_l_dist=1)) > 0):
            if teacher_name in teacher_lower:
                matched_teachers.insert(0, teacher)

            # if (not teacher in matched_teachers) and all([(len(find_near_matches(each_sub, teacher_lower, max_l_dist=1)) > 0) for each_sub in [x for x in teacher_name.split(" ") if x]]):
            if (not teacher in matched_teachers) and all([(fuzz.partial_ratio(word, teacher_lower) > 70.0) for word in [x for x in teacher_name.split(" ") if x]]):
                matched_teachers += [teacher]

        return matched_teachers

    def search_teacher_email(self, email, caller=''):
        log.info(self.logheader + caller + "Called Schedule.search_teacher_email with paramaters: " + str((email)))

        all_teachers = self.get_all_teachers(caller=caller+"(search_teacher_email) ")

        for teacher in all_teachers:
            if teacher.get('email') and str(teacher.get('email')).rstrip() == email.rstrip():
                return teacher

        log.info(self.logheader + caller + "(teacher_search_email) Queried " + str(email) + " and got no result")

    def search_teacher_email_with_creation(self, email, lastname, firstname, reverse=True):
        log.info(self.logheader + "Called Schedule.search_teacher_email_with_creation with paramaters: " + str((email, lastname, firstname, reverse)))
        self.init_db_connection(caller + '(search_teacher_email_with_creation) ')

        result = self.search_teacher_email(email)

        if result:
            return result

        log.info(self.logheader + "(search_teacher_email_with_creation) Failed to find entry, creating new one")

        self.teacher_database_insert({"name": firstname.rstrip().title() + " " + lastname.rstrip().title(),
                                       "first_name": firstname,
                                       "last_name": lastname,
                                       "email": email,
                                       "office_id":0})

        self.end_db_connection(caller + '(search_teacher_email_with_creation) ')

        return self.teacher_database_find_one(email=email, caller='(search_teacher_email_with_creation) ')



    def transactional_upsert(self, table: str, data: dict, key: list, attempt=0, caller='') -> bool:
        log.info(self.logheader + caller + "Called Schedule.transactional_upsert with paramaters: " + str((table, data, key, attempt)))
        if attempt <= 3:
            self.init_db_connection(caller + '(transactional_upsert) ')
            try:
                lock = FileLock("index.db.lock")
                with lock:
                    self.db.begin()
                    try:
                        self.db[str(table)].upsert(dict(copy.deepcopy(data)), list(key))
                        self.db.commit()
                        self.end_db_connection(caller + '(transactional_upsert) ')
                        return True
                    except:
                        self.db.rollback()
                        log.info(self.logheader + caller + " (transactional_upsert) Exception caught with DB, rolling back and trying again " + str((table, data, key, attempt)))
                        self.end_db_connection(caller + '(transactional_upsert) ')
                        return self.transactional_upsert(table, data, key, attempt=attempt+1)
            except:
                self.end_db_connection(caller + '(transactional_upsert) ')
                return self.transactional_upsert(table, data, key, attempt=attempt+1)
        else:
            log.info(self.logheader + caller + " (transactional_upsert) Automatic re-trying failed with these args: " + str((table, data, key, attempt)))

        self.end_db_connection(caller + '(transactional_upsert) ')
        return False

    def teacher_database_insert(self, data, caller=''):
        log.info(self.logheader + caller + "Called Schedule.teacher_database_insert with paramaters: " + str((data)))

        self.init_db_connection(caller + '(teacher_database_insert) ')
        self.db['teachers'].insert(data)
        self.end_db_connection(caller + '(teacher_database_insert) ')

    def get_all_teachers(self, caller=''):
        log.info(self.logheader + caller + "Called Schedule.get_all_teachers")

        self.init_db_connection(caller + '(get_all_teachers) ')
        result = self.db['teachers'].all()
        self.end_db_connection(caller + '(get_all_teachers) ')
        return result

    def teacher_database_upsert(self, data, caller=''):
        log.info(self.logheader + caller + "Called Schedule.teacher_database_upsert with paramaters: " + str((data)))

        self.init_db_connection(caller + '(teacher_database_upsert) ')

        while not self.transactional_upsert('teachers', data, ['id']):
            pass

        self.end_db_connection(caller + '(teacher_database_upsert) ')

    def course_database_upsert(self, data, caller=''):
        log.info(self.logheader + caller + "Called Schedule.course_database_upsert with paramaters: " + str((data)))

        self.init_db_connection(caller + '(course_database_upsert) ')

        while not self.transactional_upsert('courses', data, ['id']):
            pass

        self.end_db_connection(caller + '(course_database_upsert) ')

    def teacher_database_find_one(self, caller='', *args, **kwargs):
        log.info(self.logheader + caller + "Called Schedule.teacher_database_find_one with paramaters: " + str((args, kwargs)))

        self.init_db_connection(caller + '(teacher_database_find_one) ')
        result = self.db['teachers'].find_one(*args, **kwargs)
        self.end_db_connection(caller + '(teacher_database_find_one) ')
        return result

    def courses_database_find(self, caller='', *args, **kwargs):
        log.info(self.logheader + caller + "Called Schedule.courses_database_find with paramaters: " + str((args, kwargs)))

        self.init_db_connection(caller + '(courses_database_find) ')
        result = self.db['courses'].find(*args, **kwargs)
        self.end_db_connection(caller + '(courses_database_find) ')
        return result

    def init_db_connection(self, caller=''):
        self.db = dataset.connect(DB_LOC)
        log.info(self.logheader + caller + "New Database Connection")

    def end_db_connection(self, caller=''):
        self.db.close()
        del self.db
        log.info(self.logheader + caller + "Disconnected From Database")
