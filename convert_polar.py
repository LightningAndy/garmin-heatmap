import json, os
from datetime import datetime, timezone

# Gap threshold to split into separate trips (6 hours)
GAP_SECONDS = 6 * 60 * 60

polar_activities = []
file_index = 0

# Process all .json files in the polar/ folder
import glob
json_files = sorted(glob.glob("polar/*.json"))
print(f"Found {len(json_files)} JSON files in /polar/")

for filepath in json_files:
    filename = os.path.basename(filepath)
    try:
        with open(filepath) as f:
            data = json.load(f)

        # Support both {"locations": [...]} and bare [...]
        locations = data["locations"] if isinstance(data, dict) and "locations" in data else data
        locations = sorted(locations, key=lambda x: x["time"])

        if not locations:
            print(f"  ⚠️ {filename}: empty, skipping")
            continue

        # Split into trips by time gap
        trips = []
        current = [locations[0]]
        for loc in locations[1:]:
            if loc["time"] - current[-1]["time"] > GAP_SECONDS:
                trips.append(current)
                current = [loc]
            else:
                current.append(loc)
        trips.append(current)

        print(f"  📍 {filename}: {len(locations)} points → {len(trips)} trips")

        for trip in trips:
            date = datetime.fromtimestamp(trip[0]["time"], tz=timezone.utc).strftime("%Y-%m-%d")
            iso = lambda t: datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            points = [[loc["lat"], loc["lon"], iso(loc["time"])] for loc in trip]
            activity_id = f"polar_{file_index}"
            file_index += 1
            polar_activities.append({
                "id": activity_id,
                "name": f"Polar Travel ({date})",
                "type": "polar_travel",
                "date": date,
                "points": points
            })
            print(f"    ✅ Trip: {date} — {len(points)} points")

    except Exception as e:
        print(f"  ❌ {filename}: {e}")

# Save polar_travel.json
os.makedirs("docs", exist_ok=True)
with open("docs/polar_travel.json", "w") as f:
    json.dump(polar_activities, f)
print(f"\n📍 Saved {len(polar_activities)} polar trips to docs/polar_travel.json")

# Merge into heatmap.json
try:
    with open("docs/heatmap.json") as f:
        heatmap = json.load(f)
except:
    heatmap = []

heatmap = [a for a in heatmap if a.get("type") != "polar_travel"]
heatmap = heatmap + polar_activities

with open("docs/heatmap.json", "w") as f:
    json.dump(heatmap, f)

print(f"✅ Merged into heatmap.json. Total activities: {len(heatmap)}")
