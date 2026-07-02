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
import requests
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

gdf.update(pd.DataFrame.from_dict(patch, orient="index"))  # on applique les corrections sur le GeoDataFrame

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

riviere_map = {
    "Seine": "La Seine",
    "Marne": "La Marne",
    "Oise": "L'Oise",
    "Yonne": "L'Yonne",
    "Aube": "L'Aube",
    "Eure": "L'Eure",
    "Aisne": "L'Aisne"
}

sites["Riviere"] = sites["Riviere"].replace(riviere_map)
sites = sites.rename(columns={"Riviere": "libelle_cours_eau"})

sites

# %%
# Chargement des stations hydrométriques Hubeau pour "La Seine" uniquement

url_stations = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/referentiel/stations"
params_stations = {"format": "geojson", "size": 10000}

gj = requests.get(url_stations, params=params_stations, timeout=60).json()
gdf_hubeau = gpd.GeoDataFrame.from_features(gj["features"], crs="EPSG:4326")

# Filtre sur le libellé du cours d'eau : uniquement "La Seine"
cours_eau_retenus = ["La Seine", "L'Yonne", "La Marne", "L'Oise", "L'Aube","L'Eure","L'Aisne"]
gdf_hubeau = gdf_hubeau[gdf_hubeau["libelle_cours_eau"].isin(cours_eau_retenus)].copy()

# Reprojection en Lambert-93, clip à la bbox, dédoublonnage
gdf_hubeau = gdf_hubeau.to_crs("EPSG:2154")
gdf_hubeau = gdf_hubeau.clip(bbox)
gdf_hubeau = gdf_hubeau.drop_duplicates(subset="code_station")
gdf_hubeau = gdf_hubeau.rename(columns={"libelle_station": "Libellé"})
gdf_hubeau["source"] = "hubeau"

sites_hubeau = gdf_hubeau[["Libellé", "geometry", "source","libelle_cours_eau"]].reset_index(drop=True).copy()
print(f"{len(sites_hubeau)} stations Hubeau retenues sur la Seine, l'Yonne, la Marne, l'Aube, l'Eure, L'Aisne et l'Oise")

# %%
# Rattachement des sites existants et des stations Hubeau au réseau
# hydrographique, en un seul traitement unifié : pour chaque point,
# on cherche le tronçon le plus proche, on projette le point dessus,
# puis on découpe le tronçon. La coordonnée exacte insérée dans le
# tronçon est systématiquement récupérée (pour sites ET stations),
# afin d'éviter toute dérive de précision flottante entre les deux
# passes (snap/split/linemerge n'étant pas garantis stables bit-à-bit
# lorsqu'un même tronçon est retouché plusieurs fois).

sites2 = sites[~sites.is_empty].reset_index(drop=True).copy()
sites2["source"] = "sites_existants"

station_hydro = sites_hubeau[~sites_hubeau.is_empty].reset_index(drop=True).copy()
# station_hydro possède déjà une colonne "source" = "hubeau"

seine2 = seine.explode(ignore_index=True)
geom_col_s2 = seine2.columns.get_loc("geometry")

# Fusion sites + stations dans une seule collection, avec traçabilité
# de l'origine ("kind") et de l'index d'origine (pour retrouver site_id ensuite)
points = pd.concat(
    [
        sites2[["Libellé", "geometry", "source", "libelle_cours_eau"]]
            .assign(orig_index=sites2.index, kind="sites_existants"),
        station_hydro[["Libellé", "geometry", "source", "libelle_cours_eau"]]
            .assign(orig_index=station_hydro.index, kind="hubeau"),
    ],
    ignore_index=True,
)
points = gpd.GeoDataFrame(points, geometry="geometry", crs=seine2.crs)
geom_col_p = points.columns.get_loc("geometry")

# Recherche du tronçon le plus proche pour CHAQUE point (une seule fois,
# sur l'état initial de seine2)
pos1, pos2 = seine2.sindex.nearest(points["geometry"], return_all=False)

topo_touched = []  # TopoOH des tronçons ayant reçu au moins un point

