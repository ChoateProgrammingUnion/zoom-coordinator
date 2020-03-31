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

def block_iter(email, datetime_needed=False, weekday=False):
    current_datetime = datetime.now(pytz.timezone('US/Eastern')).replace(second=0, microsecond=0)
    midnight = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)

    if not weekday:
        weekday = current_datetime.strftime("%A")
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

        self.db = dataset.connect(DB_LOC)
        self.courses_database: dataset.table.Table = self.db['courses']
        self.teachers_database: dataset.table.Table = self.db['teachers']

        self.courses_database.create_index(['student_email'])
        self.teachers_database.create_index(['name'])

    def createSchedule(self, email, firstname, lastname, isTeacher):
        if not self.schedules.get(email):
            self.schedules.update({email: Schedule(self.db, self.courses_database, self.teachers_database, email, firstname, lastname, isTeacher)})

    def getSchedule(self, email) -> Schedule:
        return self.schedules[email]


class Schedule():
    """
    Schedule will fetch the student's schedule and pass it back as a dict. 
    Students are identified by their Choate email address.
    """

    def __init__(self, db, courses, teachers, email, firstname, lastname, isTeacher=False):
        self.db = db
        self.courses_database = courses
        self.teachers_database = teachers


        sanitize = lambda name: str(name).replace(' ', '').replace(',', '').replace('.', '').replace('-', '').lower().rstrip()

        self.email = email
        self.firstname = sanitize(firstname)
        self.lastname = sanitize(lastname)
        self.isTeacher = isTeacher

        self.schedule = {'A': None, 'B': None, 'C': None, 'D': None, 'E': None, 'F': None, 'G': None}

    def transactional_upsert(self, table: str, data: dict, key: list) -> bool:
        lock = FileLock("index.db.lock")
        with lock:
            self.db.begin()
            try:
                self.db[str(table)].upsert(dict(copy.deepcopy(data)), list(key))
                self.db.commit()
                return True
            except:
                self.db.rollback()

        return False

    def teacher_database_upsert(self, data):
        while not self.transactional_upsert('teachers', data, ['id']):
            pass

    def course_database_upsert(self, data):
        while not self.transactional_upsert('courses', data, ['id']):
            pass

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

        classes = self.courses_database.find(first_name=self.firstname, last_name=self.lastname)

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
                        self.schedule[b]['meeting_id'] = self.teachers_database.find_one(first_name=self.firstname, last_name=self.lastname)[b + '_id']
            else:
                self.schedule[block] = c
                self.schedule[block]['meeting_id'] = self.teachers_database.find_one(first_name=self.firstname, last_name=self.lastname)[block + '_id']

    def update_schedule(self, course, section, meeting_id):
        if (self.isTeacher):
            classes_to_update = list(self.courses_database.find(course=course, sec=section))

            self.update_teacher_database_block_id(course + " " + str(section), meeting_id)

            self.fetch_schedule_teacher()
        else:
            classes_to_update = list(self.courses_database.find(course=course, sec=section, student_email=self.email))

        log.info(str(len(classes_to_update)) + " entries to update")

        for c in classes_to_update:
            log.info("Updated " + c['student_name'])

            c['meeting_id'] = meeting_id
            self.course_database_upsert(c)

    def update_teacher_database_office_id(self, firstname, lastname, office_id):
        sanitize = lambda name: str(name).replace(' ', '').replace(',', '').replace('.', '').replace('-', '').lower().rstrip()
        firstname = sanitize(firstname)
        lastname = sanitize(lastname)

        t = self.teachers_database.find_one(first_name=firstname, last_name=lastname)

        if t is None:
            log.error("Failed to query teacher database for " + str((firstname, lastname)))

        t['office_id'] = office_id

        self.teacher_database_upsert(t)

    def update_teacher_database_block_id(self, course, id):
        t = self.teachers_database.find_one(first_name=self.firstname, last_name=self.lastname)

        block = ""
        for b in "ABCDEFG":
            if t[b] == course:
                log.info("Updating " + b + " Block")
                block = b
                t[block + "_id"] = str(id)

        if block == "":
            log.info("Class Not Found")
            return

        self.teacher_database_upsert(t)

    # @functools.lru_cache(maxsize=1000)
    def search_teacher(self, teacher_name: str) -> list:
        teacher_name = teacher_name.replace(".", "").replace(",", "").replace("-", "").lower().rstrip()
        matched_teachers = []
        all_teachers = self.teachers_database.find()

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

    # @functools.lru_cache(maxsize=1000)
       # return None
    def search_teacher_exact(self, lastname, firstname, reverse=True):
        all_teachers = self.teachers_database.find()

        sanitize = lambda name: str(name).replace(' ', '').replace(',', '').replace('.', '').replace('-', '').lower().rstrip()

        for teacher in all_teachers:
            if sanitize(lastname) == sanitize(teacher['last_name']) and sanitize(firstname) == sanitize(teacher['first_name']):
                return teacher

        log.info("teacher_search_exact queried " + str([lastname, firstname]) + " and got no result")
