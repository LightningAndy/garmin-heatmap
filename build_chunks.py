import json, os, glob

CHUNK_SIZE_MB = 45
CHUNK_SIZE_BYTES = CHUNK_SIZE_MB * 1024 * 1024

os.makedirs("docs", exist_ok=True)

# Load all existing data from heatmap.json or existing chunks
activities = []

# Try loading from existing chunks first
chunk_files = sorted(glob.glob("docs/heatmap_*.json"))
if chunk_files:
    print(f"Found {len(chunk_files)} existing chunk files")
    for cf in chunk_files:
        with open(cf) as f:
            activities.extend(json.load(f))
        print(f"  Loaded {cf}")
else:
    # Fall back to single heatmap.json
    try:
        with open("docs/heatmap.json") as f:
            activities = json.load(f)
        print(f"Loaded {len(activities)} activities from heatmap.json")
    except:
        print("No existing data found")

print(f"\nTotal activities to chunk: {len(activities)}")

# Split into chunks by estimated size
chunks = []
current_chunk = []
current_size = 0

for activity in activities:
    estimated_size = len(json.dumps(activity))
    if current_size + estimated_size > CHUNK_SIZE_BYTES and current_chunk:
        chunks.append(current_chunk)
        current_chunk = []
        current_size = 0
    current_chunk.append(activity)
    current_size += estimated_size

if current_chunk:
    chunks.append(current_chunk)

print(f"Split into {len(chunks)} chunks")

# Write chunk files
chunk_filenames = []
for i, chunk in enumerate(chunks):
    filename = f"heatmap_{i+1}.json"
    filepath = f"docs/{filename}"
    with open(filepath, "w") as f:
        json.dump(chunk, f)
    size_mb = os.path.getsize(filepath) / 1024 / 1024
    print(f"  ✅ {filename}: {len(chunk)} activities, {size_mb:.1f}MB")
    chunk_filenames.append(filename)

# Write manifest
manifest = {"chunks": chunk_filenames}
with open("docs/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
print(f"\n✅ manifest.json written with {len(chunk_filenames)} chunks")

# Remove old heatmap.json if it exists
if os.path.exists("docs/heatmap.json"):
    os.remove("docs/heatmap.json")
    print("🗑 Removed old heatmap.json")

print("\n✅ Chunking complete!")