for i1, i2 in zip(pos1, pos2):
    pt = points.iloc[i1, geom_col_p]
    ls = seine2.iloc[i2, geom_col_s2]

    proj_pt = ls.interpolate(ls.project(pt))   # projection du point sur la ligne
    snap_ls = snap(ls, proj_pt, 1e-6)          # on "accroche" la ligne au point projeté
    split_ls = split(snap_ls, proj_pt)         # on découpe la ligne au point projeté
    split_ls = linemerge(split_ls)

    # Récupération de la coordonnée EXACTE insérée dans split_ls
    # (appliqué systématiquement à TOUS les points, sites ET stations)
    if hasattr(split_ls, "geoms"):
        coords_array = np.array([c for geom in split_ls.geoms for c in geom.coords])
    else:
        coords_array = np.array(split_ls.coords)
    dists = np.linalg.norm(coords_array - np.array(proj_pt.coords[0]), axis=1)
    exact_coord = Point(coords_array[np.argmin(dists)])

    points.iloc[i1, geom_col_p] = exact_coord
    seine2.iloc[i2, geom_col_s2] = split_ls

    topo_touched.append(seine2.iloc[i2]["TopoOH"])

# On ne garde que les tronçons appartenant aux mêmes cours d'eau (TopoOH)
# que ceux ayant reçu au moins un point (site existant ou station Hubeau)
topo = pd.Series(topo_touched).dropna().drop_duplicates().to_list()
seine3 = seine2[seine2["TopoOH"].isin(topo)]

# Correction finale de précision : plusieurs points peuvent tomber sur un
# même tronçon d'origine. Lorsqu'un tronçon est splitté/linemerge plusieurs
# fois de suite (un point après l'autre), le vertex du premier point inséré
# peut subir une micro-dérive flottante lors du traitement du point suivant.
# Plutôt que de rechercher le vertex le plus proche, on normalise toutes les
# coordonnées utilisées comme clés de nœud via snap_key() : cette dérive est
# de l'ordre de 1e-9 à 1e-12, largement absorbée par l'arrondi à 6 décimales.

# On resépare sites2 / station_hydro à partir de "points"
sites2 = (
    points[points["kind"] == "sites_existants"]
    .set_index("orig_index")[["Libellé", "geometry", "source", "libelle_cours_eau"]]
)
station_hydro = (
    points[points["kind"] == "hubeau"]
    .set_index("orig_index")[["Libellé", "geometry", "source", "libelle_cours_eau"]]
)

seine3

# %%
G = nx.Graph()

# chaque point de la LineString devient un nœud du graphe,
# chaque segment devient une arête avec un poids égal à sa longueur

for _, row in tqdm(seine3.iterrows(), total=len(seine3)):
    geom = row.geometry
    for i, j in zip(geom.coords, geom.coords[1:]):
        i, j = snap_key(i), snap_key(j)
        G.add_edge(i, j, weight=LineString([i, j]).length)

# %%
root_node = sites2.loc[sites2["Libellé"] == Root_Name, "geometry"]
root_node = snap_key(root_node.squeeze().coords[0])

site_nodes = []

# Ajout des sites existants comme nœuds du graphe
for site in sites2.itertuples():
    coord = snap_key(site.geometry.coords[0])
    attrs = G.nodes[coord]
    attrs["site_id"] = site.Index
    attrs["label"] = site.Libellé
    attrs["libelle_cours_eau"] = site.libelle_cours_eau
    attrs["source"] = "sites_existants"
    site_nodes.append(coord)

# Ajout des stations Hubeau comme nœuds du graphe
# (snap_key absorbe les micro-dérives flottantes issues des splits successifs)
for station in station_hydro.itertuples():
    coord = snap_key(station.geometry.coords[0])
    attrs = G.nodes[coord]
    attrs["site_id"] = station.Index
    attrs["label"] = station.Libellé
    attrs["libelle_cours_eau"] = station.libelle_cours_eau
    attrs["source"] = "hubeau"
    site_nodes.append(coord)

# %%
site_nodes

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