# visualisation.py — a besoin de :
import matplotlib.pyplot as plt
import networkx as nx
import pickle

OG = pickle.load(open('ograph.pickle', 'rb'))

# %%
# Affichage avec les positions géographiques réelles (centroïdes des tronçons)
# On ne garde que les positions des nœuds présents dans OG
pos_contract = {n: n for n in OG.nodes()}

# Couleur différente pour les nœuds correspondant à des stations
node_colors = [
    "tab:blue" if OG.nodes[n].get("source")== "hubeau" else "tab:red"
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
