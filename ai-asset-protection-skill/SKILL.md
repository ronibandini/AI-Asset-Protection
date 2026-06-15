---
name: museum-watch-monitor
description: >
  OpenClaw skill for monitoring a museum watch exhibit using combined Edge Impulse
  image recognition, PIR motion, RCWL-0516 microwave, and MLX90614 IR temperature sensors.
  Trigger this skill whenever the user mentions museum security, exhibit monitoring,
  watch detection, sensor fusion alerts, or reading from watch_status.txt or watch_log.csv.
  Use this skill to decide whether to log normally, alert support about equipment issues,
  alert internal security during open hours, or call authorities after hours.
---

# Museum Watch Monitor — OpenClaw Skill

## Purpose

This skill is the decision layer for a physical museum watch security system.
It reads the latest sensor + detection state from `watch_status.txt` (written by
`runner.py`) and takes one of four actions:

| Priority | Action | When |
|---|---|---|
| 1 | **Alert Support** | A sensor or camera appears to be malfunctioning |
| 2 | **Call Authorities** | Anomaly detected outside museum hours |
| 3 | **Alert Internal Security** | Anomaly detected during open hours |
| 4 | **Log** | Everything nominal |

---

## Input: watch_status.txt

`runner.py` overwrites this file after every detection cycle.
OpenClaw reads the whole file; each line is `key=value`.

### Fields

| Field | Type | Values / meaning |
|---|---|---|
| `timestamp` | string | ISO datetime of the reading |
| `event` | string | See event types below |
| `museum_open` | 0 or 1 | 1 = currently within working hours |
| `confidence` | float 0–1 | Image model confidence (0 = no detection) |
| `x`, `y` | int | Detected bounding-box origin in pixels |
| `in_position` | 0 or 1 | 1 = within expected coordinates ± threshold |
| `pir` | 0 or 1 | 1 = PIR motion triggered |
| `microwave` | 0 or 1 | 1 = RCWL-0516 microwave motion triggered |
| `ambient_temp` | float or ERROR | Room temperature °C |
| `object_temp` | float or ERROR | Display-case surface temperature °C |

### Event types written by runner.py

| Event | Meaning |
|---|---|
| `WATCH_IN_PLACE` | Watch detected, in position, open hours |
| `WATCH_MISSING` | Camera sees no watch (open or closed hours, no intrusion signals) |
| `AFTER_HOURS_PRESENCE` | Watch visible but PIR/microwave active outside hours |
| `AFTER_HOURS_INTRUSION` | Watch not visible AND sensor activity outside hours |

---

## Decision Logic

Work through checks **in order**. Stop at the first match.

### 1 — Equipment failure → Alert Support

Trigger if **any** of the following is true:

- `event` field is missing or empty (runner crashed or file is stale)
- `ambient_temp` or `object_temp` is `ERROR` (MLX90614 I2C failure)
- `confidence=0` AND `pir=0` AND `microwave=0` for **3+ consecutive cycles**
  (camera or runner likely frozen)
- `x`, `y`, `in_position` are blank when `event=WATCH_IN_PLACE`
  (JSON parse failure in runner)

**Support alert must include:**
- Which component(s) are failing
- First failure timestamp
- Suggested remediation (reboot runner, inspect I2C bus, check USB camera)

---

### 2 — After-hours anomaly → Call Authorities

Trigger when `museum_open=0` AND any of:

| Condition | Reasoning |
|---|---|
| `event=AFTER_HOURS_INTRUSION` | Watch gone + sensors firing — likely theft in progress |
| `event=AFTER_HOURS_PRESENCE` | Watch still visible but human presence detected — intruder |
| `event=WATCH_MISSING` AND (`pir=1` OR `microwave=1`) | No watch + motion — same risk |
| `ambient_temp` or `object_temp` deviates > threshold AND `museum_open=0` | Unusual thermal activity (e.g. heat source, forced entry) |

**Authorities alert must include:**
- Event type and timestamp
- Sensor states (PIR, microwave, temps)
- Last known watch position (x, y, confidence)
- Museum location / exhibit identifier (fill in your deployment details)

---

### 3 — Open-hours anomaly → Alert Internal Security

Trigger when `museum_open=1` AND any of:

