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

def dfs(graph, node):
    visited = set((node,))
    dg = nx.DiGraph()
    stack = [(node,0.,node)]
    dg.add_node(node)
    dg.nodes[node]["site_id"]=graph.nodes[node]["site_id"]
    dg.nodes[node]["dist_exut"] = 0.
    while stack:
        node,d,parent = stack.pop()
        if node not in visited:
            visited.add(node)
        for next_node,attrs in graph[node].items():
            if next_node not in visited:
                dg.add_edge(next_node,node,weight = attrs['weight'])
                dg.nodes[node]["site_id"] = graph.nodes[node].get("site_id")
                dg.nodes[next_node]["dist_exut"] = d + attrs['weight']
                stack.append((next_node,dg.nodes[node]["dist_exut"]))
    return dg



# Bassin de la seine
Seine_Code = "03C00000020008"
Root_Name = "Balise fond"

# %%
sites = gpd.read_file("Sites/Sites.shp").to_crs("EPSG:2154")

# %%
sites2 = sites[~sites.is_empty]

# %%
Gc = pickle.load(open('../Graphs/G_connexe_contracted.pickle', 'rb'))

root_node = sites2.loc[sites2["Libellé"] == Root_Name, "geometry"]
root_node = root_node.squeeze().coords[0]

OG = dfs(Gc,root_node)
pickle.dump(OG, open('ograph.pickle', 'wb'))
