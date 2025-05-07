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

# Assign angles to each domain-category pair
angle_lookup = {}
for domain, (start, end) in quadrant_angles.items():
    domain_data = df[df["Domain"] == domain]
    categories = sorted(domain_data["Position_Category"].dropna().unique())
    step = (end - start) / max(len(categories), 1)
    for i, cat in enumerate(categories):
        angle_lookup[(domain, cat)] = start + step / 2 + i * step

df["Theta"] = df.apply(lambda row: angle_lookup.get((row["Domain"], row["Position_Category"]), 0), axis=1)

# Get frequency per unique dot (domain + category + level)
dot_counts = (
    df.groupby(["Position_Category", "Domain", "Career_Level"])
    .agg(
        Frequency=("ID_No", "count"),
        Record_IDs=("ID_No", list)
    )
    .reset_index()
)

dot_counts["Normalized_Category"] = dot_counts["Position_Category"].apply(normalize_name)
dot_counts["Radius"] = dot_counts["Career_Level"].map(career_map)
dot_counts["Theta"] = dot_counts.apply(lambda row: angle_lookup.get((row["Domain"], row["Position_Category"]), 0), axis=1)

# Plot setup
fig = go.Figure()

domain_colors = {
    "Health Classification": "#EF553B",
    "Health Information Management": "#00CC96",
    "Health Informatics": "#AB63FA",
    "Health Data Analysis": "#FFA15A"
}

# Add dots
for _, row in dot_counts.iterrows():
    link = f"categories/{row['Normalized_Category']}.html"
    fig.add_trace(go.Scatterpolar(
        r=[row["Radius"]],
        theta=[row["Theta"]],
        mode="markers",
        marker=dict(
            size=8 + 4 * row["Frequency"],  # scalable size
            color=domain_colors.get(row["Domain"], "#636efa"),
            line=dict(color="#000000", width=1.2),
            opacity=0.95
        ),
        hovertext=row["Position_Category"],
        hoverinfo="text",
        customdata=[link],
        name=""
    ))

# Add connecting lines based on matching ID_No
connected_lines = []
grouped = df.groupby("ID_No")
for id_no, group in grouped:
    if len(group) < 2:
        continue
    base_columns = ["Position_Category", "Career_Level"]
    if group[base_columns].nunique().eq(1).all():
        # Valid only if same category/level, but different domain
        domains_seen = set()
        for _, row_a in group.iterrows():
            for _, row_b in group.iterrows():
                if row_a["Domain"] != row_b["Domain"] and row_b["Domain"] not in domains_seen:
                    r_vals = [career_map[row_a["Career_Level"]], career_map[row_b["Career_Level"]]]
                    theta_vals = [
                        angle_lookup.get((row_a["Domain"], row_a["Position_Category"]), 0),
                        angle_lookup.get((row_b["Domain"], row_b["Position_Category"]), 0)
                    ]
                    fig.add_trace(go.Scatterpolar(
                        r=r_vals,
                        theta=theta_vals,
                        mode="lines",
                        line=dict(color="white", width=1, dash="dot"),
                        opacity=0.45,
                        hoverinfo="none",
                        showlegend=False
                    ))
            domains_seen.add(row_a["Domain"])

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

# Export radial map HTML only
chart_html = fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="map-container")

# Inject radial map into template
template_path = "../template/index_template.html"
with open(template_path, "r", encoding="utf-8") as f:
    base_template = f.read()

final_output = base_template.replace("<!--RADIAL_MAP-->", chart_html)

# Save final output
output_path = "../index.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(final_output)

print(f"✅ Radial map embedded and saved to: {output_path}")

# === Generate Category Pages ===
category_dir = os.path.join(os.path.dirname(__file__), "..", "categories")
os.makedirs(category_dir, exist_ok=True)

summary_df = (
    df.groupby("Position_Category")
    .agg(
        Frequency=("ID_No", "count"),
        Domains=("Domain", lambda x: ', '.join(sorted(set(x)))),
        Career_Levels=("Career_Level", lambda x: ', '.join(sorted(set(x))))
    )
    .reset_index()
)
summary_df["Normalized_Category"] = summary_df["Position_Category"].apply(normalize_name)
summary_df = summary_df.drop_duplicates("Normalized_Category")
summary_dict = summary_df.set_index("Normalized_Category").to_dict("index")

def generate_html(category_name, frequency, domains, career_levels):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
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
    .stats {{
      animation: slideFadeIn 0.8s ease forwards;
      opacity: 0;
      transform: translateY(20px);
    }}
    @keyframes slideFadeIn {{
      to {{
        opacity: 1;
        transform: translateY(0);
      }}
    }}
  </style>
</head>
<body>
  <h1>{category_name}</h1>
  <p>This page will include detailed information about the <strong>{category_name}</strong> category.</p>
  <p>You can describe example job roles, required skills, career progression, and domain-specific insights here.</p>
  <hr>
  <div class="stats">
    <h3>Stats:</h3>
    <p><strong>Frequency:</strong> {frequency}</p>
    <p><strong>Appears in Domains:</strong> {domains}</p>
    <p><strong>Career Levels:</strong> {career_levels}</p>
  </div>
</body>
</html>"""

for original, data in summary_dict.items():
    html = generate_html(
        category_name=summary_df[summary_df["Normalized_Category"] == original]["Position_Category"].values[0],
        frequency=data["Frequency"],
        domains=data["Domains"],
        career_levels=data["Career_Levels"]
    )
    file_path = os.path.join(category_dir, f"{original}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

print(f"✅ Generated {len(summary_dict)} category pages in: {category_dir}")
