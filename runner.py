# AI Asset Protection with Edge Impulse + OpenClaw 
# Roni Bandini @RoniBandini
# June 2026, MIT License

import subprocess
import time
import requests
import json
import csv
import os

from datetime import datetime, time as dtime
from sensors import read_sensors


# ******* Settings ************************************************************** 

WATCH_DEFAULT_X = 32
WATCH_DEFAULT_Y = 40
WATCH_POSITION_THRESHOLD_PCT = 20

# Confidence threshold (0.0–1.0) to consider a detection valid
CONFIDENCE_THRESHOLD = 0.85

# Opening and closing time (24 h). Detections are interpreted differently
# depending on whether the museum is open or closed.
MUSEUM_OPEN_HOUR  = 9   # 09:00
MUSEUM_CLOSE_HOUR = 18  # 18:00

def is_open_hours() -> bool:
    now = datetime.now().time()
    return dtime(MUSEUM_OPEN_HOUR, 0) <= now < dtime(MUSEUM_CLOSE_HOUR, 0)

DEFAULT_OBJECT_TEMP  = 22.0   # expected display-case surface temp in °C  
DEFAULT_AMBIENT_TEMP = 22.0   # expected room temperature in °C
TEMP_THRESHOLD_PCT   = 15     # alert if deviation exceeds this %

# ******* Output files ******************************************************************

STATUS_FILE = "watch_status.txt"
LOG_FILE    = "watch_log.csv"

# ******* Webhook ******************************************************************

WEBHOOK_URL = "" # future use

# ******* CSV setup ******************************************************************

CSV_FIELDS = [
    "timestamp", "event", "museum_open",
    "confidence", "x", "y", "in_position",
    "pir", "microwave", "ambient_temp", "object_temp",
    "position_threshold_pct", "temp_threshold_pct",
]

def _ensure_csv():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()

