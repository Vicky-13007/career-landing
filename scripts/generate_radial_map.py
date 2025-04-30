import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re
import os

# Load your dataset
df = pd.read_csv("/Users/vignesshwarvenkatachalam/Downloads/career_landing/data/radial_data_split_domains_filtered.csv")

# Normalize title for file-safe linking
def normalize_title(title):
    title = str(title).lower().strip()
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'[^a-z0-9\s]', '', title)
    return title.replace(' ', '_')

df["Normalized_Title"] = df["Position_Title"].apply(normalize_title)

# Map career levels to rings
career_map = {"Early Career": 1, "Established Career": 2, "Advanced Career": 3}
df["Radius"] = df["Career_Level"].map(career_map)

# Define 4 quadrants by domain
quadrant_angles = {
    "Health Classification": (0, 90),
    "Health Information Management": (90, 180),
    "Health Informatics": (180, 270),
    "Health Data Analysis": (270, 360)
}

# Assign angle per domain-category combo
angle_lookup = {}
for domain, (start_angle, end_angle) in quadrant_angles.items():
    domain_data = df[df["Domain"] == domain]
    categories = sorted(domain_data["Position_Category"].dropna().unique())
    step = (end_angle - start_angle) / max(len(categories), 1)
    for i, cat in enumerate(categories):
        angle_lookup[(domain, cat)] = start_angle + step/2 + i * step

df["Theta"] = df.apply(lambda row: angle_lookup.get((row["Domain"], row["Position_Category"]), 0), axis=1)

# Group and count
agg_df = df.groupby(
    ["Domain", "Position_Category", "Normalized_Title", "Position_Title", "Career_Level", "Radius", "Theta"]
).size().reset_index(name="Frequency")

# Generate the radial map
fig = go.Figure()

for _, row in agg_df.iterrows():
    role_link = f"roles/{row['Normalized_Title']}.html"
    fig.add_trace(go.Scatterpolar(
        r=[row["Radius"]],
        theta=[row["Theta"]],
        mode='markers',
        marker=dict(
            size=5 + 5 * np.log1p(row["Frequency"]),
            color=row["Radius"],
            colorscale="Viridis",
            line=dict(color="white", width=1),
            opacity=0.95
        ),
        hovertemplate=(
            f"<b>{row['Position_Title']}</b><br>"
            f"Category: {row['Position_Category']}<br>"
            f"Level: {row['Career_Level']}<br>"
            f"Freq: {row['Frequency']}<br>"
            f"<a href='{role_link}' target='_blank'>View Role Page</a><extra></extra>"
        )
    ))

fig.update_layout(
    title="Explore Health Career Domains (AHIMA-style Radial Map)",
    polar=dict(
        radialaxis=dict(
            visible=True,
            tickvals=[1, 2, 3],
            ticktext=["Early Career", "Established Career", "Advanced Career"],
            range=[0.5, 3.5]
        ),
        angularaxis=dict(
            tickvals=[45, 135, 225, 315],
            ticktext=list(quadrant_angles.keys()),
            direction="clockwise",
            rotation=90
        )
    ),
    template="plotly_white",
    showlegend=False,
    width=950,
    height=950
)

# Save to output file (relative to scripts folder)
output_path = "/Users/vignesshwarvenkatachalam/Downloads/career_landing/index.html"
fig.write_html(output_path)

print(f"Radial map successfully saved to {output_path}")
