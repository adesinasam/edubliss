import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_events():
    events = frappe.get_all('Event', fields=['name', 'subject', 'starts_on', 'ends_on', 'color', 'all_day'])
    
    # Transforming the data to match FullCalendar's event format
    event_list = []
    for event in events:
        event_list.append({
            'id': event.name,
            'title': event.subject,
            'start': event.starts_on,
            'end': event.ends_on,
            'color': event.color,
            'allDay': event.all_day
        })

    return {'message': event_list}

@frappe.whitelist(allow_guest=True)
def get_event_details(event_id):
    # Fetch the event details based on the event ID (name)
    event = frappe.get_doc("Event", event_id)
    
    # Return relevant event details
    return {
        'id': event.name,
        'title': event.subject,
        'start': event.starts_on,
        'end': event.ends_on,
        'color': event.color,
        "description": event.description,
        "event_category": event.event_category
    }
