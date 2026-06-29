# +
import pathlib
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import pyproj
import networkx as nx
from shapely import Point, LineString, MultiLineString, GeometryCollection
from shapely.ops import split, snap, linemerge
from tqdm.auto import tqdm

TEMP_DATA = pathlib.Path("Temper_Data")

# +
# Bassin de la seine
Code_OH = "03C00000020008"
Root_Name = "Balise fond"

gdf = gpd.read_file('../gis/CoursEau_FXX.shp')

m = gdf['CdOH'].str.startswith(Code_OH)
seine = gdf[m].copy()
seine
# -

crs = pyproj.crs.CRS('EPSG:2154')
sites = pd.read_csv(TEMP_DATA / "Tab-Sites.csv", dtype={'Code': 'str'})
geom = gpd.GeoSeries.from_xy(sites['XLAMB93'], sites['YLAMB93'], crs=crs)
sites = gpd.GeoDataFrame(sites, geometry=geom)
sites

# +
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

# gid = seine2.loc[seine2.index[pos2], "gid"]
topo = seine2.loc[seine2.index[pos2], "TopoOH"].drop_duplicates().to_list()
seine3 = seine2[seine2["TopoOH"].isin(topo)]
seine3

# +
G = nx.Graph()

for _, row in tqdm(seine3.iterrows(), total=len(seine3)):
    geom = row.geometry
    for i, j in zip(geom.coords, geom.coords[1:]):
        G.add_edge(i, j, weight=LineString([i, j]).length)

# +
root_node = sites2.loc[sites2["Libellé"] == "Balise fond", "geometry"]
root_node = root_node.squeeze().coords[0]

site_nodes = []
for site in sites2.itertuples():
    coord = site.geometry.coords[0]  # Point
    attrs = G.nodes[coord]
    attrs["site_id"] = site.Index
    attrs["label"] = site.Libellé
    site_nodes.append(coord)
# -

colors = []
for site in site_nodes:
    attrs = G.nodes[site]
    print(f"Vers {attrs['label']}")
    if nx.has_path(G, root_node, site):
        path = nx.shortest_path(G, root_node, site, weight="weight")
        colors.append("green")
    else:
        print("Aucun chemin trouvé")
        colors.append("red")
    print()

fig, ax = plt.subplots(figsize=(12, 12), dpi=600)
seine3.plot(ax=ax, lw=0.5, color='lightblue', zorder=-1)
sites2.plot(ax=ax, lw=0.5, color=colors, markersize=5)
ax.ticklabel_format(style='plain', axis='both') 
fig.savefig("seine.png")
plt.show()

sites2.sort_values("Libellé").head(40)
