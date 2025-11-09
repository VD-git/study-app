from datetime import datetime, date
from typing import List
import streamlit as st
from sqlalchemy import create_engine, text
import os

def update_event_colors(events: List[dict]) -> List[dict]:
    today = date.today()
    for ev in events:
        done = ev.get("extendedProps", {}).get("done", False)
        end_date = datetime.strptime(ev["end"], '%Y-%m-%d').date()

        if done:
            color = '#00FF00'  # Green
        elif today >= end_date:
            color = '#FF0000'  # Red
        else:
            color = '#FFFF00'  # Yellow

        ev["backgroundColor"] = color
        ev["borderColor"] = color

    return events

def diff_events(before, after):

    def key(e):
        return (e["title"], e["extendedProps"]["subtitle"])

    before_dict = {key(e): e for e in before}
    after_dict = {key(e): e for e in after}

    before_keys = set(before_dict.keys())
    after_keys = set(after_dict.keys())

    # Dictionary I can just subtract them in order to reach which were added or removed
    to_add = [after_dict[k] for k in after_keys - before_keys]
    to_remove = [before_dict[k] for k in before_keys - after_keys]

    # Symbol & is the same of intersection for dictionary | union
    common_keys = before_keys & after_keys
    to_update = []
    for k in common_keys:
        b = before_dict[k]
        a = after_dict[k]

        if (
            b.get("start") != a.get("start")
            or b.get("end") != a.get("end")
            or b.get("backgroundColor") != a.get("backgroundColor")
            or b.get("borderColor") != a.get("borderColor")
            or b["extendedProps"].get("done") != a["extendedProps"].get("done")
        ):
            to_update.append(a)

    return to_add, to_remove, to_update

def convert_to_sql(events: List[dict]) -> List[dict]:
    events_clean = []
    for event in events:
        events_clean.append(
            {
                "title": event["title"],
                "subtitle": event["extendedProps"]["subtitle"],
                "color": event["backgroundColor"],
                "start": event["start"],
                "end": event["end"],
                "done": event["extendedProps"]["done"]
            }
        )
    return events_clean

class SQLConnection:
    def __init__(self):
        self.POSTGRES_USER = os.getenv("DB_USER") or st.secrets["postgres"]["user"]
        self.POSTGRES_PASSWORD = os.getenv('DB_PASSWORD') or st.secrets['postgres']['password']
        self.POSTGRES_DB = os.getenv('DB_NAME') or st.secrets['postgres']['dbname']
        self.POSTGRES_HOST = os.getenv('DB_HOST') or st.secrets['postgres']['host']
        self.POSTGRES_PORT = os.getenv('DB_PORT') or st.secrets['postgres']['port']
        self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        self.engine = create_engine(self.DATABASE_URL)
        self.create_table_sql_query = text("""
            CREATE TABLE IF NOT EXISTS events (
                "id" SERIAL PRIMARY KEY,
                "title" VARCHAR(255) NOT NULL,
                "subtitle" VARCHAR(50) NOT NULL,
                "color" VARCHAR(55) NOT NULL,
                "start" DATE NOT NULL,
                "end" DATE NOT NULL,
                "done" BOOLEAN DEFAULT FALSE
            );
        """)
        self.select_table_sql_query = text("""
            SELECT * FROM events;
        """)
        self.drop_table_sql_query = text("""
            DROP TABLE events;
        """)
        self.insert_table_sql_query = text("""
            INSERT INTO events (title, subtitle, color, start, "end", done)
            VALUES (:title, :subtitle, :color, :start, :end, :done);
        """)
        self.removal_table_sql_query = text("""
            DELETE FROM events
            WHERE title = :title AND subtitle = :subtitle;
        """)

    def get_events(self):
        with self.engine.connect() as conn:
            conn.execute(self.create_table_sql_query)
            conn.commit()

    def drop_events(self):
        with self.engine.connect() as conn:
            conn.execute(self.drop_table_sql_query)
            conn.commit()

    def get_dataset(self):
        with self.engine.connect() as conn:
            result = conn.execute(self.select_table_sql_query)
            rows = result.fetchall()

            events = []
            for row in rows:
                events.append({
                    "title": row[1],
                    "backgroundColor": row[3],
                    "borderColor": row[3],
                    "start": row[4].isoformat(),
                    "end": row[5].isoformat(),
                    "extendedProps": {
                        "subtitle": row[2],
                        "done": row[6]
                    }
                })
            return events

    def online_table_update(self, state):
        to_add, to_remove, to_update = diff_events(self.get_dataset(), state)

        for item in convert_to_sql(to_add):
            self.insert_event(item)

        for item in convert_to_sql(to_remove):
            self.removal_event(item)

        for item in convert_to_sql(to_update):
            self.update_event(item['title'], item['subtitle'], item)


    def insert_event(self, event):
        with self.engine.connect() as conn:
            conn.execute(
                self.insert_table_sql_query,
                {
                    "title": event["title"],
                    "subtitle": event["subtitle"],
                    "color": event["color"],
                    "start": event["start"],
                    "end": event["end"],
                    "done": event.get("done", False)
                }
            )
            conn.commit()

    def removal_event(self, event):
        with self.engine.connect() as conn:
            conn.execute(
                self.removal_table_sql_query,
                {
                    "title": event["title"],
                    "subtitle": event["subtitle"]
                }
            )
            conn.commit()

    def update_event(self, old_title, old_subtitle, updated_event):
        self.update_table_sql_query = text(f"""
        UPDATE events
        SET title = '{updated_event["title"]}',
            subtitle = '{updated_event["subtitle"]}',
            color = '{updated_event["color"]}',
            start = '{updated_event["start"]}',
            "end" = '{updated_event["end"]}',
            done = {updated_event["done"]}
        WHERE title = '{old_title}'
          AND subtitle = '{old_subtitle}';
        """)
        
        with self.engine.connect() as conn:
            conn.execute(self.update_table_sql_query)
            conn.commit()

            

            