| Condition | Reasoning |
|---|---|
| `event=WATCH_MISSING` | Watch not in frame during visiting hours — possible theft or mishandling |
| `event=WATCH_IN_PLACE` AND `in_position=0` | Watch visible but shifted — may have been touched or moved |
| `event=WATCH_IN_PLACE` AND `confidence < 0.55` | Very low-confidence detection — obstruction or substitution |
| Previous cycle was `WATCH_IN_PLACE` AND current is `WATCH_MISSING`, gap < 120 s | Watch disappeared suddenly |

**Internal security alert must include:**
- Condition that triggered the alert
- Timestamp + last good reading timestamp
- Sensor cross-reference (PIR, microwave)
- Confidence and coordinates

---

### 4 — Normal → Log

Everything else: write confirmation that the row was appended to `watch_log.csv`.

---

## Action Templates

### Support alert
```
[SUPPORT ALERT] {timestamp}
Component issue on Museum Watch Node.
Failing: {sensor list}
Action: {suggested fix}
Last clean reading: {timestamp or "unknown"}
```

### Authorities alert
```
[AUTHORITIES ALERT] {timestamp}
After-hours security event at Museum Watch Exhibit.
Event: {event}
Sensors: PIR={pir}  Microwave={microwave}
Temperatures: Ambient={ambient_temp}°C  Object={object_temp}°C
Last watch position: X={x} Y={y}  Confidence={confidence}
Immediate response required.
```

### Internal security alert
```
[SECURITY ALERT] {timestamp}  [OPEN HOURS]
Watch exhibit anomaly detected.
Condition: {specific trigger}
Confidence: {confidence}  In position: {yes/no}
PIR: {active/inactive}  Microwave: {active/inactive}
Coordinates: X={x} Y={y}
Please verify exhibit immediately.
```

### Normal log confirmation
```
[LOG] {timestamp} [{OPEN/CLOSED}] — Watch in place.
Confidence={confidence}, X={x}, Y={y},
Ambient={ambient_temp}°C, Object={object_temp}°C.
Row appended to watch_log.csv.
```

---

## Consecutive Reading Tracking

When polling `watch_status.txt` in a loop, keep a short in-memory history of
the last 5 readings to enable gap-based and consecutive-failure checks.
Reset counters when a normal `WATCH_IN_PLACE` reading resumes.

---

## Configuration Reference (set in runner.py)

| Parameter | Default | Meaning |
|---|---|---|
| `MUSEUM_OPEN_HOUR` | 9 | Opening time (24 h) |
| `MUSEUM_CLOSE_HOUR` | 18 | Closing time (24 h) |
| `WATCH_DEFAULT_X/Y` | 32 / 40 | Expected pixel position |
| `WATCH_POSITION_THRESHOLD_PCT` | 20% | Allowed positional drift |
| `CONFIDENCE_THRESHOLD` | 0.55 | Minimum valid detection |
| `DEFAULT_OBJECT_TEMP` | 22.0°C | Expected display-case surface temp |
| `DEFAULT_AMBIENT_TEMP` | 22.0°C | Expected room temp |
| `TEMP_THRESHOLD_PCT` | 15% | Temperature drift alert |

---

## Example Scenarios

**A — Normal (open hours)**
```
event=WATCH_IN_PLACE, museum_open=1, confidence=0.70, in_position=1,
pir=0, microwave=0, ambient=22.1°C, object=21.9°C
→ Log
```

**B — Watch missing, visitor present (open hours)**
```
event=WATCH_MISSING, museum_open=1, pir=1, microwave=1
→ Internal security alert: watch gone, motion detected during visiting hours
```

**C — After-hours intrusion, watch gone**
```
event=AFTER_HOURS_INTRUSION, museum_open=0, pir=1, microwave=1
→ Call authorities
```

**D — After-hours presence, watch still there**
```
event=AFTER_HOURS_PRESENCE, museum_open=0, pir=1, microwave=0, confidence=0.68
→ Call authorities: someone in the room, watch still visible
```

**E — Watch shifted during open hours**
```
event=WATCH_IN_PLACE, museum_open=1, in_position=0, confidence=0.65
→ Internal security alert: watch displaced
```

**F — Temperature sensor failure**
```
ambient_temp=ERROR, object_temp=ERROR
→ Support alert: MLX90614 not responding
```

**G — After-hours thermal anomaly only**
```
event=WATCH_IN_PLACE, museum_open=0, pir=0, microwave=0,
ambient_temp=28.5°C (deviation > 15%)
→ Call authorities: unusual heat signature after closing
```
