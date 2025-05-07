# Revised radial map generator to:
# - Plot each (Position_Category + Career_Level + Domain) combo as a dot
# - Size each dot by the count of unique ID_No
# - Link dots (dashed lines) if same ID_No appears in multiple domains for the same category + level

import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re
import os

# Load and clean data
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")
df = df[df["Career_Level"] != "Advanced Career"]

# Normalize names for URLs
def normalize_name(name):
    name = str(name).lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return name.replace(' ', '_')

df["Normalized_Category"] = df["Position_Category"].apply(normalize_name)
career_map = {"Early Career": 1, "Established Career": 2}
df["Radius"] = df["Career_Level"].map(career_map)

quadrant_angles = {
    "Health Classification": (0, 90),
    "Health Information Management": (90, 180),
    "Health Informatics": (180, 270),
    "Health Data Analysis": (270, 360)
}

# Assign angle by domain/category
angle_lookup = {}
for domain, (start, end) in quadrant_angles.items():
    domain_data = df[df["Domain"] == domain]
    cats = sorted(domain_data["Position_Category"].dropna().unique())
    step = (end - start) / max(len(cats), 1)
    for i, cat in enumerate(cats):
        angle_lookup[(domain, cat)] = start + step/2 + i*step

df["Theta"] = df.apply(lambda row: angle_lookup.get((row["Domain"], row["Position_Category"]), 0), axis=1)

# Frequency by unique ID_No count
dot_data = df.groupby(["Domain", "Position_Category", "Career_Level", "Normalized_Category", "Radius", "Theta"]) \
             .agg(ID_Count=("ID_No", pd.Series.nunique)).reset_index()

# Plot
fig = go.Figure()
domain_colors = {
    "Health Classification": "#EF553B",
    "Health Information Management": "#00CC96",
    "Health Informatics": "#AB63FA",
    "Health Data Analysis": "#FFA15A"
}

for _, row in dot_data.iterrows():
    link = f"categories/{row['Normalized_Category']}.html"
    fig.add_trace(go.Scatterpolar(
        r=[row["Radius"]],
        theta=[row["Theta"]],
        mode="markers",
        marker=dict(
            size=6 + row["ID_Count"] * 2,
            color=domain_colors.get(row["Domain"], "#636efa"),
            line=dict(color="#000000", width=1.2),
            opacity=0.95
        ),
        hovertext=row["Position_Category"],
        hoverinfo="text",
        customdata=[link],
        name=""
    ))

# Connecting same ID_No across domains
pairs = df.groupby("ID_No")
for _, group in pairs:
    if group.shape[0] > 1:
        unique_roles = group.groupby(["Position_Category", "Career_Level"])
        for _, role_grp in unique_roles:
            if len(role_grp["Domain"].unique()) > 1:
                coords = role_grp.drop_duplicates(subset=["Domain"])[["Radius", "Theta"]].values.tolist()
                if len(coords) > 1:
                    coords.sort(key=lambda x: x[1])
                    r_vals, theta_vals = zip(*coords)
                    fig.add_trace(go.Scatterpolar(
                        r=r_vals,
                        theta=theta_vals,
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

# Inject into HTML
chart_html = fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="map-container")
with open("../template/index_template.html", "r", encoding="utf-8") as f:
    base_template = f.read()
final_output = base_template.replace("<!--RADIAL_MAP-->", chart_html)
with open("../index.html", "w", encoding="utf-8") as f:
    f.write(final_output)
print("✅ Radial map generated and saved to: ../index.html")