def _append_csv(row: dict):
    _ensure_csv()
    with open(LOG_FILE, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore").writerow(row)


# ******* Misc ******************************************************************

def _write_status(lines: list):
    with open(STATUS_FILE, "w") as f:
        for line in lines:
            f.write(line + "\n")

def cleanScreen():
    # 'nt' Windows, 'posix' Linux/macOS
    os.system('cls' if os.name == 'nt' else 'clear')

def within_position(x, y):
    def pct_ok(value, default):
        if default == 0:
            return value == 0
        return abs(value - default) / default * 100 <= WATCH_POSITION_THRESHOLD_PCT
    return pct_ok(x, WATCH_DEFAULT_X) and pct_ok(y, WATCH_DEFAULT_Y)

def temp_deviation_pct(measured, default):
    if default == 0 or measured is None:
        return None
    return abs(measured - default) / abs(default) * 100

# ******* Startup ********************************************************************

_ensure_csv()
output_file = open("output.txt", "w")
cleanScreen()
print(r"""
    ___    ___      _                     _     ____            _            _   _
   / _ \  |_ _|    / \   ___ ___  ___ ___| |_  |  _ \ _ __ ___ | |_ ___  ___| |_(_) ___  _ __
  / /_\ \  | |    / _ \ / __/ __|/ _ / __| __| | |_) | '__/ _ \| __/ _ \/ __| __| |/ _ \| '_ \
 / ___  |  | |   / ___ \\__ \__ |  __\__ | |_  |  __/| | | (_) | ||  __/ (__| |_| | (_) | | | |
/_/   |_| |___| /_/   \_|___|___/\___|___/\__| |_|   |_|  \___/ \__\___|\___|\__|_|\___/|_| |_|

""")
print("AI Asset Protection")
print("Roni Bandini, June 2026, Argentina, @RoniBandini")
print("")
print(f"Museum hours            → {MUSEUM_OPEN_HOUR:02d}:00 – {MUSEUM_CLOSE_HOUR:02d}:00")
print(f"Watch default position  → X:{WATCH_DEFAULT_X}  Y:{WATCH_DEFAULT_Y}  (±{WATCH_POSITION_THRESHOLD_PCT}%)")
print(f"Confidence threshold    → {CONFIDENCE_THRESHOLD}")
print(f"Object temp default     → {DEFAULT_OBJECT_TEMP}°C  (±{TEMP_THRESHOLD_PCT}%)")
print(f"Ambient temp default    → {DEFAULT_AMBIENT_TEMP}°C  (±{TEMP_THRESHOLD_PCT}%)")
print(f"Status file             → {STATUS_FILE}")
print(f"Log file                → {LOG_FILE}")
print("")
print("Stop with CTRL-C")

subprocess.Popen(["edge-impulse-linux-runner"], stdout=output_file)

# ******* Main loop ******************************************************************


with open("output.txt", "r") as f:
    lines_seen = set()
    while True:
        line = f.readline()
        if not line:
            time.sleep(1)
            continue

        ts      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        open_hr = is_open_hours()
        hours_label = "OPEN" if open_hr else "CLOSED"

        # ******* No detection ******************************************************************
        if "[]" in line:
            # During closed hours, also sample sensors for intruder check
            sensors  = read_sensors()
            pir      = sensors["pir"]
            micro    = sensors["microwave"]
            ambient  = sensors["ambient"]
            obj_temp = sensors["object"]

            amb_dev  = temp_deviation_pct(ambient,  DEFAULT_AMBIENT_TEMP)
            obj_dev  = temp_deviation_pct(obj_temp, DEFAULT_OBJECT_TEMP)
            temp_anomaly = (
                (amb_dev is not None and amb_dev > TEMP_THRESHOLD_PCT) or
                (obj_dev is not None and obj_dev > TEMP_THRESHOLD_PCT)
            )

            if not open_hr and (pir or micro or temp_anomaly):
                event = "AFTER_HOURS_INTRUSION"
                print(f"[{ts}] 🚨 AFTER-HOURS activity — watch missing + sensor activity")
            else:
                event = "WATCH_MISSING"
                print(f"[{ts}] Watch not in place  [{hours_label}]")

            status_lines = [
                f"timestamp={ts}",
                f"event={event}",
                f"museum_open={int(open_hr)}",
                "confidence=0",
                "x=", "y=", "in_position=",
                f"pir={int(pir)}",
                f"microwave={int(micro)}",
                f"ambient_temp={ambient:.2f}" if ambient is not None else "ambient_temp=ERROR",
                f"object_temp={obj_temp:.2f}" if obj_temp is not None else "object_temp=ERROR",
            ]
            _write_status(status_lines)
            _append_csv({
                "timestamp": ts, "event": event, "museum_open": int(open_hr),
                "confidence": 0, "x": "", "y": "", "in_position": "",
                "pir": int(pir), "microwave": int(micro),
                "ambient_temp": f"{ambient:.2f}" if ambient is not None else "ERROR",
                "object_temp":  f"{obj_temp:.2f}" if obj_temp is not None else "ERROR",
                "position_threshold_pct": WATCH_POSITION_THRESHOLD_PCT,
                "temp_threshold_pct": TEMP_THRESHOLD_PCT,
            })
            continue

        # ******* Watch in place ******************************************************************
        if "height" in line and "watch" in line and line not in lines_seen:
            json_start = line.find("[")
            if json_start != -1:
                json_str = line[json_start:].strip()
                try:
                    detections = json.loads(json_str)
                    for det in detections:
                        if det.get("label") != "watch":
                            continue

                        confidence = det["value"]
                        x, y       = det["x"], det["y"]
                        in_pos     = within_position(x, y)

                        sensors  = read_sensors()
                        pir      = sensors["pir"]
                        micro    = sensors["microwave"]
                        ambient  = sensors["ambient"]
                        obj_temp = sensors["object"]

                        obj_dev = temp_deviation_pct(obj_temp, DEFAULT_OBJECT_TEMP)
                        amb_dev = temp_deviation_pct(ambient,  DEFAULT_AMBIENT_TEMP)
                        obj_temp_ok = (obj_dev is None) or (obj_dev <= TEMP_THRESHOLD_PCT)
                        amb_temp_ok = (amb_dev is None) or (amb_dev <= TEMP_THRESHOLD_PCT)

                        # Classify event
                        if not open_hr and (pir or micro):
                            # Watch still in frame but someone is in the room after hours
                            event = "AFTER_HOURS_PRESENCE"
                        else:
                            event = "WATCH_IN_PLACE"

                        # Console output
                        print("─" * 52)
                        print(f"  [{ts}] 🕐 Watch in place  [{hours_label}]")
                        print(f"  Confidence : {confidence:.4f}")
                        print(f"  Coordinates: X={x}  Y={y}")
                        print(f"  Position   : {'✅ in range' if in_pos else '⚠️  out of range'}")
                        print(f"  PIR        : {'🔥 motion' if pir else 'no motion'}")
                        print(f"  Microwave  : {'📡 motion' if micro else 'no motion'}")
                        if ambient is not None:
                            print(f"  Ambient    : {ambient:.1f}°C {'✅' if amb_temp_ok else '⚠️ '}")
                            print(f"  Object     : {obj_temp:.1f}°C {'✅' if obj_temp_ok else '⚠️ '}")
                        else:
                            print("  Temp sensor: ❌ read error")
                        if event == "AFTER_HOURS_PRESENCE":
                            print("  ⚠️  AFTER-HOURS human presence detected!")

                        # Status file
                        status_lines = [
                            f"timestamp={ts}",
                            f"event={event}",
                            f"museum_open={int(open_hr)}",
                            f"confidence={confidence:.4f}",
                            f"x={x}",
                            f"y={y}",
                            f"in_position={int(in_pos)}",
                            f"pir={int(pir)}",
                            f"microwave={int(micro)}",
                            f"ambient_temp={ambient:.2f}" if ambient is not None else "ambient_temp=ERROR",
                            f"object_temp={obj_temp:.2f}" if obj_temp is not None else "object_temp=ERROR",
                        ]
                        _write_status(status_lines)

                        # CSV log
                        _append_csv({
                            "timestamp":  ts,
                            "event":      event,
                            "museum_open": int(open_hr),
                            "confidence": f"{confidence:.4f}",
                            "x": x, "y": y,
                            "in_position": int(in_pos),
                            "pir":        int(pir),
                            "microwave":  int(micro),
                            "ambient_temp": f"{ambient:.2f}" if ambient is not None else "ERROR",
                            "object_temp":  f"{obj_temp:.2f}" if obj_temp is not None else "ERROR",
                            "position_threshold_pct": WATCH_POSITION_THRESHOLD_PCT,
                            "temp_threshold_pct":     TEMP_THRESHOLD_PCT,
                        })

                        # Webhook
                        if confidence >= CONFIDENCE_THRESHOLD and WEBHOOK_URL:
                            print("  ⚡ Triggering webhook")
                            try:
                                payload = {
                                    "timestamp":  ts,
                                    "event":      event,
                                    "museum_open": open_hr,
                                    "label":      det["label"],
                                    "confidence": confidence,
                                    "x": x, "y": y,
                                    "width":  det["width"],
                                    "height": det["height"],
                                    "in_expected_position": in_pos,
                                    "pir":       pir,
                                    "microwave": micro,
                                    "ambient_temp": ambient,
                                    "object_temp":  obj_temp,
                                }
                                r = requests.post(WEBHOOK_URL, json=payload, timeout=5)
                                print(f"  Webhook response: {r.status_code} {r.text}")
                            except Exception as e:
                                print(f"  Webhook error: {e}")

                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")

            lines_seen.add(line)
