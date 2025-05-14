import pandas as pd
import numpy as np
import re
import os

# Load the dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")

# Group by Position_Category and extract Domain and Career Level
grouped = df.groupby("Position_Category").agg({
    "Domain": lambda x: ", ".join(sorted(set(x.dropna()))),
    "Career_Level": lambda x: ", ".join(sorted(set(x.dropna())))
}).reset_index()

# Normalize Position_Category for filenames
def norm(x):
    return re.sub(r'[^a-z0-9_]', '', re.sub(r'\s+', '_', x.strip().lower()))

# Generate non-overlapping-ish coordinates for dots
np.random.seed(42)
canvas_width = 2000
canvas_height = 1500
positions = list(zip(
    np.random.randint(100, canvas_width - 150, size=len(grouped)),
    np.random.randint(100, canvas_height - 40, size=len(grouped))
))

# Build dot HTML elements with tooltips
dot_divs = ""
for (idx, row), (x, y) in zip(grouped.iterrows(), positions):
    title = row["Position_Category"]
    domain = row["Domain"]
    level = row["Career_Level"]
    tooltip = f"{title} | {domain} | {level}"
    filename = norm(title)
    dot_divs += f'<div class="dot" style="left: {x}px; top: {y}px;" title="{tooltip}" onclick="window.open(\'categories/{filename}.html\', \'_blank\')">{title}</div>\n'

# Load index_template.html
with open("../template/index_template.html", "r", encoding="utf-8") as f:
    template = f.read()

# Inject the dot HTML into the placeholder
with open("../career_map.html", "w", encoding="utf-8") as f:
    f.write(template.replace("<!--DOT_CONTAINER-->", dot_divs))

print("✅ index.html successfully generated with tooltips and real categories.")
