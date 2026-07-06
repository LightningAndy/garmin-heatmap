import json, os, glob, re, hashlib
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

    chunk_entries = []
    for i, chunk in enumerate(chunks):
        filename = f"heatmap_{i+1}.json"
        filepath = f"docs/{filename}"
        payload  = json.dumps(chunk)
        with open(filepath, "w") as f:
            f.write(payload)
        digest = hashlib.md5(payload.encode()).hexdigest()
        size_mb = os.path.getsize(filepath) / 1024 / 1024
        print(f"  📦 {filename}: {len(chunk)} activities, {size_mb:.1f}MB")
        chunk_entries.append({"file": filename, "hash": digest})

    manifest = {"chunks": chunk_entries}
    with open("docs/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  📋 manifest.json updated — {len(chunk_entries)} chunk(s)")


NS = "{http://www.topografix.com/GPX/1/1}"
brouter_activities = []

gpx_files = sorted(glob.glob("brouter/*.gpx"))
print(f"Found {len(gpx_files)} GPX files in /brouter/")

for filepath in gpx_files:
    filename = os.path.basename(filepath)
    try:
        # Extract date from filename: "YYYY-MM-DD - Name.gpx"
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\s*-\s*(.+)\.gpx$", filename)
        if m:
            date = m.group(1)
            name = m.group(2).strip()
        else:
            print(f"  ⚠️ {filename}: no date prefix (expected 'YYYY-MM-DD - Name.gpx'), skipping")
            continue

        tree = ET.parse(filepath)
        root = tree.getroot()
        trkpts = root.findall(f".//{NS}trkpt")

        # Fallback for GPX 1.0 namespace or no namespace
        if not trkpts:
            trkpts = root.findall(".//trkpt")

        points = []
        for p in trkpts:
            lat = float(p.attrib["lat"])
            lon = float(p.attrib["lon"])
            points.append([lat, lon])

        if len(points) < 2:
            print(f"  ⚠️ {filename}: fewer than 2 points, skipping")
            continue

        activity_id = f"brouter_{hashlib.md5(filename.encode()).hexdigest()[:10]}"
        brouter_activities.append({
            "id":     activity_id,
            "name":   name,
            "type":   "brouter",
            "date":   date,
            "points": points
        })
        print(f"  ✅ {name} [{date}]: {len(points)} points")

    except Exception as e:
        print(f"  ❌ {filename}: {e}")

# Load all activities from chunks
os.makedirs("docs", exist_ok=True)
all_activities = []
chunk_files = sorted(glob.glob("docs/heatmap_*.json"))
for cf in chunk_files:
    with open(cf) as f:
        all_activities.extend(json.load(f))

# Replace brouter entries and rewrite chunks
all_activities = [a for a in all_activities if a.get("type") != "brouter"]
all_activities = all_activities + brouter_activities

write_chunks(all_activities)
print(f"✅ Done. {len(brouter_activities)} brouter routes. Total activities: {len(all_activities)}")
