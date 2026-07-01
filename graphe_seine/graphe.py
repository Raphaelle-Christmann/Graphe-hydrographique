# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import pathlib
import pickle
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import pyproj
import networkx as nx
import pickle
from shapely import Point, LineString, MultiLineString, GeometryCollection, box
from shapely.ops import split, snap, linemerge
from contracter import contract
from tqdm.auto import tqdm
from contracter import contract
TEMP_DATA = pathlib.Path("Temper_Data")

# Chargement des tronçons hydrographiques pour une zone (bbox) couvrant
# approximativement le bassin de la Seine, indexés par CdOH (id du tronçon)
Seine_Code = "03C00000020008"
Root_Name = "Balise fond"

bbox = box(490000, 6658000, 861000, 6981000)
gdf = gpd.read_file(
    "../Graphs/reseau_seine.gpkg")

# Chargement des sites (stations) et reprojection en Lambert-93 (EPSG:2154)
# pour être cohérent avec les données hydrographiques
sites = gpd.read_file("Sites/Sites.shp").to_crs("EPSG:2154")
sites

# Rattachement de chaque site au réseau hydrographique : pour chaque site, on cherche le tronçon le plus proche,
# on projette le point du site sur ce tronçon, puis on découpe le tronçon
# au point projeté pour insérer le site comme un nœud du réseau

sites2 = sites[~sites.is_empty]

# %%
G = nx.Graph()
OG = nx.DiGraph()

# chaque point de la LineString devient un nœud du graphe, chaque segment devient une arête avec un poids égal à sa longueur

for _, row in tqdm(gdf.iterrows(), total=len(gdf)): 
    geom = row.geometry
    for i, j in zip(geom.coords, geom.coords[1:]):
        G.add_edge(i, j, weight=LineString([i, j]).length)
        OG.add_edge(i, j, weight=LineString([i, j]).length)

# %%
root_node = sites2.loc[sites2["Libellé"] == Root_Name, "geometry"]
root_node = root_node.squeeze().coords[0]

site_nodes = []
for site in sites2.itertuples():
    coord = site.geometry.coords[0]  # Point
    attrs = G.nodes[coord]
    attrs["site_id"] = site.Index
    attrs["label"] = site.Libellé
    attrs = OG.nodes[coord]
    attrs["site_id"] = site.Index
    attrs["label"] = site.Libellé
    site_nodes.append(coord)

# %%
colors = []
paths = {}
for site in site_nodes:
    attrs = G.nodes[site]
    if nx.has_path(G, root_node, site):
        path = nx.shortest_path(G, root_node, site, weight="weight")
        paths[site] = path
        colors.append("green")
    else:
        print(f"Aucun chemin trouvé vers {attrs['label']}")
        colors.append("red")

G_contract = contract(G)

pickle.dump(G, open('graph.pickle', 'wb'))
pickle.dump(G_contract, open('contract.pickle', 'wb'))
