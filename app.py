import os
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from component import graph
from component import gmap
from dotenv import load_dotenv

app = Flask(__name__)

# Load stations for dropdowns
stations = pd.read_csv(os.path.join("value", "stations.csv"))

# Ensure the static folder exists
if not os.path.exists("static"):
    os.makedirs("static")

# Generate the full map once if it doesn't exist
if not os.path.exists("delhi_metro_googlemap.html"):
    gmap.generate_gmap_html()

load_dotenv()  # This will load variables from .env into environment

GMAP_API_KEY = os.getenv("GMAP")

@app.route('/')
def index():
    station_list = stations['Station_Name'].tolist()
    return render_template('index.html', stations=station_list)

@app.route('/graph_image')
def graph_image():
    # Show the full graph if no path is selected
    buf = graph.generate_graph_image()
    return send_file(buf, mimetype='image/png')

@app.route('/graph_path_image', methods=['POST'])
def graph_path_image():
    path_list = request.json.get('path_list', None)
    buf = graph.generate_graph_image(path_list)
    return send_file(buf, mimetype='image/png')

@app.route('/get_path', methods=['POST'])
def get_path():
    source = request.form['source']
    destination = request.form['destination']
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    exe_path = os.path.join(BASE_DIR, "component", "djkastra.exe")
    result = None
    try:
        if not os.path.exists(exe_path):
            return jsonify({'error': 'djkastra.exe not found!'})
        import subprocess
        result = subprocess.run([exe_path, source, destination], capture_output=True, text=True)
    except Exception as e:
        return jsonify({'error': str(e)})

    output = result.stdout.splitlines()
    if len(output) < 6:
        return jsonify({'error': 'No path found'})
    path_display = output[1]
    path_list = output[2].split(",")
    distance = output[3]
    time = output[4]
    fare = output[5]
    return jsonify({
        'path': path_display,
        'path_list': path_list,
        'distance': distance,
        'time': time,
        'fare': fare
    })

@app.route('/gmap_path', methods=['POST'])
def gmap_path():
    path_list = request.json.get('path_list', None)
    gmap.generate_gmap_html(path_list)
    return '', 204

@app.route('/delhi_metro_googlemap.html')
def metro_map():
    return send_file('delhi_metro_googlemap.html')

if __name__ == '__main__':
    app.run(debug=True)