import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import networkx as nx
import pickle

OG = pickle.load(open('ograph.pickle', 'rb'))
# Récupération des valeurs de dist_exut pour chaque nœud
dist_exut_values = [OG.nodes[n].get("dist_exut",0.) for n in OG.nodes()]

pos_contract = {n: n for n in OG.nodes()}
# Normalisation des valeurs pour la colormap
norm = mcolors.Normalize(vmin=min(dist_exut_values), vmax=max(dist_exut_values))
cmap = cm.viridis  # tu peux changer pour "plasma", "coolwarm", "turbo", etc.

node_colors = [cmap(norm(v)) for v in dist_exut_values]

# Taille toujours différenciée stations / autres
node_sizes = [
    40 if OG.nodes[n].get("site_id") is not None else 0
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

# Ajout d'une colorbar pour interpréter les couleurs
sm = cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.7)
cbar.set_label("dist_exut")

ax.set_aspect("equal")
plt.show()
