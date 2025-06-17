import os
import pandas as pd
from gmplot import gmplot
from collections import Counter
from flask import Flask, render_template
import subprocess
from dotenv import load_dotenv

app = Flask(__name__)

def clean_name(s):
    return str(s).strip().replace('\r', '').replace('\n', '')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Load data
stations = pd.read_csv(os.path.join(BASE_DIR, "value", "stations.csv"))
edges = pd.read_csv(os.path.join(BASE_DIR, "value", "edges.csv"))
lines = pd.read_csv(os.path.join(BASE_DIR, "value", "lines.csv"))

# Clean station names
stations['Station_Name'] = stations['Station_Name'].apply(clean_name)
edges['Source'] = edges['Source'].apply(clean_name)
edges['Target'] = edges['Target'].apply(clean_name)
edges['Line_Name'] = edges['Line_Name'].apply(clean_name)

# Remove duplicate station names
stations = stations.drop_duplicates(subset="Station_Name", keep="first")

# Color lookup for lines
line_colors = dict(zip(lines["Line_Name"], lines["Color_Hex_Code"]))

# Coordinate lookup
coord_lookup = stations.set_index("Station_Name")[["Latitude", "Longitude"]].to_dict(orient="index")

# Check for missing stations
missing_stations = set(edges['Source']).union(edges['Target']) - set(stations['Station_Name'])
if missing_stations:
    print("⚠️ These stations are in edges.csv but missing in stations.csv:", missing_stations)
else:
    print("✅ All stations in edges.csv are present in stations.csv")

# Find interchange stations (degree > 2)
all_stations = list(edges['Source']) + list(edges['Target'])
station_counts = Counter(all_stations)
interchanges = {station for station, count in station_counts.items() if count > 2}

# Center of map
center_lat = stations["Latitude"].mean()
center_lon = stations["Longitude"].mean()

load_dotenv()
GMAP_API_KEY = os.getenv("GMAP")

# Google Map Plotter (replace with your API key)
gmap = gmplot.GoogleMapPlotter(center_lat, center_lon, 11, apikey=GMAP_API_KEY)

# Draw edges as colored lines
for row in edges.itertuples():
    src = coord_lookup.get(row.Source)
    tgt = coord_lookup.get(row.Target)
    color = line_colors.get(row.Line_Name, "#888888")
    if src and tgt:
        gmap.plot([src["Latitude"], tgt["Latitude"]],
                  [src["Longitude"], tgt["Longitude"]],
                  color=color, edge_width=5)

# Draw station markers
for station, coord in coord_lookup.items():
    if station in interchanges:
        gmap.marker(coord["Latitude"], coord["Longitude"], color='orange', title=station)
    else:
        gmap.marker(coord["Latitude"], coord["Longitude"], color='blue', title=station)

# Save map
gmap.draw("delhi_metro_googlemap.html")
print("✅ Google Map HTML file 'delhi_metro_googlemap.html' created with colored connections and stations.")

def generate_gmap_html(path_list=None, filename="delhi_metro_googlemap.html"):
    stations = pd.read_csv("stations.csv")
    edges = pd.read_csv("edges.csv")
    lines = pd.read_csv("lines.csv")

    stations['Station_Name'] = stations['Station_Name'].str.strip().str.replace('\r', '').str.replace('\n', '')
    edges['Source'] = edges['Source'].str.strip().str.replace('\r', '').str.replace('\n', '')
    edges['Target'] = edges['Target'].str.strip().str.replace('\r', '').str.replace('\n', '')

    coord_lookup = stations.set_index("Station_Name")[["Latitude", "Longitude"]].to_dict(orient="index")
    line_colors = dict(zip(lines["Line_Name"], lines["Color_Hex_Code"]))

    # Center of map
    center_lat = stations["Latitude"].mean()
    center_lon = stations["Longitude"].mean()
    gmap = gmplot.GoogleMapPlotter(center_lat, center_lon, 12, apikey=GMAP_API_KEY)

    # Always plot all stations as blue markers
    for station, coord in coord_lookup.items():
        gmap.marker(coord["Latitude"], coord["Longitude"], color="blue")

    if path_list and len(path_list) > 1:
        # Draw only the path edges, colored by line
        for i in range(len(path_list) - 1):
            src = path_list[i]
            dst = path_list[i+1]
            # Find the line for this edge
            line_row = edges[((edges['Source'] == src) & (edges['Target'] == dst)) | ((edges['Source'] == dst) & (edges['Target'] == src))]
            color = "#FF0000"
            if not line_row.empty:
                line_name = line_row.iloc[0]['Line_Name']
                color = line_colors.get(line_name, "#FF0000")
            latlngs = [
                (coord_lookup[src]["Latitude"], coord_lookup[src]["Longitude"]),
                (coord_lookup[dst]["Latitude"], coord_lookup[dst]["Longitude"])
            ]
            gmap.plot(
                [latlngs[0][0], latlngs[1][0]],
                [latlngs[0][1], latlngs[1][1]],
                color,
                edge_width=8
            )
        # Optionally, highlight path stations
        for station in path_list:
            lat, lon = coord_lookup[station]["Latitude"], coord_lookup[station]["Longitude"]
            gmap.marker(lat, lon, color="orange")
    else:
        # Draw all edges
        for row in edges.itertuples():
            src = row.Source
            dst = row.Target
            color = line_colors.get(row.Line_Name, "#888888")
            latlngs = [
                (coord_lookup[src]["Latitude"], coord_lookup[src]["Longitude"]),
                (coord_lookup[dst]["Latitude"], coord_lookup[dst]["Longitude"])
            ]
            gmap.plot(
                [latlngs[0][0], latlngs[1][0]],
                [latlngs[0][1], latlngs[1][1]],
                color,
                edge_width=4
            )

    gmap.draw(filename)

@app.route('/')
def index():
    # Run gmap.py to update the map HTML
    subprocess.run(['python', 'gmap.py'])
    station_list = stations['Station_Name'].tolist()
    return render_template('index.html', stations=station_list)