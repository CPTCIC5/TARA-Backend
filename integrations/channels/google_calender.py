import os
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from integrations.helpers import (
    get_channel, create_channel, check_credentials, 
    refresh_credentials, credentials_from_db, credentials_to_db, RefreshException
)
from db.models import Integrations

# Google Calendar API scope (full access)
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_service(user_id: int, db: Session):
    """Authenticate and return Google Calendar service using database-backed credentials."""
    credentials_path = os.path.join(os.path.dirname(__file__), "credentials.json")
    
    # Get or create channel for this user
    channel = get_channel(Integrations.CALENDER, user_id, db)
    
    if not channel:
        # First time - create channel
        channel = create_channel(Integrations.CALENDER, user_id, db)
    
    creds = None
    
    # Try to load credentials from database
    if check_credentials(channel):
        try:
            creds = credentials_from_db(channel)
            
            # Check if credentials have all required scopes
            if creds and creds.scopes:
                required_scopes = set(SCOPES)
                actual_scopes = set(creds.scopes)
                if not required_scopes.issubset(actual_scopes):
                    creds = None
        except RefreshException:
            creds = None
    
    # Handle expired or invalid credentials
    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds = refresh_credentials(channel, db)
            except RefreshException:
                creds = None
        else:
            creds = None
    
    # Need new authentication
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
        
        # Store credentials in database
        credentials_to_db(creds, channel, db)

    return build("calendar", "v3", credentials=creds)


def list_events(service, calendar_id="primary", max_results=10):
    """List upcoming events."""
    now = datetime.utcnow().isoformat() + "Z"
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
        print("No upcoming events found.")
        return []

    print("Upcoming events:")
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        print(f"- {start} | {event.get('summary', '(no title)')}")
    return events


def create_event(service, calendar_id="primary"):
    """Create a sample event 10 mins from now for 30 mins."""
    start_time = datetime.now(timezone.utc) + timedelta(minutes=10)
    end_time = start_time + timedelta(minutes=30)

    event = {
        "summary": "Python API Demo Event",
        "description": "This event was created using Python + Google Calendar API",
        "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
    }

    event = service.events().insert(calendarId=calendar_id, body=event).execute()
    print("Event created:")
    print(json.dumps({"id": event["id"], "htmlLink": event["htmlLink"]}, indent=2))
    return event


def update_event(service, event_id, calendar_id="primary"):
    """Update the event summary and description."""
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

    event["summary"] = "Updated Event Title"
    event["description"] = "Event updated using Python script."

    updated_event = (
        service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
    )
    print("Event updated:")
    print(json.dumps({"id": updated_event["id"], "htmlLink": updated_event["htmlLink"]}, indent=2))
    return updated_event


def delete_event(service, event_id, calendar_id="primary"):
    """Delete an event by ID."""
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    print(f"Deleted event: {event_id}")


def main(user_id: int = 1, db: Session = None):
    """Example usage of Google Calendar functions."""
    if db is None:
        from db.models import SessionLocal
        db = SessionLocal()
    
    try:
        service = get_service(user_id, db)

        # 1. List upcoming events
        list_events(service)

        # 2. Create a new event
        created = create_event(service)

        # 3. Update the same event
        update_event(service, created["id"])

        # 4. Delete the event (cleanup)
        delete_event(service, created["id"])

    except HttpError as error:
        print("An error occurred:", error)
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    main()