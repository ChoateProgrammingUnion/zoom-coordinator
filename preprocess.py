import csv
import sys
import dataset

DB_LOC = "sqlite:///index.db"

def import_data(filename: str):

    # Connecting to the DB
    db =  dataset.connect(DB_LOC)
    courses = db['courses']

    with open(filename) as f:
        reader = csv.DictReader(f)
        for count, each_row in enumerate(reader):
            print(each_row["Student Name"])
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
