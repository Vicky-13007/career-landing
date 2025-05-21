import pandas as pd
import json
import os

# Load the dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")

# Validate necessary columns
required_cols = {"ID_No", "Position_No", "Position_Category"}
if not required_cols.issubset(df.columns):
    raise ValueError(f"Dataset must contain columns: {required_cols}")

# Drop duplicates to avoid reshaping issues
df = df.drop_duplicates(subset=["ID_No", "Position_No"])

# Pivot to wide format with ordered columns
wide = df.pivot(index="ID_No", columns="Position_No", values="Position_Category")
wide = wide[["Position_1", "Position_2", "Position_3"]]  # ensure order

# Melt to get transitions
paths = []
for col1, col2 in zip(wide.columns, wide.columns[1:]):
    chunk = wide[[col1, col2]].dropna()
    chunk.columns = ["source", "target"]
    paths.append(chunk)

edges = pd.concat(paths)

# Count frequency of each transition
flow = edges.value_counts().reset_index(name="count")

# Unique nodes
nodes = pd.Series(pd.unique(flow[["source", "target"]].values.ravel())).reset_index()
nodes.columns = ["id", "label"]

# Build name to index map
name_to_id = {name: i for i, name in enumerate(nodes["label"])}

# Build Sankey JSON structure
sankey = {
    "nodes": [{"name": name} for name in nodes["label"]],
    "links": [
        {
            "source": name_to_id[src],
            "target": name_to_id[tgt],
            "value": int(val)
        }
        for src, tgt, val in flow.itertuples(index=False)
    ]
}

# Output path
out_path = "../data/sankey_data.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(sankey, f, indent=2)

print(f"✅ Sankey data saved to {out_path}")
