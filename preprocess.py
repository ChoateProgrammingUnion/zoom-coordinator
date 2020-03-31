import csv
import sys
import dataset

from utils import *
from config import DB as DB_LOC

def import_data(filename: str):
    sanitize = lambda name: str(name).replace(' ', '').replace(',', '').replace('.', '').replace('-', '').lower().rstrip()

    # Connecting to the DB
    db =  dataset.connect(DB_LOC)
    courses = db['courses']
    teachers = db['teachers']

    with open(filename) as f:
        reader = csv.DictReader(f)
        for count, each_row in enumerate(reader):
            each_row['meeting_id'] = 0
            each_row['first_name'] = sanitize(each_row['first_name'])
            each_row['last_name'] = sanitize(each_row['last_name'])
            each_row['teacher_name'] = each_row['last_name'] + ' ' + each_row['first_name']
            courses.upsert(dict(each_row), ["id"]) #upserting info

            teacher = teachers.find_one(name=each_row['teacher_name'])

            block = each_row['block']
            if block == "":
                continue

            if teacher is None:
                if (len(block) > 1):
                    teacher = {"name":each_row['teacher_name'], 'first_name': each_row['first_name'], 'last_name': each_row['last_name'], 'office_id':0}

                    block = block.replace("Fri", "fri")

                    log.info(block)

                    for b in "ABCDEFG":
                        if b in block:
                            log.info(" " + b)
                            teacher[b] = each_row['course'] + " " + each_row['sec']
                            teacher[b + "_id"] = 0
                else:
                    teacher = {"name":each_row['teacher_name'], 'first_name': each_row['first_name'], 'last_name': each_row['last_name'], 'office_id':0, str(block):each_row['course'] + " " + each_row['sec'], str(block) + "_id":0}

                teachers.upsert(teacher, ["id"])
            else:
                if (len(block) > 1):
                    block = block.replace("Fri", "fri")

                    log.info(block)

                    for b in "ABCDEFG":
                        if b in block:
                            log.info(" " + b)
                            teacher[b] = each_row['course'] + " " + each_row['sec']
                            teacher[b + "_id"] = 0
                else:
                    teacher[block] = each_row['course'] + " " + each_row['sec']
                    teacher[block + "_id"] = 0

                teachers.upsert(teacher, ["id"])



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
