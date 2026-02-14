import streamlit as st
import heapq
import pandas as pd
import folium
import requests
import polyline
from streamlit_folium import st_folium


st.set_page_config(
    page_title="Smart Logistics Optimizer",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
    h1 {color: #1E3A8A; font-weight: 700;}
    div.stButton > button {
        background: linear-gradient(90deg, #2563EB 0%, #1E40AF 100%);
        color: white; border: none; padding: 0.5rem 1rem;
        border-radius: 8px; font-weight: 600; width: 100%;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    [data-testid="stMetricValue"] {font-size: 2rem; color: #2563EB;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)



def get_route_shape(locations_list):
    """Mengambil bentuk jalan asli (liuk-liuk) menggunakan OSRM."""
    if not locations_list: return []
    coords_string = ";".join([f"{lon},{lat}" for lat, lon in locations_list])
    url = f"http://router.project-osrm.org/route/v1/driving/{coords_string}?overview=full&geometries=polyline"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        res = r.json()
        if res.get('code') == 'Ok':
            encoded_geometry = res['routes'][0]['geometry']
            return polyline.decode(encoded_geometry)
        else:
            return locations_list
    except:
        return locations_list

class Graph:
    def __init__(self):
        self.edges = {}
        self.heuristics = {}
    def add_edge(self, from_node, to_node, weight):
        if from_node not in self.edges: self.edges[from_node] = []
        if to_node not in self.edges: self.edges[to_node] = []
        self.edges[from_node].append((to_node, weight))
        self.edges[to_node].append((from_node, weight))
    def set_heuristic(self, node, value):
        self.heuristics[node] = value
    def heuristic(self, node, goal):
        return self.heuristics.get(node, 0)
    def a_star(self, start, goal):
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {node: float('inf') for node in self.edges}
        g_score[start] = 0
        f_score = {node: float('inf') for node in self.edges}
        f_score[start] = self.heuristic(start, goal)

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                return self.reconstruct_path(came_from, start, goal), g_score[goal]

            for neighbor, weight in self.edges.get(current, []):
                tentative_g_score = g_score[current] + weight
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        return None, float('inf')
    def reconstruct_path(self, came_from, start, goal):
        path = [goal]
        while goal in came_from:
            goal = came_from[goal]
            path.append(goal)
        path.reverse()
        return path


graph = Graph()
edges = [
    ('A', 'B', 4.157), ('A', 'C', 3.072), ('A', 'H', 3.015), ('A', 'J', 3.040),
    ('B', 'C', 2.070), ('B', 'D', 1.958), ('C', 'D', 1.538), ('D', 'E', 1.921),
    ('E', 'F', 1.472), ('E', 'G', 2.051), ('F', 'G', 0.926), ('H', 'I', 1.675),
    ('I', 'J', 2.271)
]
for edge in edges: graph.add_edge(*edge)

heuristics = {
    'A': 2500, 'B': 2000, 'C': 1500, 'D': 1000, 'E': 2000, 
    'F': 0, 'G': 500, 'H': 6000, 'I': 2000, 'J': 2800
}
for node, value in heuristics.items(): graph.set_heuristic(node, value)

location_names_dict = {
    'A': 'Kantor Pos Pusat Medan',
    'B': 'Komplek Bandar Selamat Permai',
    'C': 'Kantor Pos Bakaran Batu',
    'D': 'Kantor Pos Laksamana',
    'E': 'Kantor Pos Menteng',
    'F': 'Kantor Pos SM. Raja Medan',
    'G': 'Kantor Pos Alfalah',
    'H': 'Kantor Pos Medan Baru',
    'I': 'Kantor Pos Gatot Subroto',
    'J': 'Kantor Pos Tengku Amir Hamza'
}
location_map = {v: k for k, v in location_names_dict.items()}
locations = {
    "Kantor Pos Pusat Medan": [3.589665, 98.673826],
    "Komplek Bandar Selamat Permai": [3.608456, 98.715797],
    "Kantor Pos Bakaran Batu": [3.550375, 98.605444],
    "Kantor Pos Laksamana": [3.564014, 98.644775],
    "Kantor Pos Menteng": [3.574768, 98.656064],
    "Kantor Pos SM. Raja Medan": [3.588601, 98.668603],
    "Kantor Pos Alfalah": [3.576818, 98.686293],
    "Kantor Pos Medan Baru": [3.591781, 98.685522],
    "Kantor Pos Gatot Subroto": [3.601358, 98.675832],
    "Kantor Pos Tengku Amir Hamza": [3.588830, 98.669588]
}


with st.sidebar:
    st.title("🚚 Logistic Optimizer")
    st.divider()
    
    start_location = st.selectbox('📍 Start', list(locations.keys()), index=0)
    goal_location = st.selectbox('🏁 Destination', list(locations.keys()), index=4)
    
    st.markdown("---")
    search_pressed = st.button('🔍 Search for the fastest route')
    
    with st.expander("📊 Lihat Lokasi"):
        h_df = pd.DataFrame(list(heuristics.items()), columns=['Node', 'H'])
        h_df['Loc'] = h_df['Node'].map(location_names_dict)
        st.dataframe(h_df[['Loc', 'H']], hide_index=True)


if 'path_locations' not in st.session_state:
    st.session_state.path_locations = []
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0

if search_pressed:
    s_node, g_node = location_map[start_location], location_map[goal_location]
    if s_node == g_node:
        st.toast("Lokasi awal dan tujuan sama!", icon="⚠️")
        st.session_state.path_locations = []
    else:
        with st.spinner('Menghitung rute...'):
            path, cost = graph.a_star(s_node, g_node)
            if path:
                rev_map = {v: k for k, v in location_map.items()}
                st.session_state.path_locations = [rev_map[n] for n in path]
                st.session_state.total_cost = cost
            else:
                st.error("Jalur tidak ditemukan.")
                st.session_state.path_locations = []


st.title("🗺️ Smart Map Navigation")

col1, col3 = st.columns(2)
with col1: st.metric("Total Distance", f"{st.session_state.total_cost:.1f} km")
with col3: st.metric("Status", "Route Found" if st.session_state.path_locations else "Waiting")

st.markdown("### Route Visualization")
m = folium.Map(location=[3.5952, 98.6722], zoom_start=13, tiles="cartodbpositron")

if st.session_state.path_locations:

    display_locations = st.session_state.path_locations
else:
    display_locations = [start_location, goal_location]

for name in display_locations:
    if name in locations:
        coord = locations[name]
        
        if name == start_location: 
            icon_color = "green"
            icon_type = "play"
        elif name == goal_location: 
            icon_color = "red"
            icon_type = "flag"
        else: 
            icon_color = "blue" 
            icon_type = "info-sign"

        folium.Marker(
            location=coord,
            popup=name,
            icon=folium.Icon(color=icon_color, icon=icon_type)
        ).add_to(m)

if st.session_state.path_locations:
    route_coords = [locations[loc] for loc in st.session_state.path_locations]
    real_route = get_route_shape(route_coords)
    folium.PolyLine(real_route, color='rgba(37, 99, 235, 0.4)', weight=8).add_to(m)
    folium.PolyLine(real_route, color='#2563EB', weight=4).add_to(m)

st_folium(m, width="100%", height=500)