from icalendar import Calendar, Event
from app import check_teacher
from schedule import block_iter, ScheduleManager
import pytz
import datetime

CLASSDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

def make_calendar(email, name):
    ScheduleManager().createSchedule(email, name, check_teacher(email))
    user_schedule = ScheduleManager().getSchedule(email)
    user_schedule.fetch_schedule()
    
    today_offset = datetime.date.today().weekday()
    this_monday = datetime.date.today() - datetime.timedelta(days=-today_offset)
    print(this_monday)

    print(this_monday.day)
    # Taken from documentation
    cal = Calendar()
    cal['summary'] = 'Choate Zoom Coordinator Schedule'
    for count, each_day in enumerate(CLASSDAYS):
        for block, start_time in block_iter(email, datetime_needed=True, weekday=each_day):
            start_time = start_time.replace(day=this_monday.day) + datetime.timedelta(days=count)
            
            block_data = user_schedule.schedule[block]
            if block_data:
                print(block_data)

                event = Event()
                # event['summary'] = block + ' block class'
                event['LOCATION'] = "https://zoom.us/j/" + str(block_data.get('meeting_id'))
                event['summary'] = block_data.get('course_name').title()
                event['DESCRIPTION'] = "Zoom link: https://zoom.us/j/" + str(block_data.get('meeting_id')) + "\nMeeting ID: " + str(block_data.get('meeting_id'))
                event.add('dtstart', start_time)
                event.add('dtend', start_time + datetime.timedelta(minutes=50))
                cal.add_component(event)
    return cal

