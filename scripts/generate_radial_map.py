import pandas as pd, numpy as np, re, os

# Load dataset
df = pd.read_csv("../data/radial_data_split_domains_filtered.csv")
categories = df["Position_Category"].dropna().unique()

# Normalize for filenames
def norm(x): return re.sub(r'[^a-z0-9_]', '', re.sub(r'\s+', '_', x.strip().lower()))

# Generate more spatially distributed positions
np.random.seed(42)
positions = []
used_positions = set()
while len(positions) < len(categories):
    x = np.random.randint(100, 1800)
    y = np.random.randint(100, 1400)
    key = (round(x / 30), round(y / 30))  # avoid tight overlap
    if key not in used_positions:
        used_positions.add(key)
        positions.append((x, y))

# Build HTML
dots = ""
for label, (x, y) in zip(categories, positions):
    filename = norm(label)
    dots += f'<div class="dot" style="left: {x}px; top: {y}px;" onclick="window.open(\'categories/{filename}.html\', \'_blank\')" title="{label}">{label}</div>\n'

# Inject into template
with open("../template/index_template.html", "r", encoding="utf-8") as f:
    template = f.read()

with open("../index.html", "w", encoding="utf-8") as f:
    f.write(template.replace("<!--DOT_CONTAINER-->", dots))

print("✅ Fully scattered HIM career map index.html generated.")
