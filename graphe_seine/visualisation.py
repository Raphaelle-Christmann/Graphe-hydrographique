# visualisation.py — a besoin de :
import matplotlib.pyplot as plt
import networkx as nx
import pickle
from contracter import contract

G = pickle.load(open('graph.pickle', 'rb'))
G_contract = pickle.load(open('contract.pickle', 'rb'))

# %%
# Affichage avec les positions géographiques réelles (centroïdes des tronçons)
# On ne garde que les positions des nœuds présents dans G_contract
pos_contract = {n: n for n in G_contract.nodes()}

# Couleur différente pour les nœuds (sites en orange, hubeau en vert, autres en rouge)
def get_color(n):
    source = G_contract.nodes[n].get("source")
    if source == "sites_existants":
        return "tab:orange"
    elif source == "hubeau":
        return "tab:green"
    else:
        return "tab:red"

node_colors = [get_color(n) for n in G_contract.nodes()]
node_sizes = [40 if G_contract.nodes[n].get("site_id") is not None else 5 
              for n in G_contract.nodes()]

fig, ax = plt.subplots(figsize=(12, 12))
nx.draw(
    G_contract,
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