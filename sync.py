import os, json
from garminconnect import Garmin

email = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]

client = Garmin(email, password)
client.login()

# Load existing points
try:
    with open("docs/heatmap.json") as f:
        points = json.load(f)
except:
    points = []

existing_ids = {p["id"] for p in points if "id" in p}

# Fetch last 100 activities
activities = client.get_activities(0, 100)

for act in activities:
    aid = str(act["activityId"])
    if aid in existing_ids:
        continue
    try:
        gpx_data = client.download_activity(aid, dl_fmt=client.ActivityDownloadFormat.GPX)
        # Parse GPX for lat/lon points
        import xml.etree.ElementTree as ET
        root = ET.fromstring(gpx_data)
        ns = {"gpx": "http://www.topografix.com/GPX/1/1"}
        for trkpt in root.findall(".//gpx:trkpt", ns):
            lat = float(trkpt.attrib["lat"])
            lon = float(trkpt.attrib["lon"])
            points.append({"id": aid, "lat": lat, "lon": lon})
    except Exception as e:
        print(f"Skipping {aid}: {e}")

os.makedirs("docs", exist_ok=True)
with open("docs/heatmap.json", "w") as f:
    json.dump(points, f)

print(f"Total points: {len(points)}")
