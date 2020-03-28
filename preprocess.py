import csv
import sys
import dataset

DB_LOC = "sqlite:///index.db"



def import_data(filename: str):

    # Connecting to the DB
    db =  dataset.connect(DB_LOC)
    courses = db['courses']
    teachers = db['teachers']

    with open(filename) as f:
        reader = csv.DictReader(f)
        for count, each_row in enumerate(reader):
            each_row['meeting_id'] = 0
            courses.upsert(dict(each_row), ["id"]) #upserting info

            teacher = teachers.find_one(name=each_row['teacher_name'])

            block = each_row['block']
            if block == "":
                continue

            if teacher is None:
                if (len(block) > 1):
                    teacher = {"name":each_row['teacher_name'], 'office_id':0, "A":each_row['course']}

                    block = block.replace("Fri", "fri")

                    print(block)

                    for b in "ABCDEFG":
                        if b in block:
                            print(" " + b)
                            teacher[b] = each_row['course'] + " " + each_row['sec']
                else:
                    teacher = {"name":each_row['teacher_name'], 'office_id':0, str(block):each_row['course'] + " " + each_row['sec']}

                teachers.insert(teacher)
            else:
                if (len(block) > 1):
                    block = block.replace("Fri", "fri")

                    print(block)

                    for b in "ABCDEFG":
                        if b in block:
                            print(" " + b)
                            teacher[b] = each_row['course'] + " " + each_row['sec']
                else:
                    teacher[block] = each_row['course'] + " " + each_row['sec']

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
