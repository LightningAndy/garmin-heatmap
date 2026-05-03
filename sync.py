import os, json
from garminconnect import Garmin
import xml.etree.ElementTree as ET

email = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]

client = Garmin(email, password)
client.login()
print("✅ Logged in to Garmin")

try:
    with open("docs/heatmap.json") as f:
        existing = json.load(f)
    # Support both old flat format and new grouped format
    if isinstance(existing, list) and existing and "points" in existing[0]:
        activities = existing
    else:
        activities = []
    existing_ids = {a["id"] for a in activities}
    print(f"📍 {len(activities)} activities already stored")
except:
    activities = []
    existing_ids = set()
    print("📍 Starting fresh")

raw_activities = client.get_activities(0, 100)
print(f"🏃 Found {len(raw_activities)} activities from Garmin")

for act in raw_activities:
    aid = str(act["activityId"])
    if aid in existing_ids:
        continue

    activity_type = act.get("activityType", {}).get("typeKey", "unknown")
    activity_date = act.get("startTimeLocal", "")[:10]
    name = act.get("activityName", "unknown")

    try:
        gpx_data = client.download_activity(aid, dl_fmt=client.ActivityDownloadFormat.GPX)
        root = ET.fromstring(gpx_data)
        ns = {"gpx": "http://www.topografix.com/GPX/1/1"}
        trkpts = root.findall(".//gpx:trkpt", ns)

        points = []
for p in trkpts:
    lat = float(p.attrib["lat"])
    lon = float(p.attrib["lon"])
    # Extract timestamp if available
    time_el = p.find("{http://www.topografix.com/GPX/1/1}time")
    if time_el is not None and time_el.text:
        points.append([lat, lon, time_el.text])
    else:
        points.append([lat, lon])


        print(f"  ✅ {name} [{activity_type}] {activity_date}: {len(points)} points")

        activities.append({
            "id": aid,
            "name": name,
            "type": activity_type,
            "date": activity_date,
            "points": points
        })

    except Exception as e:
        print(f"  ❌ {name} ({aid}): {e}")

os.makedirs("docs", exist_ok=True)
with open("docs/heatmap.json", "w") as f:
    json.dump(activities, f)

total_points = sum(len(a["points"]) for a in activities)
print(f"\n✅ Done. {len(activities)} activities, {total_points} total points")
