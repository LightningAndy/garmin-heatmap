import json, os, glob
from datetime import datetime, timezone

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


GAP_SECONDS  = 6 * 60 * 60
polar_activities = []
file_index   = 0

os.makedirs("docs", exist_ok=True)
json_files = sorted(glob.glob("polar/*.json"))
print(f"Found {len(json_files)} JSON files in /polar/")

for filepath in json_files:
    filename = os.path.basename(filepath)
    try:
        with open(filepath) as f:
            data = json.load(f)

        locations = data["locations"] if isinstance(data, dict) and "locations" in data else data
        locations = sorted(locations, key=lambda x: x["time"])

        if not locations:
            print(f"  ⚠️ {filename}: empty, skipping")
            continue

        trips   = []
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
            iso  = lambda t: datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            points = [[loc["lat"], loc["lon"], iso(loc["time"])] for loc in trip]
            activity_id = f"polar_{file_index}"
            file_index += 1
            polar_activities.append({
                "id":     activity_id,
                "name":   f"Polar Travel ({date})",
                "type":   "polar_travel",
                "date":   date,
                "points": points
            })
            print(f"    ✅ Trip: {date} — {len(points)} points")

    except Exception as e:
        print(f"  ❌ {filename}: {e}")

# Save polar_travel.json as before
with open("docs/polar_travel.json", "w") as f:
    json.dump(polar_activities, f)
print(f"\n📍 Saved {len(polar_activities)} polar trips to docs/polar_travel.json")

# Load all activities from chunks
all_activities = []
chunk_files = sorted(glob.glob("docs/heatmap_*.json"))
if chunk_files:
    for cf in chunk_files:
        with open(cf) as f:
            all_activities.extend(json.load(f))
else:
    try:
        with open("docs/heatmap.json") as f:
            all_activities = json.load(f)
    except:
        all_activities = []

# Replace polar entries and rewrite chunks
all_activities = [a for a in all_activities if a.get("type") != "polar_travel"]
all_activities = all_activities + polar_activities

write_chunks(all_activities)
print(f"✅ Done. Total activities: {len(all_activities)}")
