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
        raw = json.load(f)
    # Wipe old data since we're adding new fields
    print(f"📍 Rebuilding from scratch to add type/date fields")
    points = []
    existing_ids = set()
except:
    points = []
    existing_ids = set()

activities = client.get_activities(0, 100)
print(f"🏃 Found {len(activities)} activities")

for act in activities:
    aid = str(act["activityId"])
    if aid in existing_ids:
        continue

    activity_type = act.get("activityType", {}).get("typeKey", "unknown")
    activity_date = act.get("startTimeLocal", "")[:10]  # YYYY-MM-DD
    name = act.get("activityName", "unknown")

    try:
        gpx_data = client.download_activity(aid, dl_fmt=client.ActivityDownloadFormat.GPX)
        root = ET.fromstring(gpx_data)
        ns = {"gpx": "http://www.topografix.com/GPX/1/1"}
        trkpts = root.findall(".//gpx:trkpt", ns)
        print(f"  ✅ {name} [{activity_type}] {activity_date}: {len(trkpts)} points")
        for trkpt in trkpts:
            points.append({
                "id": aid,
                "lat": float(trkpt.attrib["lat"]),
                "lon": float(trkpt.attrib["lon"]),
                "type": activity_type,
                "date": activity_date
            })
    except Exception as e:
        print(f"  ❌ {name} ({aid}): {e}")

os.makedirs("docs", exist_ok=True)
with open("docs/heatmap.json", "w") as f:
    json.dump(points, f)

print(f"\n✅ Done. Total points: {len(points)}")
