from datetime import date

calendar_options = {
    "editable": True,
    "navLinks": True,
    "resources": [],
    "selectable": True,
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridDay,dayGridWeek,dayGridMonth",
    },
    "initialDate": str(date.today()),
    "initialView": "dayGridMonth",
}

custom_css = """
.fc-event-past {
    opacity: 0.8;
}
.fc-event-time {
    font-style: italic;
}
.fc-event-title {
    font-weight: 700;
}
.fc-toolbar-title {
    font-size: 2rem;
}
"""
