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
from shapely import Point, LineString, MultiLineString, GeometryCollection, box
from shapely.ops import split, snap, linemerge
from tqdm.auto import tqdm

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
G = nx.Graph()

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

# %%
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


def contract(g):
    """
    Contract chains of neighbouring vertices with degree 2 into a single edge.

    Arguments:
    ----------
    g -- networkx.Graph or networkx.DiGraph instance

    Returns:
    --------
    h -- networkx.Graph or networkx.DiGraph instance
        the contracted graph
    """

    # Travailler sur la version non orientée pour identifier les chaînes
    ug = g.to_undirected() if g.is_directed() else g

    # Créer le sous-graphe des nœuds de degré 2
    is_chain = [node for node, degree in ug.degree() if ((degree == 2) and (G.nodes[node].get("site_id") is None))]
    chains = ug.subgraph(is_chain)

    # Correction : connected_component_subgraphs supprimé en NX 2.4+
    # On applique connected_components sur chains (pas sur g)
    components = [chains.subgraph(c) for c in nx.connected_components(chains)]

    hyper_edges = []
    for component in components:
        end_points = [node for node, degree in component.degree() if degree < 2]
        candidates = set(neighbor for node in end_points for neighbor in ug.neighbors(node))
        connectors = list(candidates - set(component.nodes()))
        weights = [data.get('weight', 1) for _, _, data in component.edges(data=True)]
        hyper_edges.append((connectors, np.sum(weights)))

    # Initialiser le nouveau graphe sans les nœuds de degré 2
    not_chain = [node for node in g.nodes() if node not in is_chain]
    h = g.subgraph(not_chain).copy()
    for connectors, weight in hyper_edges:
        # Garde-fou : une chaîne en bout de graphe peut avoir < 2 connecteurs
        if len(connectors) == 2:
            h.add_edge(connectors[0], connectors[1], weight=weight)

    return h


# Contraction
G_contract = contract(G)

'''

# Plot
pos = nx.spring_layout(G_contract) 

fig, (ax1, ax2) = plt.subplots(1, 2, sharex=True, sharey=True)
nx.draw(G_contract, pos=pos, ax=ax1)
nx.draw(G_contract, pos={n: pos[n] for n in G_contract.nodes() if n in pos}, ax=ax2)

plt.show()
'''

print(len(G_contract.nodes()), len(G_contract.edges()),len(G.nodes()), len(G.edges()))
