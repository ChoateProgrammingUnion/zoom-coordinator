import dataset
from config import DB as DB_LOC

from utils import log

db =  dataset.connect(DB_LOC)

courses: dataset.Table = db['courses']
teachers: dataset.Table = db['teachers']

for c in courses.all():
    entries = courses.find(course=c['course'], sec=c['sec'], student_email=c['student_email'])
    log.info(str(len(list(entries))) + " NEW COURSES")

    if len(list(entries)) == 1:
        log.info("ENTRY LENGTH IS 1")
        continue

    # courses.delete(course=c['course'], sec=c['sec'], student_email=c['student_email'])

    for e in entries:
        if e['teacher_email']:
            log.info("INSERT: " + str(e))
            # courses.insert(e)
        else:
            log.info("EMAIL INVALID: " + str(e))