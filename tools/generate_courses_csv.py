import csv
import sys
import dataset
import secrets

from utils import *
from config import DB as DB_LOC

def import_data(filename: str, output_file: str, teacher_file: str):
    sanitize = lambda name: str(name).replace(' ', '').replace(',', '').replace('.', '').replace('-', '').lower().rstrip()

    # Connecting to the DB
    db =  dataset.connect(DB_LOC)

    hotfixes = {}

    courses: dataset.Table = db['courses']
    teachers: dataset.Table = db['teachers']
    teacher_temp: dataset.Table = db['teacher_temp']

    teacher_temp.delete()

    with open(teacher_file) as teachers:
        reader = csv.DictReader(teachers)
        for count, each_row in enumerate(reader):
            each_row['last_name'] = sanitize(each_row['last_name'])
            each_row['first_name'] = sanitize(each_row['first_name'])
            teacher_temp.insert(each_row)

    teacher_temp.create_index(['last_name', 'first_name'])

    with open(filename) as f:
        with open(output_file, 'w', newline='') as out:
            reader = csv.DictReader(f)
            writer = csv.DictWriter(out, reader.fieldnames + ['teacher_email'])
            for count, each_row in enumerate(reader):
                try:
                    each_row['teacher_email'] = teacher_temp.find_one(last_name=sanitize(each_row['last_name']), first_name=sanitize(each_row['first_name']))['email']
                    log.info("Correct email for " + each_row['last_name'] + ", " + each_row['first_name'])
                except:
                    if sanitize(each_row['last_name']) + sanitize(each_row['first_name']) in hotfixes.keys():
                        each_row['teacher_email'] = hotfixes[sanitize(each_row['last_name']) + sanitize(each_row['first_name'])]
                    else:
                        hotfixes[sanitize(each_row['last_name']) + sanitize(each_row['first_name'])] = input("HOTFIX: Teacher Email For " + each_row['last_name'].rstrip() + ", " + each_row['first_name'].rstrip() + ": ")
                        each_row['teacher_email'] = hotfixes[sanitize(each_row['last_name']) + sanitize(each_row['first_name'])]

                writer.writerow(each_row)


if __name__ == "__main__":
    import_data("data/courses.csv", "data/courses_with_email.csv", "data/faculty_email.csv")
