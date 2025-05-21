import pandas as pd
import json
import os

# Load the dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")

# Sort data by ID and Position_No (to preserve career path order)
df_sorted = df.sort_values(by=["ID_No", "Position_No"])

# Filter only necessary columns
paths = df_sorted[["ID_No", "Position_Category"]]

# Group by ID and extract the list of transitions
career_paths = paths.groupby("ID_No")["Position_Category"].apply(list)

# Initialize link structure
links = {}
for path in career_paths:
    for i in range(len(path) - 1):
        source = path[i].strip()
        target = path[i + 1].strip()
        if source != target:  # skip if same position repeated
            key = (source, target)
            links[key] = links.get(key, 0) + 1

# Prepare nodes and links for Sankey
all_nodes = sorted(set([n for pair in links for n in pair]))
node_index = {name: i for i, name in enumerate(all_nodes)}

sankey_json = {
    "nodes": [{"name": name} for name in all_nodes],
    "links": [
        {"source": node_index[src], "target": node_index[tgt], "value": count}
        for (src, tgt), count in links.items()
    ]
}

# Save to JSON
output_path = "../data/sankey_data.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(sankey_json, f, indent=2)

print("✅ Sankey data generated and saved to data/sankey_data.json")
