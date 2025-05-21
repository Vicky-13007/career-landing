import pandas as pd
import json
import os

# Load the dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")

# Sort by ID and Career_Level (if available)
if "Career_Level" in df.columns:
    level_order = {"Early Career": 0, "Established Career": 1, "Advanced Career": 2}
    df["level_order"] = df["Career_Level"].map(level_order)
    df = df.sort_values(by=["ID_No", "level_order"])
else:
    df = df.sort_values(by=["ID_No"])

# Group by ID and get sequential transitions
all_paths = df.groupby("ID_No")["Position_Category"].apply(list)

# Count transitions
transition_counts = {}
for path in all_paths:
    for i in range(len(path) - 1):
        src = path[i]
        tgt = path[i+1]
        key = (src, tgt)
        transition_counts[key] = transition_counts.get(key, 0) + 1

# Map positions to node indices
positions = sorted(set([pos for pair in transition_counts for pos in pair]))
position_to_idx = {pos: i for i, pos in enumerate(positions)}

# Construct Sankey data
sankey_data = {
    "nodes": positions,
    "links": [
        {"source": position_to_idx[src], "target": position_to_idx[tgt], "value": count}
        for (src, tgt), count in transition_counts.items()
    ]
}

# Save as JSON
os.makedirs("../data", exist_ok=True)
with open("../data/sankey_data.json", "w", encoding="utf-8") as f:
    json.dump(sankey_data, f, indent=2)

print("Sankey data saved to data/sankey_data.json")
