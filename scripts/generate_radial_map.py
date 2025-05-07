import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re
import os

# Load data
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")

# Filter out 'Advanced Career'
df = df[df["Career_Level"] != "Advanced Career"]

# Normalize position category names
def normalize_name(name):
    name = str(name).lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return name.replace(' ', '_')

df["Normalized_Category"] = df["Position_Category"].apply(normalize_name)

# Map career level to radial positions
career_map = {"Early Career": 1, "Established Career": 2}
df["Radius"] = df["Career_Level"].map(career_map)

# Assign angular range for each domain
quadrant_angles = {
    "Health Classification": (0, 90),
    "Health Information Management": (90, 180),
    "Health Informatics": (180, 270),
    "Health Data Analysis": (270, 360)
}

# Assign theta angles per domain-category-career_level
angle_lookup = {}
for domain, (start, end) in quadrant_angles.items():
    domain_data = df[df["Domain"] == domain]
    combinations = sorted(domain_data[["Position_Category", "Career_Level"]].drop_duplicates().values.tolist())
    step = (end - start) / max(len(combinations), 1)
    for i, (cat, level) in enumerate(combinations):
        angle_lookup[(domain, cat, level)] = start + step / 2 + i * step

df["Theta"] = df.apply(lambda row: angle_lookup.get((row["Domain"], row["Position_Category"], row["Career_Level"]), 0), axis=1)

# Count frequency per unique dot (Domain + Category + Career Level)
freq_df = (
    df.groupby(["Position_Category", "Career_Level", "Domain"])
    .agg(Frequency=("ID_No", "count"))
    .reset_index()
)
freq_df["Normalized_Category"] = freq_df["Position_Category"].apply(normalize_name)
freq_df["Radius"] = freq_df["Career_Level"].map(career_map)
freq_df["Theta"] = freq_df.apply(lambda row: angle_lookup.get((row["Domain"], row["Position_Category"], row["Career_Level"]), 0), axis=1)

# Plot radial map
fig = go.Figure()

domain_colors = {
    "Health Classification": "#EF553B",
    "Health Information Management": "#00CC96",
    "Health Informatics": "#AB63FA",
    "Health Data Analysis": "#FFA15A"
}

for _, row in freq_df.iterrows():
    link = f"categories/{row['Normalized_Category']}.html"
    custom = f"{row['Domain']}||{row['Position_Category']}||{row['Career_Level']}||{link}"
    fig.add_trace(go.Scatterpolar(
        r=[row["Radius"]],
        theta=[row["Theta"]],
        mode="markers",
        marker=dict(
            size=8 + row["Frequency"] * 2,
            color=domain_colors.get(row["Domain"], "#636efa"),
            line=dict(color="#000000", width=1.2),
            opacity=0.95
        ),
        hovertext=f"{row['Position_Category']} ({row['Domain']}, {row['Career_Level']})",
        hoverinfo="text",
        customdata=[[custom]],
        name=""
    ))

# Connect dots with same ID_No and same category/career level but across domains
shared_ids = (
    df.groupby("ID_No")
    .filter(lambda g: g[["Position_Category", "Career_Level"]].nunique().eq(1).all() and g["Domain"].nunique() > 1)
)

for _, group in shared_ids.groupby("ID_No"):
    grouped = group.sort_values("Domain")
    r_vals = grouped["Radius"].tolist()
    theta_vals = grouped["Theta"].tolist()
    if len(r_vals) > 1:
        fig.add_trace(go.Scatterpolar(
            r=r_vals,
            theta=theta_vals,
            mode="lines",
            line=dict(color="white", width=1.1, dash="dot"),
            opacity=0.45,
            hoverinfo="none",
            showlegend=False
        ))

# Layout
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

# Embed radial map into index.html
chart_html = fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="map-container")
template_path = "../template/index_template.html"
with open(template_path, "r", encoding="utf-8") as f:
    base_template = f.read()

final_output = base_template.replace("<!--RADIAL_MAP-->", chart_html)
output_path = "../index.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(final_output)
print(f"\u2705 Radial map embedded and saved to: {output_path}")
