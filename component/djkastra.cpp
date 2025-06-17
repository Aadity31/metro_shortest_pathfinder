#include <iostream>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <vector>
#include <queue>
#include <limits>
#include <cmath>
#include <stack>
#include <algorithm>
using namespace std;

struct Edge {
    int to;
    float distance;
    float time;
};

unordered_map<string, int> stationToID;
unordered_map<int, string> idToStation;
vector<vector<Edge>> graph;

void loadCSV(const string &filename) {
    ifstream file(filename);
    if (!file.is_open()) {
        cerr << "Error: Could not open file '" << filename << "'\n";
        exit(1);
    }

    string line, station1, station2, distanceStr, timeStr;
    int id = 0;
    getline(file, line); // skip header

    while (getline(file, line)) {
        stringstream ss(line);
        string field;
        vector<string> fields;
        bool inQuotes = false;
        string token;
        for (char c : line) {
            if (c == '"') inQuotes = !inQuotes;
            else if (c == ',' && !inQuotes) {
                fields.push_back(token);
                token.clear();
            } else {
                token += c;
            }
        }
        fields.push_back(token);
        if (fields.size() < 4) continue;
        station1 = fields[0];
        station2 = fields[1];
        distanceStr = fields[2];
        timeStr = fields[3];

        if (station1.empty() || station2.empty() || distanceStr.empty() || timeStr.empty())
            continue;

        try {
            float distance = stof(distanceStr);
            float time = stof(timeStr);

            if (stationToID.find(station1) == stationToID.end()) {
                stationToID[station1] = id;
                idToStation[id] = station1;
                id++;
            }
            if (stationToID.find(station2) == stationToID.end()) {
                stationToID[station2] = id;
                idToStation[id] = station2;
                id++;
            }

            int u = stationToID[station1];
            int v = stationToID[station2];

            if (graph.size() <= max(u, v))
                graph.resize(max(u, v) + 1);

            graph[u].push_back({v, distance, time});
            graph[v].push_back({u, distance, time});
        } catch (...) {
            cerr << "Skipping invalid line: " << line << endl;
        }
    }
}

void dijkstraPath(int source, int destination) {
    int n = graph.size();
    vector<float> dist(n, numeric_limits<float>::max());
    vector<float> time(n, numeric_limits<float>::max());
    vector<int> parent(n, -1);
    dist[source] = 0;
    time[source] = 0;

    using P = pair<float, int>;
    priority_queue<P, vector<P>, greater<P>> pq;
    pq.push({0, source});

    while (!pq.empty()) {
        pair<float, int> top = pq.top(); pq.pop();
        float d = top.first;
        int u = top.second;
        if (d > dist[u]) continue;

        for (auto edge : graph[u]) {
            int v = edge.to;
            float dNew = dist[u] + edge.distance;
            float tNew = time[u] + edge.time;

            if (dNew < dist[v]) {
                dist[v] = dNew;
                time[v] = tNew;
                parent[v] = u;
                pq.push({dist[v], v});
            }
        }
    }

    if (dist[destination] == numeric_limits<float>::max()) {
        cout << "No path found between these stations." << endl;
        return;
    }

    // Build path
    vector<int> path;
    for (int at = destination; at != -1; at = parent[at]) {
        path.push_back(at);
    }
    reverse(path.begin(), path.end());

    // Output
    cout << "Shortest path from " << idToStation[source] << " to " << idToStation[destination] << ":" << endl;

    // Print path as a string for display
    for (int i = 0; i < path.size(); i++) {
        cout << idToStation[path[i]];
        if (i != path.size() - 1) cout << " -> ";
    }
    cout << endl;

    // Print path as a comma-separated list for backend use
    for (int i = 0; i < path.size(); i++) {
        cout << idToStation[path[i]];
        if (i != path.size() - 1) cout << ",";
    }
    cout << endl;

    float fare = ceil(dist[destination] / 2.0) * 10;
    cout << "Total Distance: " << dist[destination] << " km" << endl;
    cout << "Estimated Time: " << time[destination] << " min" << endl;
    cout << "Fare: Rs " << fare << endl;
}

int main(int argc, char* argv[]) {
    string filename = "value/data.csv";
    loadCSV(filename);

    string srcStation, destStation;
    if (argc == 3) {
        srcStation = argv[1];
        destStation = argv[2];
    } else {
        cout << "Enter source station: ";
        getline(cin, srcStation);
        cout << "Enter destination station: ";
        getline(cin, destStation);
    }

    if (stationToID.find(srcStation) == stationToID.end()) {
        cout << "Source station not found!" << endl;
        return 1;
    }
    if (stationToID.find(destStation) == stationToID.end()) {
        cout << "Destination station not found!" << endl;
        return 1;
    }

    int srcID = stationToID[srcStation];
    int destID = stationToID[destStation];

    dijkstraPath(srcID, destID);

    return 0;
}
