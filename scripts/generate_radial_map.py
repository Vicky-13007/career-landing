import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re
import os

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

# Assign fixed angle for each unique Position_Category
unique_cats = sorted(df["Position_Category"].unique())
angle_step = 360 / len(unique_cats)
cat_angle_map = {cat: i * angle_step for i, cat in enumerate(unique_cats)}

# Assign all dots same radius to spread evenly
df["Theta"] = df["Position_Category"].map(cat_angle_map)
df["Radius"] = 1.5

# Aggregate frequency
agg = df.groupby("Position_Category").agg(
    Frequency=("ID_No", "nunique")
).reset_index()
agg["Normalized_Category"] = agg["Position_Category"].apply(normalize_name)
agg["Theta"] = agg["Position_Category"].map(cat_angle_map)
agg["Radius"] = 1.5

# Plot
fig = go.Figure()
color = "#636efa"

for _, row in agg.iterrows():
    link = f"categories/{row['Normalized_Category']}.html"
    fig.add_trace(go.Scatterpolar(
        r=[row["Radius"]],
        theta=[row["Theta"]],
        mode="markers",
        marker=dict(
            size=8 + row["Frequency"] * 2,
            color=color,
            line=dict(color="#000", width=1.2),
            opacity=0.92
        ),
        hovertext=f"{row['Position_Category']} (Total: {row['Frequency']})",
        hoverinfo="text",
        customdata=[[row["Position_Category"], link]],
        name=""
    ))

# Layout
fig.update_layout(
    title="Top Position Categories Across Health Career Domains",
    polar=dict(
        bgcolor="#000000",
        radialaxis=dict(
            visible=False,
            range=[0, 2]
        ),
        angularaxis=dict(
            visible=True,
            tickvals=list(cat_angle_map.values()),
            ticktext=list(cat_angle_map.keys()),
            tickfont=dict(size=10, color="#FFFFFF")
        )
    ),
    paper_bgcolor="#000000",
    font=dict(color="#FFFFFF"),
    showlegend=False,
    width=950,
    height=950
)

# Embed radial map
chart_html = fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="map-container")
template_path = "../template/index_template.html"
with open(template_path, "r", encoding="utf-8") as f:
    template = f.read()

final = template.replace("<!--RADIAL_MAP-->", chart_html)
with open("../index.html", "w", encoding="utf-8") as f:
    f.write(final)

print("✅ Radial map updated.")

# Generate HTML role pages
out_dir = os.path.join(os.path.dirname(__file__), "..", "categories")
os.makedirs(out_dir, exist_ok=True)

grouped = (
    df.groupby(["Position_Category", "Career_Level", "Domain"])
    .agg(Frequency=("ID_No", "count"))
    .reset_index()
)
grouped["Normalized_Category"] = grouped["Position_Category"].apply(normalize_name)

for cat in grouped["Normalized_Category"].unique():
    sub = grouped[grouped["Normalized_Category"] == cat]
    display_name = sub["Position_Category"].iloc[0]

    rows = ""
    for _, r in sub.iterrows():
        rows += f"<li>{r['Domain']} - {r['Career_Level']} → {r['Frequency']}</li>\n"

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <title>{display_name}</title>
  <style>
    body {{ font-family: Arial; padding: 2rem; background: #fff; color: #333; }}
    h1 {{ color: #2c3e50; }}
    ul {{ margin-top: 1rem; }}
  </style>
</head>
<body>
  <h1>{display_name}</h1>
  <p>This page includes detailed data combinations for the <strong>{display_name}</strong> category.</p>
  <hr>
  <h3>Stats (by Domain and Career Level):</h3>
  <ul>{rows}</ul>
</body>
</html>
"""
    with open(os.path.join(out_dir, f"{cat}.html"), "w", encoding="utf-8") as f:
        f.write(html)

print("✅ Role-specific HTML pages updated.")
