import pandas as pd
import json
import os

# Load and clean
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")
df = df[["ID_No", "Position_No", "Position_Category", "Domain"]].dropna()
df = df.drop_duplicates(subset=["ID_No", "Position_No"], keep="first")

# Ensure Position_No has order
position_order = {"Position_1": 0, "Position_2": 1, "Position_3": 2}
df["order"] = df["Position_No"].map(position_order)
df = df.sort_values(by=["ID_No", "order"])

# Create career transitions
df["next_Position_Category"] = df.groupby("ID_No")["Position_Category"].shift(-1)

# Drop where next is NaN
df_links = df.dropna(subset=["next_Position_Category"])

# Count transitions
links = df_links.groupby(["Position_Category", "next_Position_Category"]).size().reset_index(name="value")

# Create list of all unique roles
all_roles = pd.unique(links[["Position_Category", "next_Position_Category"]].values.ravel())

# Map roles to indices
role_to_index = {role: i for i, role in enumerate(all_roles)}

# Optional: assign colors
import random
import colorsys
random.seed(42)
colors = [
    f"rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, 0.8)"
    for r, g, b in [colorsys.hsv_to_rgb(i/len(all_roles), 0.6, 0.9) for i in range(len(all_roles))]
]

# Build nodes and links
nodes = [{"name": role, "color": colors[i]} for i, role in enumerate(all_roles)]
sankey_links = {
    "source": [role_to_index[src] for src in links["Position_Category"]],
    "target": [role_to_index[tgt] for tgt in links["next_Position_Category"]],
    "value": links["value"].tolist(),
}

# Final sankey JSON
sankey_data = {
    "nodes": nodes,
    "links": sankey_links
}

# Output JSON
os.makedirs("../data", exist_ok=True)
with open("../data/sankey_data.json", "w", encoding="utf-8") as f:
    json.dump(sankey_data, f, indent=2)

print("Sankey data written to data/sankey_data.json")
