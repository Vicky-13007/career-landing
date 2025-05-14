import pandas as pd
import numpy as np
import re
import os

# Load the dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")
categories = df["Position_Category"].dropna().unique()

# Normalize for filenames
def norm(x):
    return re.sub(r'[^a-z0-9_]', '', re.sub(r'\s+', '_', x.strip().lower()))

# Randomly spread across a large canvas
np.random.seed(42)
canvas_width = 2000
canvas_height = 1500
positions = list(zip(
    np.random.randint(100, canvas_width - 150, size=len(categories)),
    np.random.randint(100, canvas_height - 40, size=len(categories))
))

# Build HTML for each category dot
dots = ""
for label, (x, y) in zip(categories, positions):
    filename = norm(label)
    dots += f'<div class="dot" style="left: {x}px; top: {y}px;" onclick="window.open(\'categories/{filename}.html\', \'_blank\')" title="{label}">{label}</div>\n'

# Load the index template
with open("../template/index_template.html", "r", encoding="utf-8") as f:
    template = f.read()

# Inject the dots into the template
with open("../index.html", "w", encoding="utf-8") as f:
    f.write(template.replace("<!--DOT_CONTAINER-->", dots))

print("✅ index.html successfully generated with real category positions.")
