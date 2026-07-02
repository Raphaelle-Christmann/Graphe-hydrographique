# visualisation.py — a besoin de :
import matplotlib.pyplot as plt
import networkx as nx
import pickle

OG = pickle.load(open('ograph.pickle', 'rb'))

# %%
# Affichage avec les positions géographiques réelles (centroïdes des tronçons)
# On ne garde que les positions des nœuds présents dans OG
pos_contract = {n: n for n in OG.nodes()}

# Couleur différente pour les nœuds correspondant à des stations (sites)
node_colors = [
    "tab:blue" if OG.nodes[n].get("libelle_cours_eau")=="La Seine"
    else "tab:orange" if OG.nodes[n].get("libelle_cours_eau")=="L'Yonne"
    else "tab:purple" if OG.nodes[n].get("libelle_cours_eau")=="L'Aube"
    else "tab:brown" if OG.nodes[n].get("libelle_cours_eau")=="L'Eure"
    else "tab:cyan" if OG.nodes[n].get("libelle_cours_eau")=="L'Aisne"
    else "tab:olive" if OG.nodes[n].get("libelle_cours_eau")=="L'Oise"
      else "tab:red" if OG.nodes[n].get("libelle_cours_eau")=="La Marne" else "tab:green" if OG.nodes[n].get("site_id") is not None else "tab:gray"
    for n in OG.nodes()
]
node_sizes = [
    40 if OG.nodes[n].get("site_id") is not None else 5
    for n in OG.nodes()
]

fig, ax = plt.subplots(figsize=(12, 12))
nx.draw(
    OG,
    pos=pos_contract,
    ax=ax,
    node_color=node_colors,
    node_size=node_sizes,
    edge_color="tab:blue",
    width=0.5,
    with_labels=False,
)
ax.set_aspect("equal")
plt.show()
