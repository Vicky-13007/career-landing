import pandas as pd
import json

# Load the dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")
df.columns = df.columns.str.strip()

# Drop duplicates safely
df = df.drop_duplicates(subset=["ID_No", "Position_No"], keep="first")

# Pivot into wide format: ID_No → Position_1, Position_2, Position_3
pivoted = df.pivot(index="ID_No", columns="Position_No", values="Position_Category").reset_index()

# Remove rows with fewer than 2 valid positions
pivoted = pivoted.dropna(thresh=3)

# Build transitions (source → target)
pairs = []
for _, row in pivoted.iterrows():
    if pd.notna(row.get("Position_1")) and pd.notna(row.get("Position_2")):
        pairs.append((row["Position_1"], row["Position_2"]))
    if pd.notna(row.get("Position_2")) and pd.notna(row.get("Position_3")):
        pairs.append((row["Position_2"], row["Position_3"]))

# Count frequency of each source-target transition
transitions = pd.DataFrame(pairs, columns=["source", "target"])
sankey_data = transitions.value_counts().reset_index(name="value")

# Create unique node list
nodes = pd.Series(pd.unique(sankey_data[["source", "target"]].values.ravel()))
node_map = {name: i for i, name in enumerate(nodes)}

# Replace node names with indices for links
sankey_data["source"] = sankey_data["source"].map(node_map)
sankey_data["target"] = sankey_data["target"].map(node_map)

# Build final JSON for Sankey diagram
sankey_json = {
    "nodes": [{"name": name} for name in nodes],
    "links": sankey_data.to_dict(orient="records")
}

# Save to file
with open("../data/sankey_data.json", "w") as f:
    json.dump(sankey_json, f, indent=2)

print("Sankey data generated and saved to data/sankey_data.json")
