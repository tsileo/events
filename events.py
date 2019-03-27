import uuid
import sys
import re
from pathlib import Path
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Optional

import caldav
import vobject
import yaml
from dateutil.tz import tzlocal
from dateutil.parser import parse

tz = tzlocal()
now = datetime.now().astimezone(tz)

DATE_FMT = "%a, %b %d @ %H:%M"
duration_regex = re.compile(r'((?P<hours>-?\d+?)h)?((?P<minutes>-?\d+?)m)?')


def parse_duration(s: str) -> timedelta:
    parts = duration_regex.match(s)
    if not parts:
        return
    parts = parts.groupdict()
    print(parts)
    time_params = {}
    for (name, param) in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)


RED = "\033[1;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[;33m"
RESET = "\033[0;0m"


def red(text: str) -> str:
    return RED + text + RESET


def yellow(text: str) -> str:
    return YELLOW + text + RESET


def green(text: str) -> str:
    return GREEN + text + RESET


def _cal(url: str) -> Any:
    client = caldav.DAVClient(url)
    principal = client.principal()
    calendars = principal.calendars()
    cal = calendars[0]
    return cal


def events(url: str) -> None:
    cal = _cal(url)
    now = datetime.now().astimezone(tz)
    window = timedelta(days=7)

    events = []

    raw_events = cal.events()
    for event in raw_events:
        # event.vobject_instance.prettyPrint()
        vevent = event.vobject_instance.vevent
        # TODO(tsileo): parse .event_list, support dtend
        keys = vevent.sortChildKeys()

        if "duration" in keys:
            duration = vevent.duration.value
        else:
            duration = None

        if "summary" in keys:
            summary = vevent.summary.value
        else:
            summary = None

        if "location" in keys:
            location = vevent.location.value
        else:
            location = None

        if "description" in keys:
            description = vevent.description.value
        else:
            description = None

        # Check if it's reccurent event
        if vevent.rruleset:
            next_date = vevent.rruleset.after(now).astimezone(tz)
        else:
            # One-time event
            next_date = vevent.dtstart.value.astimezone(tz)

        if next_date < now or next_date > now + window:
            continue

        end = next_date
        if duration:
            end = end + duration
            duration = int(duration.total_seconds())

        # TODO parse alarms, show uid
        current_event = {
            "id": str(event.url),
            "summary": summary,
            "duration": duration,
            "location": location,
            "description": description,
            "start": next_date.isoformat(),
            "start_human": next_date.strftime(DATE_FMT),
            "end": end.isoformat(),
        }
        events.append(current_event)

    events = sorted(events, key=lambda e: e["start"])
    return events


def new_event(
    url: str,
    title: str,
    dt: datetime,
    loc: Optional[str] = None,
    duration: Optional[str] = None,
) -> None:
    cal = vobject.iCalendar()
    cal.add("vevent")
    cal.vevent.add("summary").value = title
    cal.vevent.add("uid").value = str(uuid.uuid4())
    cal.vevent.add("dtstart").value = dt
    if loc:
        cal.vevent.add("location").value = loc
    if duration:
        cal.vevent.add("duration").value = parse_duration(duration)
    cal.vevent.add("valarm")
    # FIXME(tsileo): parse_duration for the trigger
    cal.vevent.valarm.add("trigger").value = timedelta(hours=-4)
    cal.vevent.valarm.add("action").value = "DISPLAY"
    cal.vevent.valarm.add("description").value = title
    ccal = _cal(url)
    ccal.add_event(cal.serialize())
    return cal

def main() -> None:  # noqa: C901
    """CLI interface."""
    cli_args = sys.argv[1:]

    # Check if the help is requested
    if len(cli_args) == 1 and cli_args[0] in ["--help", "-h"]:
        help()
        return

    # Config check
    CONFIG_FILE = Path("~/.config/events.yaml").expanduser()
    try:
        with CONFIG_FILE.open() as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Please create config file at {CONFIG_FILE}. 😾")
        return

    url = config["url"]

    if not cli_args:
        print(f"{now.strftime(DATE_FMT)}\tNOW\n")
        evts = events(url)
        for event in evts:
            print("{start_human}\t{summary}".format(**event))

    elif cli_args[0] == "add":
        add_args = cli_args[1:]
        if add_args:
            print(add_args)
            loc = None
            dur = None
            for i, part in enumerate(add_args.copy()):
                if part.startswith("loc:"):
                    loc = part[4:]
                    add_args.pop(i)
                    break

            for i, part in enumerate(add_args.copy()):
                if part.startswith("dur:"):
                    dur = part[4:]
                    add_args.pop(i)
                    break

            dt, rest = parse(" ".join(add_args), fuzzy_with_tokens=True)
            dt = dt.astimezone(tz)
            new_event(url, (" ".join(rest)).strip(), dt, loc, dur)

    return None


if __name__ == "__main__":
    # print(new_event().serialize())
    main()
