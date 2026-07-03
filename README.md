# Graphe-hydrographique

Ce projet a pour but de générer un graphe hydrographique de la Seine, qui inclut aussi des stations de relevé de débit et de température de l'eau sur le fleuve et ses affluents. Ce travail est réalisé en se basant sur la base de données Topage du Gouvernement français.

Pour faire tourner le code, il est donc nécessaire de télécharger cette base de données (à l'URL suivant : https://services.sandre.eaufrance.fr/telechargement/geo/ETH/BDTopage/2024/BD_Topage_FXX_2024-shp.zip) et d'importer dans le repo github les fichiers CoursEau_FXX.shp et TronconHydrographique_FXX.shp. Il faut les mettre dans le .gitignore car ils sont très volumineux. Il est préférable de stocker l'ensemble de ces données dans un dossier "données hackaton", et de bien vérifier lors du chargement des fichiers dans le code python qu'il n'y a pas de problème dans les chemins indiqués (à adapter au besoin).

Il est aussi nécessaire d'importer le fichier (.shp ou.xlsx) contenant les stations de relevé de température, et leurs coordonnées géographiques. Les stations de débit sont quant à elles chargées via un URL. Une connexion internet stable est donc nécessaire pour le bon fontcionnement des codes.

Notre repo contient un notebook (notebook.ipynb), qui suit notre cheminement au cours de la semaine dans la construction du projet, et qui condense tous les codes nécessaires. Il permet de générer des fichiers .pickle des graphes, qui peuvent ensuite être utilisés pour réaliser une analyse de données. Ces .pickle contiennent aussi les utilitaires d'analyse de données.
Il contient aussi des modules séparées qui reprennent ces même codes, mais en les séparant. Ils sont stockés dans le dossier graphe_seine. Les ficheirs visu_dist.py et visu_oriented.py spermettent une visualisation plus interactive des graphes. 
C'est à l'utilisateur.ice de détrminer le format plus adapté à son usage (notebook ou module).

Enfin, on stocke dans le dossier Graphs les version successives du graphe au format .pickle, ainsi qu'une base de données au format geopackage (reseau_seine.gpkg) qui concatène les données de cours d'eau et des tronçons hydrographiques.