import pandas as pd, numpy as np, re, os

# Load the dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")
categories = df["Position_Category"].dropna().unique()

# Normalize for filenames
def norm(x): return re.sub(r'[^a-z0-9_]', '', re.sub(r'\s+', '_', x.strip().lower()))

# Use grid layout to avoid overlapping
cols = 6
spacing_x = 180
spacing_y = 90
offset_x = 120
offset_y = 100
positions = [(offset_x + (i % cols) * spacing_x, offset_y + (i // cols) * spacing_y)
             for i in range(len(categories))]

# Build HTML for each category dot
dots = ""
for label, (x, y) in zip(categories, positions):
    filename = norm(label)
    dots += f'<div class="dot" style="left: {x}px; top: {y}px;" onclick="window.open(\'categories/{filename}.html\', \'_blank\')" title="{label}">{label}</div>\n'

# Load template
with open("../template/index_template.html", "r", encoding="utf-8") as f:
    template = f.read()

# Inject dot HTML and save
with open("../index.html", "w", encoding="utf-8") as f:
    f.write(template.replace("<!--DOT_CONTAINER-->", dots))

print("✅ Non-overlapping index.html generated with real categories.")
