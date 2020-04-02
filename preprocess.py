import csv
import sys
import dataset
import secrets

from utils import *
from config import DB as DB_LOC

def import_data(filename: str):
    sanitize = lambda name: str(name).replace(' ', '').replace(',', '').replace('.', '').replace('-', '').lower().rstrip()

    # Connecting to the DB
    db =  dataset.connect(DB_LOC, engine_kwargs={‘pool_recycle’: 3600})
    courses = db['courses']
    teachers = db['teachers']

    with open(filename) as f:
        reader = csv.DictReader(f)
        for count, each_row in enumerate(reader):
            c = courses.find_one(course=each_row['course'], sec=each_row['sec'], student_email=each_row['student_email'])

            if c:
                each_row['id'] = c['id']

            if c and c['meeting_id'] != 0:
                log.info("Preserved Meeting id " + str(c['meeting_id']))
                each_row['meeting_id'] = c['meeting_id']
            else:
                each_row['meeting_id'] = 0

            # log.info(each_row)

            each_row['teacher_name'] = each_row['first_name'].rstrip().title() + ' ' + each_row['last_name'].rstrip().title()
            each_row['first_name'] = sanitize(each_row['first_name'])
            each_row['last_name'] = sanitize(each_row['last_name'])

            teacher = teachers.find_one(name=each_row['teacher_name'])

            block = each_row['block']
            if block == "":
                continue

            if teacher is None:
                if (len(block) > 1):
                    teacher = {"name":each_row['teacher_name'],
                               'first_name': each_row['first_name'],
                               'last_name': each_row['last_name'],
                               'email': each_row['teacher_email'],
                               'office_id':0}

                    block = block.replace("Fri", "fri")

                    for b in "ABCDEFG":
                        if b in block:
                            teacher[b] = each_row['course'] + " " + each_row['sec']
                            teacher[b + "_id"] = 0
                else:
                    teacher = {"name":each_row['teacher_name'],
                               'first_name': each_row['first_name'],
                               'last_name': each_row['last_name'],
                               'email': each_row['teacher_email'],
                               'office_id':0,
                               str(block):each_row['course'] + " " + each_row['sec'], str(block) + "_id":0}

                teachers.upsert(teacher, ["id"])
            else:
                if not teacher.get("email"):
                    teacher['email'] = each_row["teacher_email"]

                if (len(block) > 1):
                    block = block.replace("Fri", "fri")

                    for b in "ABCDEFG":
                        if b in block:
                            teacher[b] = each_row['course'] + " " + each_row['sec']

                            if not teacher.get(b + "_id"):
                                teacher[b + "_id"] = 0
                            else:
                                log.info("Teacher id " + str(teacher.get(b + "_id")) + " preserved")
                else:
                    teacher[block] = each_row['course'] + " " + each_row['sec']

                    if not teacher.get(block + "_id"):
                        teacher[block + "_id"] = 0
                    else:
                        log.info("Teacher id " + str(teacher.get(block + "_id")) + " preserved")

                teachers.upsert(teacher, ["id"])

            courses.upsert(dict(each_row), ["id"]) #upserting info



def upsert_db(db, email):
    pass

if __name__ == "__main__":
    """
    Usage:
        python3 preprocess.py data/courses.csv
        Final argument optional
    """
    if len(sys.argv) == 2:
        import_data(sys.argv[1])
    else:
        import_data("data/courses.csv")
