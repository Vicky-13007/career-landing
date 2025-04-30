import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re

# Load dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")

# Step 1: Filter out "Advanced Career"
df = df[df["Career_Level"] != "Advanced Career"]

# Normalize titles for URLs
def normalize_title(title):
    title = str(title).lower().strip()
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'[^a-z0-9\s]', '', title)
    return title.replace(' ', '_')

df["Normalized_Title"] = df["Position_Title"].apply(normalize_title)

# Career ring mapping
career_map = {"Early Career": 1, "Established Career": 2}
df["Radius"] = df["Career_Level"].map(career_map)

# Define quadrant angular range
quadrant_angles = {
    "Health Classification": (0, 90),
    "Health Information Management": (90, 180),
    "Health Informatics": (180, 270),
    "Health Data Analysis": (270, 360)
}

# Assign angle by domain-category
angle_lookup = {}
for domain, (start, end) in quadrant_angles.items():
    domain_data = df[df["Domain"] == domain]
    categories = sorted(domain_data["Position_Category"].dropna().unique())
    step = (end - start) / max(len(categories), 1)
    for i, cat in enumerate(categories):
        angle_lookup[(domain, cat)] = start + step / 2 + i * step

df["Theta"] = df.apply(lambda row: angle_lookup.get((row["Domain"], row["Position_Category"]), 0), axis=1)

# Compute frequency per domain-role
df["Frequency"] = df.groupby(["Domain", "Position_Title"])["Position_Title"].transform("count")

# Drop duplicate entries for same role per domain (keep max freq)
df = df.sort_values("Frequency", ascending=False).drop_duplicates(subset=["Domain", "Position_Title"])

# Select top 10 unique roles per domain
top_roles = df.groupby("Domain").head(10)

# Prepare plot
fig = go.Figure()

domain_colors = {
    "Health Classification": "#EF553B",
    "Health Information Management": "#00CC96",
    "Health Informatics": "#AB63FA",
    "Health Data Analysis": "#FFA15A"
}

for _, row in top_roles.iterrows():
    link = f"roles/{row['Normalized_Title']}.html"
    fig.add_trace(go.Scatterpolar(
        r=[row["Radius"]],
        theta=[row["Theta"]],
        mode="markers",
        marker=dict(
            size=6 + 6 * np.log1p(row["Frequency"]),
            color=domain_colors.get(row["Domain"], "#636efa"),
            line=dict(color="#000000", width=1.5),
            opacity=0.9
        ),
        hovertemplate=(
            f"<b>{row['Position_Title']}</b><br>"
            f"Category: {row['Position_Category']}<br>"
            f"Level: {row['Career_Level']}<br>"
            f"Frequency: {row['Frequency']}<br>"
            f"<a href='{link}' target='_blank'>View Role</a><extra></extra>"
        )
    ))

fig.update_layout(
    title="Explore Health Career Domains (Top 10 Unique Roles per Domain)",
    polar=dict(
        radialaxis=dict(
            visible=True,
            tickvals=[1, 2],
            ticktext=["Early Career", "Established Career"],
            range=[0.5, 2.5],
            gridcolor="#d3d3d3"
        ),
        angularaxis=dict(
            tickvals=[45, 135, 225, 315],
            ticktext=list(quadrant_angles.keys()),
            direction="clockwise",
            rotation=90,
            gridcolor="#e1e1e1"
        ),
        bgcolor="#f9f9f9"
    ),
    paper_bgcolor="#ffffff",
    showlegend=False,
    width=1000,
    height=1000,
    font=dict(size=13)
)

# Save file
output_path = "../index.html"
fig.write_html(output_path)
print(f"✔️ Radial map saved to {output_path}")
