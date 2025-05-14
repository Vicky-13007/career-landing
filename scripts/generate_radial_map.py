import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re
import os
import hashlib
from pathlib import Path

# Load data
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")
df = df[df["Career_Level"] != "Advanced Career"]

# Normalize category names for linking
def normalize_name(name):
    name = str(name).lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return name.replace(' ', '_')

df["Normalized_Category"] = df["Position_Category"].apply(normalize_name)

# Aggregate frequencies per category
agg = df.groupby("Position_Category").agg(
    Frequency=("ID_No", "nunique")
).reset_index()
agg["Normalized_Category"] = agg["Position_Category"].apply(normalize_name)

# Random spread for radial visual
np.random.seed(42)
agg["Theta"] = np.random.uniform(0, 360, len(agg))
agg["Radius"] = np.random.uniform(1.2, 2.2, len(agg))

# Unique color per category
def generate_color(name):
    hex_color = "#" + hashlib.md5(name.encode()).hexdigest()[:6]
    return hex_color

agg["Color"] = agg["Normalized_Category"].apply(generate_color)

# Plot radial map
fig = go.Figure()

for _, row in agg.iterrows():
    link = f"categories/{row['Normalized_Category']}.html"
    fig.add_trace(go.Scatterpolar(
        r=[row["Radius"]],
        theta=[row["Theta"]],
        mode="markers",
        marker=dict(
            size=8 + row["Frequency"] * 2,
            color=row["Color"],
            line=dict(color="#000", width=1.2),
            opacity=0.9
        ),
        hovertext=f"{row['Position_Category']} (Total: {row['Frequency']})",
        hoverinfo="text",
        customdata=[[row["Position_Category"], link]],
        name=""
    ))

fig.update_layout(
    title="Top Position Categories Across Health Career Domains",
    polar=dict(
        bgcolor="#000000",
        radialaxis=dict(visible=False, range=[0, 2.5]),
        angularaxis=dict(visible=False)
    ),
    paper_bgcolor="#000000",
    font=dict(color="#FFFFFF"),
    showlegend=False,
    width=950,
    height=950
)

# Embed chart into HTML
chart_html = fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="map-container")
with open("../template/index_template.html", "r", encoding="utf-8") as f:
    base = f.read()
html_out = base.replace("<!--RADIAL_MAP-->", chart_html)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_out)
print("✅ index.html generated.")

# Create individual role pages
output_dir = "categories"
os.makedirs(output_dir, exist_ok=True)
summary = df.groupby(["Position_Category", "Career_Level", "Domain"]).agg(Frequency=("ID_No", "count")).reset_index()
summary["Normalized_Category"] = summary["Position_Category"].apply(normalize_name)

for cat in summary["Normalized_Category"].unique():
    sub = summary[summary["Normalized_Category"] == cat]
    original_name = sub["Position_Category"].iloc[0]
    details = "\n".join(f"<li>{row['Domain']} - {row['Career_Level']} → {row['Frequency']}</li>" for _, row in sub.iterrows())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{original_name}</title>
  <style>
    body {{ font-family: Arial; padding: 2rem; background: #fff; color: #333; }}
    h1 {{ color: #2c3e50; }}
    ul {{ margin-top: 1rem; }}
  </style>
</head>
<body>
  <h1>{original_name}</h1>
  <p>This page includes detailed data combinations for the <strong>{original_name}</strong> category.</p>
  <hr>
  <h3>Stats (by Domain and Career Level):</h3>
  <ul>{details}</ul>
</body>
</html>
"""
    with open(f"{output_dir}/{cat}.html", "w", encoding="utf-8") as f:
        f.write(html)

print("✅ Category pages written to /categories/")
