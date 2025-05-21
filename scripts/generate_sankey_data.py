import pandas as pd
import json
from collections import Counter
import os

# Load dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")
df = df.dropna(subset=["ID_No", "Position_Title", "Position_No"])

# Extract numeric order from "Position_No"
df["Position_No"] = df["Position_No"].str.extract(r'(\d+)').astype(int)

# Sort data for each respondent
df = df.sort_values(by=["ID_No", "Position_No"])

# Build unique role list and index map
all_roles = sorted(df["Position_Title"].dropna().unique())
node_index = {role: idx for idx, role in enumerate(all_roles)}

# Create links between career transitions
links = []
for _, group in df.groupby("ID_No"):
    group = group.sort_values(by="Position_No")
    positions = group["Position_Title"].tolist()
    for i in range(len(positions) - 1):
        source = node_index[positions[i]]
        target = node_index[positions[i + 1]]
        links.append((source, target))

# Count transitions
link_counts = Counter(links)

# Construct Sankey nodes and links
nodes = [{"name": role} for role in all_roles]
links_data = [{"source": s, "target": t, "value": v} for (s, t), v in link_counts.items()]
sankey_data = {"nodes": nodes, "links": links_data}

# Save output
output_path = "../data/sankey_data.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(sankey_data, f, indent=2)

print("✅ sankey_data.json generated at: data/sankey_data.json")
