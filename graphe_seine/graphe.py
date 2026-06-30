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
from tqdm.auto import tqdm
from contracter import contract
TEMP_DATA = pathlib.Path("Temper_Data")

# Chargement des tronçons hydrographiques pour une zone (bbox) couvrant
# approximativement le bassin de la Seine, indexés par CdOH (id du tronçon)
Seine_Code = "03C00000020008"
Root_Name = "Balise fond"

bbox = box(490000, 6658000, 861000, 6981000)
gdf = gpd.read_file(
    "TronconHydrographique_FXX-shp/TronconHydrographique_FXX.shp",
    bbox=bbox,
).set_index("CdOH")

# Correctif manuel : deux tronçons mal renseignés se voient réaffecter
# le nom de cours d'eau "la Marne" et le code de cours d'eau correspondant

patch = {
    "03T0000002287758528": {"TopoOH": "la Marne", "CdCoursEau": "03C0000002000815787"},
    "03T0000002287758537": {"TopoOH": "la Marne", "CdCoursEau": "03C0000002000815787"},
}

gdf.update(pd.DataFrame.from_dict(patch, orient="index")) # on applique les corrections sur le GeoDataFrame

# Filtrage : on ne garde que les tronçons dont le CdCoursEau commence par
# le code du bassin de la Seine, et on force les géométries en 2D (suppression Z)

m = gdf['CdCoursEau'].fillna("").str.startswith(Seine_Code)
seine = gdf[m].copy()
seine["geometry"] = seine.force_2d()
seine

# %%
seine['CdCoursEau'].dropna()

# Chargement des sites (stations) et reprojection en Lambert-93 (EPSG:2154)
# pour être cohérent avec les données hydrographiques
sites = gpd.read_file("Sites/Sites.shp").to_crs("EPSG:2154")
sites

# Rattachement de chaque site au réseau hydrographique : pour chaque site, on cherche le tronçon le plus proche,
# on projette le point du site sur ce tronçon, puis on découpe le tronçon
# au point projeté pour insérer le site comme un nœud du réseau

sites2 = sites[~sites.is_empty]
seine2 = seine.explode(ignore_index=True)

pos1, pos2 = seine2.sindex.nearest(sites2["geometry"], return_all=False)

for idx1, idx2 in zip(sites2.index[pos1], seine2.index[pos2]):
    pt = sites.loc[idx1, "geometry"]
    ls = seine2.loc[idx2, "geometry"]

    proj_pt = ls.interpolate(ls.project(pt)) # projection du site sur la ligne
    snap_ls = snap(ls, proj_pt, 1e-6) # on "accroche" la ligne au point projeté
    split_ls = split(snap_ls, proj_pt) # on découpe la ligne au point projeté
    split_ls = linemerge(split_ls) 

    sites2.loc[idx1, "geometry"] = proj_pt # le site prend la position du point projeté
    seine2.loc[idx2, "geometry"] = split_ls # le tronçon est remplacé par la ligne découpée

# On ne garde que les tronçons appartenant aux mêmes cours d'eau (TopoOH)
# que ceux ayant reçu un site

topo = seine2.loc[seine2.index[pos2], "TopoOH"].drop_duplicates().to_list()
seine3 = seine2[seine2["TopoOH"].isin(topo)]
seine3

# %%
G = nx.Graph()

# chaque point de la LineString devient un nœud du graphe, chaque segment devient une arête avec un poids égal à sa longueur

for _, row in tqdm(seine3.iterrows(), total=len(seine3)): 
    geom = row.geometry
    for i, j in zip(geom.coords, geom.coords[1:]):
        G.add_edge(i, j, weight=LineString([i, j]).length)

# %%
root_node = sites2.loc[sites2["Libellé"] == Root_Name, "geometry"]
root_node = root_node.squeeze().coords[0]

site_nodes = []
for site in sites2.itertuples():
    coord = site.geometry.coords[0]  # Point
    attrs = G.nodes[coord]
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