import csv
import sys

def import_data(filename: str):
    with open(filename) as f:
        reader = csv.DictReader(f)
        for each_row in reader:
            print(each_row)

def upsert_db(db, email=email):
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
