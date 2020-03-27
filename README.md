## Zoom Coordinator

This project is heeding the call/challenge by Andrew Speyer, director of Choate ITS, to make a Zoom link coordinator for each student across classes.

Collaboration is welcome!

## Deployment
Docker (requires Docker):
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

## Layout
[`app.py`](/app.py) is the main app

[`preprocess.py`](/preprocess.py) imports the course list in `data/course.csv` and puts it into a SQL database

[`deploy`](/preprocess.py) docker deployment script

[`schedule.py`](/preprocess.py) contains schedule class that [`app.py`](/app.py) consumes


## TODO
Backend:
- [x] authentication (talk to Speyer)
- [x] checking if authorized (student and teacher view)
- [ ] keeping track of people/classes (db)
- [ ] admin edits (admin view) (optional)

Frontend:
- [ ] student view
- [ ] teacher view
- [ ] login page
- [ ] admin view (optional)
