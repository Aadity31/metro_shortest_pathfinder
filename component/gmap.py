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
load_dotenv()
GMAP_API_KEY = os.getenv("GMAP")

def generate_gmap_html(path_list=None, filename="delhi_metro_googlemap.html"):
    stations = pd.read_csv(os.path.join(BASE_DIR, "value", "stations.csv"))
    edges = pd.read_csv(os.path.join(BASE_DIR, "value", "edges.csv"))
    lines = pd.read_csv(os.path.join(BASE_DIR, "value", "lines.csv"))

    stations['Station_Name'] = stations['Station_Name'].apply(clean_name)
    edges['Source'] = edges['Source'].apply(clean_name)
    edges['Target'] = edges['Target'].apply(clean_name)
    edges['Line_Name'] = edges['Line_Name'].apply(clean_name)

    stations = stations.drop_duplicates(subset="Station_Name", keep="first")
    line_colors = dict(zip(lines["Line_Name"], lines["Color_Hex_Code"]))
    coord_lookup = stations.set_index("Station_Name")[["Latitude", "Longitude"]].to_dict(orient="index")

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