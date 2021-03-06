## Zoom Coordinator

This project is heeding the call/challenge by Andrew Speyer, director of Choate ITS, to make a Zoom link coordinator for each student across classes.

Collaboration is welcome!

## Deployment
Docker (requires Docker):
- clone to home folder (~/)
- place `index.db` inside git repo
```bash
bash deploy
```

Native with gunicorn (requires Python deps):
```bash
gunicorn app:app -w 4 --bind :8000
```


Native (for development, requires Python deps):
```bash
flask run
```

## Python Deps
- Flask
- Gunicorn (for production)
- Flask-Dance
- validators
- fuzzysearch
- dataset
- pytz


## Layout
[`app.py`](/app.py) is the main app

[`preprocess.py`](/preprocess.py) imports the course list in `data/course.csv` and puts it into a SQL database

[`deploy`](/deploy) docker deployment script

[`serve`](/serve) docker serve script (not used rn)

[`schedule.py`](/schedule.py) contains schedule class that [`app.py`](/app.py) consumes

[`auth.py`](/auth.py) contains the authentication code [`app.py`](/app.py) consumes to manage tokens and user sessions


## TODO
None, features are now frozen for production (mostly).

