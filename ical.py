from icalendar import Calendar, Event
from app import check_teacher
from schedule import block_iter_datetime_today, ScheduleManager, CLASS_DURATION, END_DATE
import pytz
import datetime

from utils import *


def make_calendar(email, firstname, lastname):
    """
    Returns an ical of the user's schedule
    """
    # ScheduleManager().createSchedule(email, firstname, lastname, check_teacher(email))
    user_schedule = ScheduleManager().getSchedule(email, firstname, lastname, check_teacher(email))
    user_schedule.init_db_connection()
    user_schedule.fetch_schedule()
    
    today_offset = datetime.date.today().weekday()
    event_date = datetime.date.today() - datetime.timedelta(days=today_offset)

    # Taken from documentation
    cal = Calendar()
    cal['summary'] = 'Choate Zoom Coordinator Schedule'

    while event_date <= END_DATE:
        event_date += datetime.timedelta(days=1)

        for block, start_time in block_iter_datetime_today(event_date):
            block_data = user_schedule.schedule[block]
            if block_data:
                event = Event()
                # event['summary'] = block + ' block class'
                event['LOCATION'] = "https://zoom.us/j/" + str(block_data.get('meeting_id'))
                event['summary'] = block_data.get('course_name').title()
                event['DESCRIPTION'] = "Zoom link: https://zoom.us/j/" + str(block_data.get('meeting_id')) + "\nMeeting ID: " + str(block_data.get('meeting_id'))
                # event.add('rrule', {'freq': 'weekly', 'count': 10})

                event.add('dtstart', start_time)
                event.add('dtend', start_time + CLASS_DURATION)

                cal.add_component(event)

    user_schedule.end_db_connection()
    return cal

