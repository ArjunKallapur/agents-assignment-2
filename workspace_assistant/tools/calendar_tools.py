"""
Option A: Calendar Assistant Tools

Implement at least 3 tools for Google Calendar operations.
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "America/Los_Angeles"
WEEKDAY_NAMES = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _error(message: str) -> dict:
    return {"status": "error", "message": message}


def _parse_time_of_day(value: str) -> Optional[tuple[int, int]]:
    text = value.strip().lower().replace(".", "")
    minute = 0

    if text.endswith("am") or text.endswith("pm"):
        meridiem = text[-2:]
        time_text = text[:-2].strip()
    else:
        meridiem = ""
        time_text = text

    if ":" in time_text:
        hour_text, minute_text = time_text.split(":", 1)
        if not hour_text.isdigit() or not minute_text.isdigit():
            return None
        hour = int(hour_text)
        minute = int(minute_text)
    elif time_text.isdigit():
        hour = int(time_text)
    else:
        return None

    if minute < 0 or minute > 59:
        return None

    if meridiem:
        if hour < 1 or hour > 12:
            return None
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
    elif hour < 0 or hour > 23:
        return None

    return hour, minute


def _parse_datetime(value: str) -> datetime:
    """Parse ISO datetimes plus a small, explicit natural-language fallback."""
    if not value or not value.strip():
        raise ValueError("Please provide a date and time.")

    tz = ZoneInfo(DEFAULT_TIMEZONE)
    text = value.strip()

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tz)
        return parsed
    except ValueError:
        pass

    lowered = " ".join(text.lower().replace(" at ", " ").split())
    parts = lowered.split()
    today = datetime.now(tz).replace(second=0, microsecond=0)

    if len(parts) == 2 and parts[0] in {"today", "tomorrow"}:
        parsed_time = _parse_time_of_day(parts[1])
        if not parsed_time:
            raise ValueError(f"Could not understand the time in '{value}'.")
        days = 1 if parts[0] == "tomorrow" else 0
        hour, minute = parsed_time
        return (today + timedelta(days=days)).replace(hour=hour, minute=minute)

    if len(parts) == 3 and parts[0] == "next" and parts[1] in WEEKDAY_NAMES:
        parsed_time = _parse_time_of_day(parts[2])
        if not parsed_time:
            raise ValueError(f"Could not understand the time in '{value}'.")
        current_weekday = today.weekday()
        target_weekday = WEEKDAY_NAMES[parts[1]]
        days_until = (target_weekday - current_weekday) % 7
        if days_until == 0:
            days_until = 7
        hour, minute = parsed_time
        return (today + timedelta(days=days_until)).replace(hour=hour, minute=minute)

    raise ValueError(
        "Please use an ISO datetime like '2026-07-06T15:00:00' or a simple "
        "phrase like 'today 3pm', 'tomorrow 10am', or 'next monday 2pm'."
    )


def _to_rfc3339(value: str) -> str:
    return _parse_datetime(value).isoformat()


def _event_summary(event: dict[str, Any]) -> dict[str, Any]:
    start = event.get("start", {})
    end = event.get("end", {})
    return {
        "id": event.get("id"),
        "summary": event.get("summary", "(No title)"),
        "start": start.get("dateTime", start.get("date")),
        "end": end.get("dateTime", end.get("date")),
        "location": event.get("location", ""),
        "html_link": event.get("htmlLink", ""),
    }


def _friendly_google_error(error: Exception) -> str:
    if error.__class__.__name__ == "HttpError":
        reason = getattr(error, "reason", str(error))
        return f"Google Calendar API error: {reason}"
    if isinstance(error, FileNotFoundError):
        return str(error)
    return f"Unexpected calendar error: {error}"


def _get_calendar_service():
    from tools.auth import get_calendar_service

    return get_calendar_service()


def list_upcoming_events(start_time: str = "", end_time: str = "", max_results: int = 10) -> dict:
    """List upcoming Google Calendar events in a time range.

    Use this when the user asks what is on their calendar, what meetings are
    coming up, or what they have scheduled during a specific range.

    Args:
        start_time: Start of the range as an ISO datetime or simple phrase.
            If blank, starts from now in America/Los_Angeles.
        end_time: End of the range as an ISO datetime or simple phrase.
            If blank, Google Calendar returns the next upcoming events.
        max_results: Maximum number of events to return.

    Returns:
        A dict with status, events, and count on success, or message on error.
    """
    try:
        tz = ZoneInfo(DEFAULT_TIMEZONE)
        time_min = _to_rfc3339(start_time) if start_time else datetime.now(tz).isoformat()
        params = {
            "calendarId": "primary",
            "timeMin": time_min,
            "maxResults": max(1, min(max_results, 50)),
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if end_time:
            params["timeMax"] = _to_rfc3339(end_time)

        service = _get_calendar_service()
        result = service.events().list(**params).execute()
        events = [_event_summary(event) for event in result.get("items", [])]
        return {"status": "success", "events": events, "count": len(events)}
    except ValueError as e:
        return _error(str(e))
    except Exception as e:
        return _error(_friendly_google_error(e))


def find_available_slots(
    start_time: str,
    end_time: str,
    duration_minutes: int = 30,
    attendee_emails: Optional[list[str]] = None,
) -> dict:
    """Find available meeting slots on the primary calendar and attendees' calendars.

    Use this when the user asks for free time, open slots, or availability for
    themselves or a group of attendees.

    Args:
        start_time: Search window start as an ISO datetime or simple phrase.
        end_time: Search window end as an ISO datetime or simple phrase.
        duration_minutes: Required meeting length in minutes.
        attendee_emails: Optional attendee email addresses to include in free/busy.

    Returns:
        A dict with status, available_slots, and count on success, or message on error.
    """
    try:
        if duration_minutes <= 0:
            return _error("Duration must be a positive number of minutes.")

        start_dt = _parse_datetime(start_time)
        end_dt = _parse_datetime(end_time)
        if end_dt <= start_dt:
            return _error("End time must be after start time.")

        calendars = [{"id": "primary"}]
        for email in attendee_emails or []:
            calendars.append({"id": email})

        service = _get_calendar_service()
        body = {
            "timeMin": start_dt.isoformat(),
            "timeMax": end_dt.isoformat(),
            "items": calendars,
        }
        freebusy = service.freebusy().query(body=body).execute()

        busy_blocks = []
        for calendar in freebusy.get("calendars", {}).values():
            for block in calendar.get("busy", []):
                busy_blocks.append(
                    (_parse_datetime(block["start"]), _parse_datetime(block["end"]))
                )
        busy_blocks.sort(key=lambda item: item[0])

        slots = []
        cursor = start_dt
        minimum_delta = timedelta(minutes=duration_minutes)
        for busy_start, busy_end in busy_blocks:
            if busy_end <= cursor:
                continue
            if busy_start > cursor and busy_start - cursor >= minimum_delta:
                slots.append({"start": cursor.isoformat(), "end": busy_start.isoformat()})
            if busy_end > cursor:
                cursor = busy_end

        if end_dt - cursor >= minimum_delta:
            slots.append({"start": cursor.isoformat(), "end": end_dt.isoformat()})

        return {"status": "success", "available_slots": slots, "count": len(slots)}
    except ValueError as e:
        return _error(str(e))
    except Exception as e:
        return _error(_friendly_google_error(e))


def create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    attendee_emails: Optional[list[str]] = None,
) -> dict:
    """Create a Google Calendar meeting on the primary calendar.

    Use this only after the user has confirmed they want to schedule the event.
    The agent should collect a title, start time, end time or duration, and any
    attendee emails before calling this tool.

    Args:
        summary: Meeting title.
        start_time: Meeting start as an ISO datetime or simple phrase.
        end_time: Meeting end as an ISO datetime or simple phrase.
        description: Optional meeting description.
        location: Optional meeting location.
        attendee_emails: Optional attendee email addresses to invite.

    Returns:
        A dict with status and event details on success, or message on error.
    """
    try:
        if not summary.strip():
            return _error("Event title is required.")

        start_dt = _parse_datetime(start_time)
        end_dt = _parse_datetime(end_time)
        if end_dt <= start_dt:
            return _error("End time must be after start time.")

        event_body = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": DEFAULT_TIMEZONE},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": DEFAULT_TIMEZONE},
            "attendees": [{"email": email} for email in attendee_emails or []],
        }

        service = _get_calendar_service()
        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            sendUpdates="all" if attendee_emails else "none",
        ).execute()
        return {"status": "success", "event": _event_summary(event)}
    except ValueError as e:
        return _error(str(e))
    except Exception as e:
        return _error(_friendly_google_error(e))


def check_conflicts(
    start_time: str,
    end_time: str,
    attendee_emails: Optional[list[str]] = None,
) -> dict:
    """Check whether a proposed meeting time conflicts with existing calendars.

    Use this when the user asks if a time is free, whether a meeting conflicts,
    or before suggesting that a meeting time is safe.

    Args:
        start_time: Proposed meeting start as an ISO datetime or simple phrase.
        end_time: Proposed meeting end as an ISO datetime or simple phrase.
        attendee_emails: Optional attendee email addresses to include in free/busy.

    Returns:
        A dict with status, has_conflicts, and conflicts on success, or message on error.
    """
    try:
        start_dt = _parse_datetime(start_time)
        end_dt = _parse_datetime(end_time)
        if end_dt <= start_dt:
            return _error("End time must be after start time.")

        calendars = [{"id": "primary"}]
        for email in attendee_emails or []:
            calendars.append({"id": email})

        service = _get_calendar_service()
        body = {
            "timeMin": start_dt.isoformat(),
            "timeMax": end_dt.isoformat(),
            "items": calendars,
        }
        freebusy = service.freebusy().query(body=body).execute()

        conflicts = []
        for calendar_id, calendar in freebusy.get("calendars", {}).items():
            for block in calendar.get("busy", []):
                conflicts.append(
                    {
                        "calendar": calendar_id,
                        "start": block.get("start"),
                        "end": block.get("end"),
                    }
                )

        return {
            "status": "success",
            "has_conflicts": bool(conflicts),
            "conflicts": conflicts,
            "count": len(conflicts),
        }
    except ValueError as e:
        return _error(str(e))
    except Exception as e:
        return _error(_friendly_google_error(e))


def reschedule_event(event_id: str, new_start_time: str, new_end_time: str) -> dict:
    """Move an existing Google Calendar event to a new time.

    Use this only after the user has confirmed they want to reschedule a known
    event. If the user has not provided an event ID, list events first and ask
    them to identify the event.

    Args:
        event_id: Google Calendar event ID to move.
        new_start_time: New event start as an ISO datetime or simple phrase.
        new_end_time: New event end as an ISO datetime or simple phrase.

    Returns:
        A dict with status and updated event details on success, or message on error.
    """
    try:
        if not event_id.strip():
            return _error("Event ID is required to reschedule an event.")

        start_dt = _parse_datetime(new_start_time)
        end_dt = _parse_datetime(new_end_time)
        if end_dt <= start_dt:
            return _error("End time must be after start time.")

        service = _get_calendar_service()
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
        event["start"] = {"dateTime": start_dt.isoformat(), "timeZone": DEFAULT_TIMEZONE}
        event["end"] = {"dateTime": end_dt.isoformat(), "timeZone": DEFAULT_TIMEZONE}

        updated = service.events().update(
            calendarId="primary",
            eventId=event_id,
            body=event,
            sendUpdates="all",
        ).execute()
        return {"status": "success", "event": _event_summary(updated)}
    except ValueError as e:
        return _error(str(e))
    except Exception as e:
        return _error(_friendly_google_error(e))


calendar_tools = [
    list_upcoming_events,
    find_available_slots,
    create_event,
    check_conflicts,
    reschedule_event,
]
