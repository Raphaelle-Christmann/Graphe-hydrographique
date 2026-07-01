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
    stack = [node]
    while stack:
        node = stack[-1]
        if node not in visited:
            visited.add(node)
        remove_from_stack = True
        for next_node in graph[node]:
            if next_node not in visited:
                stack.append(next_node)
                print(node)
                dg.add_edge(node,next_node)
                dg.nodes[node]["site_id"] = graph.nodes[node].get("site_id")
                remove_from_stack = False
                break
        if remove_from_stack:
            stack.pop()
    return dg



# Bassin de la seine
Seine_Code = "03C00000020008"
Root_Name = "Balise fond"

# %%
sites = gpd.read_file("Sites/Sites.shp").to_crs("EPSG:2154")

# %%
sites2 = sites[~sites.is_empty]

# %%
G = pickle.load(open('graph.pickle', 'rb'))
Gc = pickle.load(open('contract.pickle', 'rb'))

root_node = sites2.loc[sites2["Libellé"] == Root_Name, "geometry"]
root_node = root_node.squeeze().coords[0]

OG = dfs(Gc,root_node)
pickle.dump(OG, open('ograph.pickle', 'wb'))
