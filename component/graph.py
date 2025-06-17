import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO

def generate_graph_image(path_list=None):
    import os
    import pandas as pd
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stations = pd.read_csv(os.path.join(BASE_DIR, "value", "stations.csv"))
    edges = pd.read_csv(os.path.join(BASE_DIR, "value", "edges.csv"))
    lines = pd.read_csv(os.path.join(BASE_DIR, "value", "lines.csv"))

    print("Generating graph image, path_list:", path_list)
    stations['Station_Name'] = stations['Station_Name'].str.strip().str.replace('\r', '').str.replace('\n', '')
    edges['Source'] = edges['Source'].str.strip().str.replace('\r', '').str.replace('\n', '')
    edges['Target'] = edges['Target'].str.strip().str.replace('\r', '').str.replace('\n', '')

    stations = stations.drop_duplicates(subset="Station_Name", keep="first")
    line_colors = dict(zip(lines["Line_Name"], lines["Color_Hex_Code"]))
    coord_lookup = stations.set_index("Station_Name")[["Latitude", "Longitude"]].to_dict(orient="index")

    # Build edge to line mapping
    edge_to_line = {}
    for row in edges.itertuples():
        edge_to_line[(row.Source, row.Target)] = row.Line_Name
        edge_to_line[(row.Target, row.Source)] = row.Line_Name  # undirected

    G = nx.Graph()
    for station, coord in coord_lookup.items():
        G.add_node(station, pos=(coord["Longitude"], coord["Latitude"]))

    for row in edges.itertuples():
        color = line_colors.get(row.Line_Name, "#888888")
        G.add_edge(row.Source, row.Target, color=color)

    pos = nx.get_node_attributes(G, 'pos')

    plt.figure(figsize=(20, 12))

    if path_list and len(path_list) > 1:
        # Draw only the path, color edges by line
        path_edges = list(zip(path_list, path_list[1:]))
        edge_colors = []
        for u, v in path_edges:
            line = edge_to_line.get((u, v), None)
            color = line_colors.get(line, "#FF0000") if line else "#FF0000"
            edge_colors.append(color)
        nx.draw_networkx_nodes(G, pos, nodelist=path_list, node_size=120, node_color='orange', alpha=0.9)
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color=edge_colors, width=4, alpha=0.8)
        nx.draw_networkx_labels(G, pos, labels={n: n for n in path_list}, font_size=10, font_color="black")
    else:
        # Draw full graph
        edge_colors = [G[u][v]['color'] for u, v in G.edges()]
        node_sizes = [30 for _ in G.nodes()]
        node_colors = ['#0077cc' for _ in G.nodes()]
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9)
        nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=2, alpha=0.7)
        nx.draw_networkx_labels(G, pos, font_size=7, font_color="black", font_family="sans-serif")

    plt.title("Delhi Metro Track Graph (Path Highlighted)" if path_list else "Delhi Metro Track Graph")
    plt.axis("off")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    print("Returning graph image buffer")
    return buf