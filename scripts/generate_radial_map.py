import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re

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
        angle_lookup[(domain, cat)] = start + step/2 + i * step

df["Theta"] = df.apply(lambda row: angle_lookup.get((row["Domain"], row["Position_Category"]), 0), axis=1)

# Frequency calculation
df["Frequency"] = df.groupby(["Domain", "Position_Category"])["Position_Category"].transform("count")

# Drop duplicates — one per domain-category
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

fig.update_layout(
    title="Top Position Categories Across Health Career Domains",
    polar=dict(
        bgcolor="#000000",  # black for better contrast
        radialaxis=dict(
            visible=True,
            tickvals=[1, 2],
            ticktext=["Early Career", "Established Career"],
            range=[0.5, 2.5],
            gridcolor="#a3a3a3",  # darker radial ring lines
            gridwidth=1.5,
            linecolor="#333333",
            linewidth=1
        ),
        angularaxis=dict(
            tickvals=[45, 135, 225, 315],
            ticktext=list(quadrant_angles.keys()),
            direction="clockwise",
            rotation=90,
            gridcolor="#a3a3a3",  # darker quadrant lines
            gridwidth=1.5,
            linecolor="#333333",
            linewidth=1
        )
    ),
    paper_bgcolor="#ffffff",
    showlegend=False,
    width=1000,
    height=1000,
    font=dict(size=13)
)


# Save HTML
html_path = "../index.html"
fig.write_html(html_path, include_plotlyjs="cdn", full_html=True)

# Add click-to-navigate JS
with open(html_path, "r") as f:
    content = f.read()

content = content.replace(
    "<body>",
    """<body>
<script>
document.querySelectorAll('g.scatterlayer .trace').forEach(trace => {
  trace.addEventListener('click', function(evt) {
    const target = evt.target.closest('[data-unformatted]');
    if (target && target.__data__ && target.__data__.customdata) {
      const url = target.__data__.customdata;
      if (url) window.open(url, "_blank");
    }
  });
});
</script>"""
)

with open(html_path, "w") as f:
    f.write(content)

print(f"✔️ Clean clickable category map saved to {html_path}")
