#!/usr/bin/env python3
"""Télécharge l'emploi du temps HyperPlanning (.ics) et l'écrit dans data/events.json.

L'URL est lue dans la variable d'environnement ICS_URL (secret GitHub),
pour qu'elle n'apparaisse jamais dans le code public.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
OUT = Path(__file__).resolve().parent.parent / "data" / "events.json"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (agenda-github-pages)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def unfold(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line[:1] in (" ", "\t") and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def unescape(v: str) -> str:
    return re.sub(r"\\([\\;,nN])", lambda m: "\n" if m.group(1) in "nN" else m.group(1), v).strip()


LINE_RE = re.compile(r'^([A-Za-z0-9-]+)((?:;[^:;=]+=(?:"[^"]*"|[^:;]*))*):(.*)$')
PARAM_RE = re.compile(r';([^:;=]+)=("[^"]*"|[^:;]*)')


def parse_line(line: str):
    m = LINE_RE.match(line)
    if not m:
        return None
    params = {k.upper(): v.strip('"') for k, v in PARAM_RE.findall(m.group(2))}
    return m.group(1).upper(), params, m.group(3)


def parse_dt(value: str, params: dict):
    value = value.strip()
    if params.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", value):
        return datetime.strptime(value[:8], "%Y%m%d").replace(tzinfo=PARIS), True
    fmt = "%Y%m%dT%H%M%S"
    if value.endswith("Z"):
        return datetime.strptime(value[:-1], fmt).replace(tzinfo=timezone.utc), False
    tz = PARIS
    if "TZID" in params:
        try:
            tz = ZoneInfo(params["TZID"])
        except Exception:
            tz = PARIS  # ex. "Romance Standard Time" (fuseau Windows) -> Paris
    return datetime.strptime(value[:15], fmt).replace(tzinfo=tz), False


def parse_events(text: str) -> list[dict]:
    events, cur = [], None
    for line in unfold(text):
        if line == "BEGIN:VEVENT":
            cur = {}
            continue
        if line == "END:VEVENT":
            if cur is not None and "start" in cur and cur.get("status") != "CANCELLED":
                start = cur["start"]
                end = cur.get("end") or (start + timedelta(days=1) if cur["allDay"] else start + timedelta(hours=1))
                events.append({
                    "_sort": start.timestamp(),
                    "id": cur.get("uid", ""),
                    "title": cur.get("summary", "(sans titre)"),
                    "location": cur.get("location", ""),
                    "description": cur.get("description", ""),
                    "start": start.astimezone(PARIS).isoformat(),
                    "end": end.astimezone(PARIS).isoformat(),
                    "allDay": cur["allDay"],
                })
            cur = None
            continue
        if cur is None:
            continue
        parsed = parse_line(line)
        if not parsed:
            continue
        name, params, value = parsed
        if name == "DTSTART":
            cur["start"], cur["allDay"] = parse_dt(value, params)
        elif name == "DTEND":
            cur["end"], _ = parse_dt(value, params)
        elif name in ("SUMMARY", "LOCATION", "DESCRIPTION", "UID", "STATUS"):
            cur[name.lower()] = unescape(value)
    events.sort(key=lambda e: e["_sort"])
    for e in events:
        del e["_sort"]
    return events


def main() -> int:
    url = os.environ.get("ICS_URL", "").strip()
    if not url:
        print("ICS_URL est vide : ajoute le secret ICS_URL dans les réglages du dépôt.", file=sys.stderr)
        return 1
    try:
        events = parse_events(fetch(url))
    except Exception as exc:
        print(f"Téléchargement impossible : {exc}", file=sys.stderr)
        return 1
    if not events:
        print("Aucun événement trouvé : fichier conservé tel quel.", file=sys.stderr)
        return 1

    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    if old.get("events") == events:
        print(f"Aucun changement ({len(events)} événements).")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "events": events,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(events)} événements écrits dans {OUT}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
