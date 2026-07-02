# Chargement des stations hydrométriques Hubeau pour "La Seine"
import requests
import geopandas as gpd

url_stations = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/referentiel/stations"
params_stations = {"format": "geojson", "size": 10000}

gj = requests.get(url_stations, params=params_stations, timeout=60).json()
gdf_hubeau = gpd.GeoDataFrame.from_features(gj["features"], crs="EPSG:4326")

# Filtre sur le libellé du cours d'eau : uniquement "La Seine"
gdf_hubeau = gdf_hubeau[gdf_hubeau["libelle_cours_eau"] == "La Marne"].copy()

# Reprojection en Lambert-93, clip à la bbox, dédoublonnage
gdf_hubeau = gdf_hubeau.to_crs("EPSG:2154")
gdf_hubeau = gdf_hubeau.drop_duplicates(subset="code_station")
gdf_hubeau = gdf_hubeau.rename(columns={"libelle_station": "Libellé"})
gdf_hubeau["source"] = "hubeau"

sites_hubeau = gdf_hubeau[["Libellé", "geometry", "source"]].reset_index(drop=True).copy()
print(f"{len(sites_hubeau)} stations Hubeau retenues sur La Seine")

