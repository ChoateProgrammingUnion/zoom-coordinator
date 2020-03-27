Each meeting will be documented so people in different timezone/otherwise unable to attend will be able to catch-up.

## March 26th Meeting notes (with ITS)

### Pre-meeting
#### Questions:
- How do you want authentication to work? 
- Will ITS be adding Zoom links or will teachers do it?
- How do we get access to their schedule (if teachers do it)?
- How are you generating the PDFs?
- Can we reuse your ChoateSIS css verbatim? (plagiarism)

#### Plan (frameworks):
Backend: flask + sqlite

Frontend: html + css (vanilla, maybe some frameworks)

## Meeting overview
- we're given more or less free rein in terms of UI/UX
- they want us to be able to export to SQL/csv/excel eventually (using dataset/datafreeze will make this easy)
- we're allowed to use their CSS
- Ryan is in charge of frontend, seeing as she has good experience with SASS
- teachers will not be able to enter in their zoom meeting IDs in time, so we also need to allow students to overwrite/do it themselves

Things we still need:
- the list of students and the class they're attending (as well as which teacher is teaching)
