# Graphe-hydrographique

Ce projet a pour but de générer un graphe hydrographique de la Seine, qui inclut aussi des stations de relevé de débit et de température de l'eau sur le fleuve et ses afluents. Ce travail est réalisé en se basant sur la base de données Topage du Gouvernement français.

Pour faire tourner le code, il est donc nécessaire de télécharger cette base de données (à l'URL suivant : https://services.sandre.eaufrance.fr/telechargement/geo/ETH/BDTopage/2024/BD_Topage_FXX_2024-shp.zip) et d'importer dans le repo github les fichiers CoursEau_FXX.shp et TronconHydrographique_FXX.shp. Il faut les mettre dans le .gitignore car ils sont très volumineux. Il faut stocker l'ensemble de ces données dans un dossier données hackaton, 

Il est aussi nécessaire d'importer le fichier (.shp ou.xlsx) contenant les stations de relevé de température, et leurs coordonnées géographiques.

Notre repo contient un notebook qui suit notre cheminement au cours de la semaine dans la construction du projet, et qui condense