import streamlit as st
from streamlit_calendar import calendar
from config import calendar_options, custom_css
from utils import update_event_colors, SQLConnection
from datetime import datetime, date, timedelta

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

st.set_page_config(page_title="Study Calendar", page_icon="📆")

PERIODS = ['D0', 'D3', 'D9', 'D30', 'D45', 'D90', 'D180']

if st.session_state.get("events") is None:
    st.session_state.conn = SQLConnection()
    st.session_state.conn.get_events()
    st.session_state["events"] = update_event_colors(st.session_state.conn.get_dataset())

state = calendar(
    events=update_event_colors(st.session_state.get("events")),
    options=calendar_options,
    custom_css=custom_css,
    key="daygrid",
)

# Where all the events are noted
if state.get("eventsSet") is not None:
    st.session_state["events"] = update_event_colors(state["eventsSet"]["events"])

if state.get("eventClick") or state.get("dateClick"):
    if state.get("eventClick"):
        event = state["eventClick"]["event"]
        with st.form(key="edit_event_form"):
            event_title = st.text_input("Event Title", value=event["title"], disabled = True)
            event_subtitle = st.text_input("Period", value=event["extendedProps"]["subtitle"], disabled = True)
            event_start = st.text_input("Start Date", value=event["start"])
            event_end = str((datetime.strptime(event_start, "%Y-%m-%d") + timedelta(days=1)).date())
            event_done = st.checkbox("done", value=event['extendedProps']["done"])
            submit_button = st.form_submit_button("Save Changes")

            if submit_button:
                for e in st.session_state["events"]:
                    if (e["title"] == event["title"]) and (e["extendedProps"]["subtitle"] == event["extendedProps"]["subtitle"]):  # Replace event based on title
                        e["title"] = event_title
                        e["extendedProps"]["subtitle"] = event_subtitle
                        e["start"] = event_start
                        e["end"] = event_end
                        e["extendedProps"]["done"] = event_done
                        break
                
                # Re-render the calendar with the updated events
                st.session_state["events"] = update_event_colors(st.session_state["events"])
                st.session_state.conn.online_table_update(st.session_state["events"])
                st.rerun()
                
    elif state.get("dateClick"):
        selected_date = state["dateClick"]
        with st.form(key="create_event_form"):

            start_datetime = datetime.strptime(selected_date['date'], "%Y-%m-%dT%H:%M:%S.%fZ").date()
            
            new_event_title = st.text_input("Event Title")
            new_event_start = st.text_input("Start Time", disabled = True, value=start_datetime)
            submit_button = st.form_submit_button("Create Event")

            if submit_button:
                for period in PERIODS:
                    subtitle_start_datetime = (start_datetime + timedelta(days=int(period.lstrip('D'))))
                    subtitle_end_datetime = (subtitle_start_datetime + timedelta(days=1))
                    new_event = {
                        "title": new_event_title,
                        "backgroundColor": "#FFFF00",
                        "borderColor": "#FFFF00",
                        "start": str(subtitle_start_datetime),
                        "end": str(subtitle_end_datetime),
                        "extendedProps": {
                            "subtitle": period,
                            "done": False,
                        }
                    }
                    st.session_state["events"].append(new_event)
                st.session_state["events"] = update_event_colors(st.session_state["events"])
                st.session_state.conn.online_table_update(st.session_state["events"])
                st.rerun()
                

               
# Remocao end date - ok
# colocar um base fora
# realizar o refresh quando dar o update - ok
# campo de remarcacao de eventos
# When a date or an event is clicked, state will change and will appear at the bottom of the page