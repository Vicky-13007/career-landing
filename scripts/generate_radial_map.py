import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re

# Load dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")

# Normalize titles for URLs
def normalize_title(title):
    title = str(title).lower().strip()
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'[^a-z0-9\s]', '', title)
    return title.replace(' ', '_')

df["Normalized_Title"] = df["Position_Title"].apply(normalize_title)

# Map Career Levels
career_map = {"Early Career": 1, "Established Career": 2, "Advanced Career": 3}
df["Radius"] = df["Career_Level"].map(career_map)

# Quadrant angle setup
quadrant_angles = {
    "Health Classification": (0, 90),
    "Health Information Management": (90, 180),
    "Health Informatics": (180, 270),
    "Health Data Analysis": (270, 360)
}

# Assign unique angle per domain-category
angle_lookup = {}
for domain, (start, end) in quadrant_angles.items():
    domain_data = df[df["Domain"] == domain]
    categories = sorted(domain_data["Position_Category"].dropna().unique())
    step = (end - start) / max(len(categories), 1)
    for i, cat in enumerate(categories):
        angle_lookup[(domain, cat)] = start + step / 2 + i * step

df["Theta"] = df.apply(lambda row: angle_lookup.get((row["Domain"], row["Position_Category"]), 0), axis=1)

# Frequency of roles per domain
role_counts = df.groupby(["Domain", "Position_Title"]).size().reset_index(name="Frequency")

# Keep top 10 roles per domain
top_roles = role_counts.groupby("Domain").apply(lambda g: g.nlargest(10, "Frequency")).reset_index(drop=True)

# Merge to get full details
df_unique = df.drop_duplicates(subset=["Domain", "Position_Title"])
merged = pd.merge(top_roles, df_unique, on=["Domain", "Position_Title"], how="left")

# Aggregate
agg_df = merged[[
    "Domain", "Position_Category", "Normalized_Title", "Position_Title", "Career_Level", "Radius", "Theta", "Frequency"
]]

# Plotly Radial Plot
fig = go.Figure()

# Color by domain
domain_colors = {
    "Health Classification": "#EF553B",
    "Health Information Management": "#00CC96",
    "Health Informatics": "#AB63FA",
    "Health Data Analysis": "#FFA15A"
}

for _, row in agg_df.iterrows():
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
    title="Explore Health Career Domains (Top 10 Roles per Domain)",
    polar=dict(
        bgcolor="#f9f9f9",
        radialaxis=dict(
            visible=True,
            tickvals=[1, 2, 3],
            ticktext=["Early Career", "Established Career", "Advanced Career"],
            range=[0.5, 3.5],
            gridcolor="#d3d3d3"
        ),
        angularaxis=dict(
            tickvals=[45, 135, 225, 315],
            ticktext=list(quadrant_angles.keys()),
            direction="clockwise",
            rotation=90,
            gridcolor="#e1e1e1"
        )
    ),
    paper_bgcolor="#ffffff",
    showlegend=False,
    width=1000,
    height=1000,
    font=dict(size=13)
)

# Save output
output_path = "../index.html"
fig.write_html(output_path)
print(f"✔️ Map saved to {output_path}")
