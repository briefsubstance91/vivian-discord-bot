import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_google_calendar_service():
    """Get authenticated Google Calendar service"""
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use service account for production
            service_account_info = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if service_account_info:
                # For production: use service account
                from google.oauth2 import service_account
                creds = service_account.Credentials.from_service_account_info(
                    json.loads(service_account_info),
                    scopes=SCOPES
                )
            else:
                # For development: use OAuth2 flow
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    print("❌ No credentials found. Please set up Google Calendar API.")
                    return None
        
        # Save the credentials for the next run
        if creds and not service_account_info:
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"❌ Failed to build calendar service: {e}")
        return None

def get_calendar_events(days_ahead=7, calendar_id='primary'):
    """Get events from Google Calendar"""
    service = get_google_calendar_service()
    
    if not service:
        print("📅 Using mock calendar data (no Google Calendar connection)")
        return get_mock_calendar_events()
    
    try:
        # Get date range
        now = datetime.utcnow()
        start_time = now.isoformat() + 'Z'
        end_time = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        print(f"📅 Fetching events for next {days_ahead} days")
        
        # Call the Calendar API
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time,
            timeMax=end_time,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print('No upcoming events found.')
            return []
        
        calendar_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Parse start time
            if 'T' in start:  # It's a datetime
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            else:  # It's a date
                start_dt = datetime.strptime(start, '%Y-%m-%d')
            
            # Calculate duration
            if end and 'T' in end:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                duration = end_dt - start_dt
                duration_str = f"{int(duration.total_seconds() / 60)} min"
            else:
                duration_str = "All day"
            
            calendar_events.append({
                "title": event.get('summary', 'Untitled'),
                "start_time": start_dt,
                "duration": duration_str,
                "description": event.get('description', ''),
                "location": event.get('location', '')
            })
        
        print(f"✅ Found {len(calendar_events)} calendar events")
        return calendar_events
        
    except Exception as e:
        print(f"❌ Error fetching Google Calendar events: {e}")
        return get_mock_calendar_events()

def get_events_for_date(target_date):
    """Get events for a specific date"""
    service = get_google_calendar_service()
    
    if not service:
        return []
    
    try:
        # Set date range for the specific day
        start_time = target_date.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        end_time = (target_date + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        calendar_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            if 'T' in start:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            else:
                start_dt = datetime.strptime(start, '%Y-%m-%d')
            
            calendar_events.append({
                "title": event.get('summary', 'Untitled'),
                "start_time": start_dt,
                "duration": "See details",
                "description": event.get('description', '')
            })
        
        return calendar_events
        
    except Exception as e:
        print(f"❌ Error fetching events for date: {e}")
        return []

def get_mock_calendar_events():
    """Mock calendar data - fallback when no real calendar available"""
    today = datetime.now()
    
    mock_events = [
        {
            "title": "Team Standup",
            "start_time": today.replace(hour=9, minute=30),
            "duration": "30 min",
            "description": "Daily sync with the team",
            "location": "Zoom"
        },
        {
            "title": "Strategy Review", 
            "start_time": today.replace(hour=14, minute=0),
            "duration": "60 min",
            "description": "Q4 planning session",
            "location": "Conference Room A"
        },
        {
            "title": "Client Call - Project Alpha",
            "start_time": today.replace(hour=16, minute=30),
            "duration": "45 min",
            "description": "Progress update",
            "location": "Teams"
        }
    ]
    
    return mock_events

def find_free_time(duration_minutes=60, days_ahead=1):
    """Find free time slots in calendar"""
    events = get_calendar_events(days_ahead=days_ahead)
    
    free_slots = []
    business_hours_start = 9
    business_hours_end = 18
    
    # Process each day
    for day_offset in range(days_ahead):
        current_date = datetime.now() + timedelta(days=day_offset)
        day_start = current_date.replace(hour=business_hours_start, minute=0, second=0)
        day_end = current_date.replace(hour=business_hours_end, minute=0, second=0)
        
        # Get events for this day
        day_events = [e for e in events if e['start_time'].date() == current_date.date()]
        day_events.sort(key=lambda x: x['start_time'])
        
        current_time = day_start
        
        for event in day_events:
            event_start = event['start_time']
            
            # Check gap before event
            if current_time < event_start:
                gap_minutes = (event_start - current_time).total_seconds() / 60
                if gap_minutes >= duration_minutes:
                    free_slots.append({
                        "date": current_date.date(),
                        "start": current_time,
                        "end": event_start,
                        "duration_minutes": int(gap_minutes)
                    })
            
            # Move to end of event (assume 1 hour if duration unknown)
            event_duration = 60  # default
            if event['duration'] != "All day" and "min" in event['duration']:
                event_duration = int(event['duration'].split()[0])
            
            current_time = event_start + timedelta(minutes=event_duration)
        
        # Check time after last event
        if current_time < day_end:
            gap_minutes = (day_end - current_time).total_seconds() / 60
            if gap_minutes >= duration_minutes:
                free_slots.append({
                    "date": current_date.date(),
                    "start": current_time,
                    "end": day_end,
                    "duration_minutes": int(gap_minutes)
                })
    
    return free_slots