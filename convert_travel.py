import json
from datetime import datetime, timezone

# Load locations
with open("locations1.json") as f:
    data = json.load(f)

locations = data["locations"]
locations.sort(key=lambda x: x["time"])

# Split into trips by detecting gaps > 6 hours
GAP_SECONDS = 6 * 60 * 60
trips = []
current = [locations[0]]

for loc in locations[1:]:
    if loc["time"] - current[-1]["time"] > GAP_SECONDS:
        trips.append(current)
        current = [loc]
    else:
        current.append(loc)
trips.append(current)

# Convert to activity format
travel_activities = []
for i, trip in enumerate(trips):
    date = datetime.fromtimestamp(trip[0]["time"], tz=timezone.utc).strftime("%Y-%m-%d")
    points = [[loc["lat"], loc["lon"]] for loc in trip]
    travel_activities.append({
        "id": f"travel_{i}",
        "name": "Travel",
        "type": "travel",
        "date": date,
        "points": points
    })
    print(f"  Trip {i+1}: {date} — {len(points)} points")

# Load existing heatmap.json
with open("docs/heatmap.json") as f:
    existing = json.load(f)

# Remove old travel entries and re-add fresh ones
existing = [a for a in existing if a.get("type") != "travel"]
merged = existing + travel_activities

with open("docs/heatmap.json", "w") as f:
    json.dump(merged, f)

print(f"\n✅ Done. {len(travel_activities)} travel trips merged. Total activities: {len(merged)}")
