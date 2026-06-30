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
import pickle
import pathlib
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import pyproj
import networkx as nx
from shapely import Point, LineString, MultiLineString, GeometryCollection, box
from shapely.ops import split, snap, linemerge
from tqdm.auto import tqdm
from collections import deque
"""
def oriente(graph, node):

    visited = []
    stack = deque()
    stack.append((node,0.))

    while stack:
        (node,d) = stack.pop()
        if node not in visited:
            visited.append(node)
            unvisited = []
            for v in graph[node] :
              if graph.nodes[node].get["site_id"] is not None :
               OG.
            stack.extend(unvisited)

    return visited
"""
TEMP_DATA = pathlib.Path("Temper_Data")

# %%
# Bassin de la seine
Seine_Code = "03C00000020008"
Root_Name = "Balise fond"

bbox = box(490000, 6658000, 861000, 6981000)
gdf = gpd.read_file(
    "TronconHydrographique_FXX-shp/TronconHydrographique_FXX.shp",
    bbox=bbox,
).set_index("CdOH")

patch = {
    "03T0000002287758528": {"TopoOH": "la Marne", "CdCoursEau": "03C0000002000815787"},
    "03T0000002287758537": {"TopoOH": "la Marne", "CdCoursEau": "03C0000002000815787"},
}

gdf.update(pd.DataFrame.from_dict(patch, orient="index"))

m = gdf['CdCoursEau'].fillna("").str.startswith(Seine_Code)
seine = gdf[m].copy()
seine["geometry"] = seine.force_2d()
seine

# %%
seine['CdCoursEau'].dropna()

# %%
sites = gpd.read_file("Sites/Sites.shp").to_crs("EPSG:2154")
sites

# %%
sites2 = sites[~sites.is_empty]
seine2 = seine.explode(ignore_index=True)

pos1, pos2 = seine2.sindex.nearest(sites2["geometry"], return_all=False)

for idx1, idx2 in zip(sites2.index[pos1], seine2.index[pos2]):
    pt = sites.loc[idx1, "geometry"]
    ls = seine2.loc[idx2, "geometry"]

    proj_pt = ls.interpolate(ls.project(pt))
    snap_ls = snap(ls, proj_pt, 1e-6)
    split_ls = split(snap_ls, proj_pt)
    split_ls = linemerge(split_ls)

    sites2.loc[idx1, "geometry"] = proj_pt
    seine2.loc[idx2, "geometry"] = split_ls

topo = seine2.loc[seine2.index[pos2], "TopoOH"].drop_duplicates().to_list()
seine3 = seine2[seine2["TopoOH"].isin(topo)]
seine3

# %%
G = pickle.load(open('graph.pickle', 'rb'))
Gc = pickle.load(open('contract.pickle', 'rb'))


OG = nx.DiGraph()

for (u,v) in G.edges :
  OG.add_edge(u,v)

pickle.dump(OG, open('oriented_graph.pickle', 'wb'))



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


'''
fig, ax = plt.subplots(figsize=(12, 12))
seine3.plot(ax=ax, lw=0.5, color="tab:blue", zorder=-1)
sites2.plot(ax=ax, lw=0.5, color=colors, markersize=5)
ax.ticklabel_format(style="plain", axis="both")
ax.set_aspect("equal")
fig.savefig("seine.png")
plt.show()
'''

# %% [markdown]
# Dans le shapefile, il y a 2 colonnes `CdNoeudDeb` et `CdNoeudFin` qui référencent l'index `CdOH`. Grâce à `pos2`, on peut retrouver les `CdOH` intégrant une station. Avec la fonction `nx.from_pandas_edgelist`, on peut construire un graph logique indépendemment de la topologie des cours d'eau. Les LineString (edges) deviennent des noeuds (nodes) du graph. Le centroide de la LineString pourrait être la position pour le layout et la longueur (length) physique du tronçon hydrographique.

# %%
cntr = gdf.centroid
pos = dict(zip(cntr.index, np.array([cntr.x, cntr.y]).T.tolist()))

m = gdf[["CdNoeudDeb", "CdNoeudFin"]].notna().all(axis=1)
H = nx.from_pandas_edgelist(gdf[m].assign(length=gdf[m].length), source="CdNoeudDeb", target="CdNoeudFin", edge_attr=["length"])


'''

# Plot
pos = nx.spring_layout(G_contract) 

fig, (ax1, ax2) = plt.subplots(1, 2, sharex=True, sharey=True)
nx.draw(G_contract, pos=pos, ax=ax1)
nx.draw(G_contract, pos={n: pos[n] for n in G_contract.nodes() if n in pos}, ax=ax2)

plt.show()
'''

print(len(Gc.nodes()), len(Gc.edges()),len(G.nodes()), len(G.edges()))
