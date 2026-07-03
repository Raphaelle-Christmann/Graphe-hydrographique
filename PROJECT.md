Ce projet a pour but de faciliter l'analyse des données utilisées par les chercheureuses en hydrographie.
A partir d'une carte des cours d'eau du bassin versant de la Seine sous la forme d'une liste de segments et ainsi que de la liste de sites de mesures (pour le moment, thermique et de débit) que nous intégrons par projection sur les cours d'eau. Les chercheureuses peuvent mettre à jour ces données, notamment lors de la mise en place de nouvelles stations. Notre travail a consisté à générer un graphe orienté et simplifié dans le sens de l'écoulement de l'eau. Nous avons de plus implémenté différentes fonctionnalités en utilisant ce nouveau graphe, à la demande des chercheureuses que nous avons rencontré.
Notamment : La distance à l'exutoire le long des cours d'eau,
            Les sites de mesures de débits présents immédiatement en amont,
            Le noms du cours d'eau sur lequel est présent le site
Les arêtes reliant les sites possèdent les poids adaptés correspondant  à la distance les séparant le long des cours d'eau.

Une part importante du calcul a été de trouver une solution pour prendre en compte deux bases de données (CoursEau et TronconsHydrographiques) afin d'augmenter la connexité du graphe.

A noter que le calcul de cette fusion prend un temps relativement important mais n'est nécessaire que lors de l'ajout de nouveaux sites, une piste d'amélioration serait de simplifier ce calcul ou de faire une concession sur la base de données utilisées pour représenter les cours d'eau, TronconsHydrographiques semble relativement suffisant.
En effet G_connexe_non_contracted.pickle contient l'entiéreté des informations des bases de données et n'est généré qu'une fois.
Le graphe plus lisible et manipulable plus rapidement (G_oriented_par_tr.pickle) que nous calculons ne contient comme sommets que les différents sites de mesures, et peut permettre rapidement à l'utilisateurices de calculer de nouvelles informations.

La visualisation de l'ensemble de ces informations peut être obtenue rapidement en lançant visu_oriented.py