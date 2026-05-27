import os, json, glob
from garminconnect import Garmin
import xml.etree.ElementTree as ET

CHUNK_SIZE_BYTES = 45 * 1024 * 1024

def write_chunks(activities):
    for cf in glob.glob("docs/heatmap_*.json"):
        os.remove(cf)

    chunks = []
    current_chunk = []
    current_size  = 0

    for activity in activities:
        estimated_size = len(json.dumps(activity))
        if current_size + estimated_size > CHUNK_SIZE_BYTES and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_size  = 0
        current_chunk.append(activity)
        current_size += estimated_size

    if current_chunk:
        chunks.append(current_chunk)

    chunk_filenames = []
    for i, chunk in enumerate(chunks):
        filename = f"heatmap_{i+1}.json"
        filepath = f"docs/{filename}"
        with open(filepath, "w") as f:
            json.dump(chunk, f)
        size_mb = os.path.getsize(filepath) / 1024 / 1024
        print(f"  📦 {filename}: {len(chunk)} activities, {size_mb:.1f}MB")
        chunk_filenames.append(filename)

    manifest = {"chunks": chunk_filenames}
    with open("docs/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  📋 manifest.json updated — {len(chunk_filenames)} chunk(s)")


email    = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]

client = Garmin(email, password)
client.login()
print("✅ Logged in to Garmin")

activities   = []
existing_ids = set()

os.makedirs("docs", exist_ok=True)
chunk_files = sorted(glob.glob("docs/heatmap_*.json"))

if chunk_files:
    for cf in chunk_files:
        with open(cf) as f:
            activities.extend(json.load(f))
    existing_ids = {a["id"] for a in activities}
    print(f"📍 {len(activities)} activities loaded from {len(chunk_files)} chunk(s)")
else:
    try:
        with open("docs/heatmap.json") as f:
            existing = json.load(f)
        if isinstance(existing, list) and existing and "points" in existing[0]:
            activities = existing
        existing_ids = {a["id"] for a in activities}
        print(f"📍 {len(activities)} activities loaded from heatmap.json (legacy)")
    except:
        print("📍 Starting fresh")

raw_activities = client.get_activities(0, 100)
print(f"🏃 Found {len(raw_activities)} activities from Garmin")

new_count = 0
for act in raw_activities:
    aid = str(act["activityId"])
    if aid in existing_ids:
        continue

    activity_type = act.get("activityType", {}).get("typeKey", "unknown")
    activity_date = act.get("startTimeLocal", "")[:10]
    name          = act.get("activityName", "unknown")

    try:
        gpx_data = client.download_activity(aid, dl_fmt=client.ActivityDownloadFormat.GPX)
        root     = ET.fromstring(gpx_data)
        ns       = {"gpx": "http://www.topografix.com/GPX/1/1"}
        trkpts   = root.findall(".//gpx:trkpt", ns)

        points = []
        for p in trkpts:
            lat     = float(p.attrib["lat"])
            lon     = float(p.attrib["lon"])
            time_el = p.find("{http://www.topografix.com/GPX/1/1}time")
            if time_el is not None and time_el.text:
                points.append([lat, lon, time_el.text])
            else:
                points.append([lat, lon])

        print(f"  ✅ {name} [{activity_type}] {activity_date}: {len(points)} points")
        activities.append({
            "id":     aid,
            "name":   name,
            "type":   activity_type,
            "date":   activity_date,
            "points": points
        })
        new_count += 1

    except Exception as e:
        print(f"  ❌ {name} ({aid}): {e}")

if new_count == 0:
    print("No new activities — skipping chunk rewrite")
else:
    write_chunks(activities)

total_points = sum(len(a["points"]) for a in activities)
print(f"\n✅ Done. {len(activities)} activities, {total_points} total points")
