import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re

# Load your dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")

# Normalize titles for safe HTML links
def normalize_title(title):
    title = str(title).lower().strip()
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'[^a-z0-9\s]', '', title)
    return title.replace(' ', '_')

df["Normalized_Title"] = df["Position_Title"].apply(normalize_title)

# Map career levels to rings
career_map = {"Early Career": 1, "Established Career": 2, "Advanced Career": 3}
df["Radius"] = df["Career_Level"].map(career_map)

# Define quadrant angular range
quadrant_angles = {
    "Health Classification": (0, 90),
    "Health Information Management": (90, 180),
    "Health Informatics": (180, 270),
    "Health Data Analysis": (270, 360)
}

# Map each domain-category to a unique angle
angle_lookup = {}
for domain, (start_angle, end_angle) in quadrant_angles.items():
    domain_data = df[df["Domain"] == domain]
    categories = sorted(domain_data["Position_Category"].dropna().unique())
    step = (end_angle - start_angle) / max(len(categories), 1)
    for i, cat in enumerate(categories):
        angle_lookup[(domain, cat)] = start_angle + step / 2 + i * step

df["Theta"] = df.apply(lambda row: angle_lookup.get((row["Domain"], row["Position_Category"]), 0), axis=1)

# Keep only top 10 roles per domain by frequency
df["Frequency"] = df.groupby("Normalized_Title")["Normalized_Title"].transform("count")
df_top = df.sort_values("Frequency", ascending=False).groupby("Domain").head(10)

# Aggregate
agg_df = df_top.groupby(
    ["Domain", "Position_Category", "Normalized_Title", "Position_Title", "Career_Level", "Radius", "Theta"]
).size().reset_index(name="Frequency")

# Plot
fig = go.Figure()

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
    title="Explore Health Career Domains (AHIMA-style Radial Map)",
    polar=dict(
        bgcolor="#f9f9f9",
        radialaxis=dict(
            visible=True,
            tickvals=[1, 2, 3],
            ticktext=["Early Career", "Established Career", "Advanced Career"],
            range=[0.5, 3.5],
            showline=False,
            linewidth=1,
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
    plot_bgcolor="#ffffff",
    showlegend=False,
    width=1000,
    height=1000,
    font=dict(size=13)
)

# Save HTML
output_path = "../index.html"
fig.write_html(output_path)
print(f"✔️ Radial map saved to {output_path}")
