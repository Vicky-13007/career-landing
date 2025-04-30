import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Load the dataset
df = pd.read_csv("/Users/vignesshwarvenkatachalam/Downloads/career_landing/data/radial_data_split_domains_filtered.csv")

# Group and summarize to create the 'Frequency' column
agg_df = df.groupby(
    ["Domain", "Position_Category", "Position_Title", "Career_Level"]
).size().reset_index(name="Frequency")

# Define ring mapping
ring_map = {"Early Career": 1, "Established Career": 2, "Advanced Career": 3}

# Create radial plots per domain
for domain in agg_df["Domain"].dropna().unique():
    domain_data = agg_df[agg_df["Domain"] == domain].copy()
    categories = sorted(domain_data["Position_Category"].unique())
    angle_map = {cat: i * (360 / len(categories)) for i, cat in enumerate(categories)}
    domain_data["Angle"] = domain_data["Position_Category"].map(angle_map)
    domain_data["Radius"] = domain_data["Career_Level"].map(ring_map)

    fig = go.Figure()
    for _, row in domain_data.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[row["Radius"]],
            theta=[row["Angle"]],
            mode='markers',
            marker=dict(
                size=5 + 5 * np.log1p(row["Frequency"]),
                color=row["Radius"],
                colorscale="Viridis",
                line=dict(color="white", width=1),
                opacity=0.9
            ),
            hovertemplate=f"<b>{row['Position_Title']}</b><br>{row['Position_Category']}<br>{row['Career_Level']}<br>Freq: {row['Frequency']}<extra></extra>"
        ))

    fig.update_layout(
        title=f"Career Pathways in {domain}",
        polar=dict(
            radialaxis=dict(
                visible=True,
                tickvals=[1, 2, 3],
                ticktext=["Early Career", "Established Career", "Advanced Career"],
                range=[0.5, 3.5]
            ),
            angularaxis=dict(
                tickvals=list(angle_map.values()),
                ticktext=list(angle_map.keys()),
                rotation=90,
                direction="clockwise"
            )
        ),
        template="plotly_dark",
        showlegend=False,
        width=850,
        height=850
    )

    # Save HTML file
    filename = f"../final_radial_map_{domain.replace(' ', '_')}.html"
    fig.write_html(filename)
