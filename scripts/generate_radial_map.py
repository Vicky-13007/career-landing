import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re
import os

# Load CSV
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")

# Exclude Advanced Career
df = df[df["Career_Level"] != "Advanced Career"]

# Normalize for filenames
def normalize_name(name):
    name = str(name).lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return name.replace(' ', '_')

df["Normalized_Category"] = df["Position_Category"].apply(normalize_name)

# Map career level to rings
career_map = {"Early Career": 1, "Established Career": 2}
df["Radius"] = df["Career_Level"].map(career_map)

# Quadrant angular setup
quadrant_angles = {
    "Health Classification": (0, 90),
    "Health Information Management": (90, 180),
    "Health Informatics": (180, 270),
    "Health Data Analysis": (270, 360)
}

# Assign angles per domain-category
angle_lookup = {}
for domain, (start, end) in quadrant_angles.items():
    domain_data = df[df["Domain"] == domain]
    categories = sorted(domain_data["Position_Category"].dropna().unique())
    step = (end - start) / max(len(categories), 1)
    for i, cat in enumerate(categories):
        angle_lookup[(domain, cat)] = start + step / 2 + i * step

df["Theta"] = df.apply(lambda row: angle_lookup.get((row["Domain"], row["Position_Category"]), 0), axis=1)

# Frequency calculation
df["Frequency"] = df.groupby(["Domain", "Position_Category"])["Position_Category"].transform("count")

# Drop duplicates 
df = df.sort_values("Frequency", ascending=False).drop_duplicates(subset=["Domain", "Position_Category"])

# Top 10 categories per domain
top_categories = df.groupby("Domain").head(10)

# Plot
fig = go.Figure()

domain_colors = {
    "Health Classification": "#EF553B",
    "Health Information Management": "#00CC96",
    "Health Informatics": "#AB63FA",
    "Health Data Analysis": "#FFA15A"
}

for _, row in top_categories.iterrows():
    link = f"categories/{row['Normalized_Category']}.html"
    fig.add_trace(go.Scatterpolar(
        r=[row["Radius"]],
        theta=[row["Theta"]],
        mode="markers",
        marker=dict(
            size=14,
            color=domain_colors.get(row["Domain"], "#636efa"),
            line=dict(color="#000000", width=1.2),
            opacity=0.95
        ),
        hovertext=row["Position_Category"],
        hoverinfo="text",
        customdata=[link],
        name=""
    ))

# Add connecting lines for categories shared across domains
shared = top_categories.groupby("Position_Category").filter(lambda g: len(g["Domain"].unique()) > 1)

for category, group in shared.groupby("Position_Category"):
    r_vals = group["Radius"].tolist()
    theta_vals = group["Theta"].tolist()
    if len(r_vals) > 1:
        paired = sorted(zip(theta_vals, r_vals))
        theta_sorted, r_sorted = zip(*paired)
        fig.add_trace(go.Scatterpolar(
            r=r_sorted,
            theta=theta_sorted,
            mode="lines",
            line=dict(color="white", width=1.2, dash="dot"),
            opacity=0.5,
            hoverinfo="none",
            showlegend=False
        ))

fig.update_layout(
    title="Top Position Categories Across Health Career Domains",
    polar=dict(
        bgcolor="#000000",
        radialaxis=dict(
            visible=True,
            tickvals=[1, 2],
            ticktext=["Early Career", "Established Career"],
            range=[0.5, 2.5],
            gridcolor="#555555",
            gridwidth=1.3,
            showline=False,
            tickfont=dict(color="#FFFFFF")
        ),
        angularaxis=dict(
            tickvals=[45, 135, 225, 315],
            ticktext=list(quadrant_angles.keys()),
            direction="clockwise",
            rotation=90,
            gridcolor="#777777",
            gridwidth=1.3,
            tickfont=dict(color="#FFFFFF")
        )
    ),
    paper_bgcolor="#000000",
    font=dict(color="#FFFFFF"),
    showlegend=False,
    width=1000,
    height=1000
)

# Save HTML
html_path = "../index.html"
fig.write_html(html_path, include_plotlyjs="cdn", full_html=True)

# Add working click handler using Plotly's native event system
with open(html_path, "r") as f:
    content = f.read()

content = content.replace(
    "<body>",
    """<body>
<script>
document.addEventListener(\"DOMContentLoaded\", function() {
  var plot = document.querySelector('.js-plotly-plot');
  if (plot) {
    plot.on('plotly_click', function(data) {
      const point = data.points[0];
      const url = point.customdata;
      if (url) window.open(url, '_blank');
    });
  }
});
</script>"""
)

with open(html_path, "w") as f:
    f.write(content)

print(f"\u2705 Radial map with working click events saved to: {html_path}")

# Generate category HTML pages
category_dir = os.path.join(os.path.dirname(__file__), "..", "categories")
os.makedirs(category_dir, exist_ok=True)

unique_categories = top_categories["Position_Category"].unique()
normalized_map = {cat: normalize_name(cat) for cat in unique_categories}

def generate_html(category_name):
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>{category_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 2rem;
            background-color: #ffffff;
            color: #333333;
        }}
        h1 {{
            color: #2c3e50;
        }}
        p {{
            font-size: 1.1rem;
        }}
    </style>
</head>
<body>
    <h1>{category_name}</h1>
    <p>This page will include detailed information about the <strong>{category_name}</strong> category.</p>
    <p>You can describe example job roles, required skills, career progression, and domain-specific insights here.</p>
</body>
</html>"""

for original, normalized in normalized_map.items():
    html = generate_html(original)
    file_path = os.path.join(category_dir, f"{normalized}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

print(f"\u2705 Generated {len(unique_categories)} category pages in: {category_dir}")
