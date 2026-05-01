import json

with open("docs/heatmap.json") as f:
    data = json.load(f)

cleaned = [a for a in data if a.get("type") != "travel"]

with open("docs/heatmap.json", "w") as f:
    json.dump(cleaned, f)

print(f"Done. Removed travel entries. Remaining: {len(cleaned)} activities")
