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

def snap_key(coord, ndigits=6):
    """
    Arrondit une coordonnée (x, y) à `ndigits` décimales, pour l'utiliser
    comme clé de nœud stable dans le graphe. En Lambert-93 (EPSG:2154),
    les coordonnées sont exprimées en mètres : 6 décimales correspond donc
    à une précision de l'ordre du micromètre, largement suffisante pour
    absorber les micro-dérives flottantes introduites par des opérations
    géométriques successives (snap/split/linemerge) sans jamais confondre
    deux vertices réellement distincts.
    """
    return (round(coord[0], ndigits), round(coord[1], ndigits))


def dfs(graph, node):
    visited = set((node,))
    dg = nx.DiGraph()
    stack = [(node,0.,node)]
    dg.add_node(node)
    dg.nodes[node]["site_id"]=graph.nodes[node]["site_id"]
    dg.nodes[node]["source"]=graph.nodes[node].get("source")
    dg.nodes[node]["dist_exut"] = 0.
    while stack:
        node,d,parent = stack.pop()
        if node not in visited:
            visited.add(node)
        for next_node,attrs in graph[node].items():
            if next_node not in visited:
                if graph.nodes[next_node].get("site_id") is not None :
                    dg.add_edge(next_node,parent,weight = d + attrs["weight"])
                    dg.nodes[next_node]["site_id"] = graph.nodes[next_node].get("site_id")
                    dg.nodes[next_node]["source"] = graph.nodes[next_node].get("source")
                    dg.nodes[next_node]["dist_exut"] = d + dg.nodes[parent].get("dist_exut")
                    stack.append((next_node,0.,next_node))
                else :
                    stack.append((next_node,d+attrs["weight"],parent))
    return dg



# Bassin de la seine
Seine_Code = "03C00000020008"
Root_Name = "Balise fond"

# %%
sites = gpd.read_file("Sites/Sites.shp").to_crs("EPSG:2154")

# %%
sites2 = sites[~sites.is_empty]

# %%
Gc = pickle.load(open('contract.pickle', 'rb'))

root_node = sites2.loc[sites2["Libellé"] == Root_Name, "geometry"]
root_node = root_node.squeeze().coords[0]


OG = dfs(Gc,snap_key(root_node))


def debit(graph, s):
    visited = set((s,))
    stations = []
    stack = [s]
    while stack:
        node = stack[-1]
        stack.pop()
        if node not in visited:
            visited.add(node)
        for next_node in graph.predecessors(node):
            if next_node not in visited:
                if graph.nodes[next_node].get("source") == "hubeau" :
                    stations.append(next_node)
                else :
                    stack.append(next_node)
    graph.nodes[s]["debits"] = stations

def debits(graph) :
    for n in graph.nodes :
      if graph.nodes[n].get("source") == "sites_existants" :
        debit(graph,n)

debits(OG)
pickle.dump(OG, open('ograph.pickle', 'wb'))
