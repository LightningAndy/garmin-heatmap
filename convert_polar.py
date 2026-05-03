import json, glob, os
import xml.etree.ElementTree as ET

NS = "http://www.topografix.com/GPX/1/1"
polar_activities = []

gpx_files = sorted(glob.glob("polar/*.gpx"))
print(f"Found {len(gpx_files)} GPX files in /polar/")

for filepath in gpx_files:
    filename = os.path.basename(filepath)
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        # Get track name if available
        name_el = root.find(f".//{{{NS}}}name")
        name = name_el.text if name_el is not None else filename.replace(".gpx", "")

        # Get all track points
        trkpts = root.findall(f".//{{{NS}}}trkpt")

        points = []
        date = ""
        for p in trkpts:
            lat = float(p.attrib["lat"])
            lon = float(p.attrib["lon"])
            time_el = p.find(f"{{{NS}}}time")
            if time_el is not None and time_el.text:
                points.append([lat, lon, time_el.text])
                if not date:
                    date = time_el.text[:10]
            else:
                points.append([lat, lon])

        if not points:
            print(f"  ⚠️ {filename}: no points found, skipping")
            continue

        activity_id = f"polar_{filename.replace('.gpx', '')}"
        polar_activities.append({
            "id": activity_id,
            "name": name,
            "type": "polar_travel",
            "date": date,
            "points": points
        })
        print(f"  ✅ {filename}: {len(points)} points, date {date}")

    except Exception as e:
        print(f"  ❌ {filename}: {e}")

# Save polar_travel.json
with open("docs/polar_travel.json", "w") as f:
    json.dump(polar_activities, f)
print(f"\n📍 Saved {len(polar_activities)} polar activities to docs/polar_travel.json")

# Merge into heatmap.json
try:
    with open("docs/heatmap.json") as f:
        heatmap = json.load(f)
except:
    heatmap = []

# Remove old polar entries and re-add fresh
heatmap = [a for a in heatmap if a.get("type") != "polar_travel"]
heatmap = heatmap + polar_activities

with open("docs/heatmap.json", "w") as f:
    json.dump(heatmap, f)

print(f"✅ Merged into heatmap.json. Total activities: {len(heatmap)}")
