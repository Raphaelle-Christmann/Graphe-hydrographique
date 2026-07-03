# visu_oriented.py — a besoin de :
import matplotlib.pyplot as plt
import networkx as nx
import pickle

OG = pickle.load(open('ograph.pickle', 'rb'))

# %%
# Affichage avec les positions géographiques réelles (centroïdes des tronçons)
pos_contract = {n: n for n in OG.nodes()}

# Couleur différente pour les nœuds correspondant à des stations (sites)
node_colors = [
    "tab:blue" if OG.nodes[n].get("libelle_cours_eau")=="La Seine"
    else "tab:orange" if OG.nodes[n].get("libelle_cours_eau")=="L'Yonne"
    else "tab:purple" if OG.nodes[n].get("libelle_cours_eau")=="L'Aube"
    else "tab:brown" if OG.nodes[n].get("libelle_cours_eau")=="L'Eure"
    else "tab:cyan" if OG.nodes[n].get("libelle_cours_eau")=="L'Aisne"
    else "tab:olive" if OG.nodes[n].get("libelle_cours_eau")=="L'Oise"
    else "tab:red" if OG.nodes[n].get("libelle_cours_eau")=="La Marne"
    else "tab:green" if OG.nodes[n].get("site_id") is not None else "tab:gray"
    for n in OG.nodes()
]
node_sizes = [
    40 if OG.nodes[n].get("site_id") is not None else 5
    for n in OG.nodes()
]

# Liste des nœuds "station" (ceux pour lesquels on veut un tooltip au survol)
station_nodes = [n for n in OG.nodes() if OG.nodes[n].get("site_id") is not None]
station_colors = [c for n, c in zip(OG.nodes(), node_colors) if n in station_nodes]

fig, ax = plt.subplots(figsize=(12, 12))

# Arêtes (les flèches sont retirées exactement à la taille de chaque nœud
# cible, grâce à node_size, pour que leur extrémité touche le nœud sans le dépasser)
nx.draw_networkx_edges(
    OG, pos=pos_contract, ax=ax,
    edge_color="tab:blue", width=0.5,
    node_size=node_sizes,
    arrowsize=8,
)
# Nœuds stations : dessinés à part via scatter pour pouvoir détecter le survol
station_xy = [pos_contract[n] for n in station_nodes]
station_scatter = ax.scatter(
    [xy[0] for xy in station_xy],
    [xy[1] for xy in station_xy],
    c=station_colors,
    s=40,
    zorder=3,
)

ax.set_aspect("equal")

# --- Tooltip au survol ---
annot = ax.annotate(
    "", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
    bbox=dict(boxstyle="round", fc="lightyellow", ec="0.5"),
    arrowprops=dict(arrowstyle="->"),
    fontsize=9,
)
annot.set_visible(False)


def format_station_info(node):
    """Construit le texte du tooltip pour une station donnée."""
    data = OG.nodes[node]
    debits_list = data.get("debits", [])
    lines = [
        f"type de station : {data.get('source', '(non renseigné)')}",
        f"coordonnées : {node}",
        f"cours d'eau : {data.get('libelle_cours_eau', '(non renseigné)')}",
        f"distance à l'exut : {data.get('dist_exut', 0.)/1000:.2f} km",
        "station de débit la plus proche :",
    ]
    if debits_list:
        lines += [f"  {d}" for d in debits_list]
    else:
        lines.append("(aucune station amont)")
    return "\n".join(lines)


def on_hover(event):
    if event.inaxes != ax:
        if annot.get_visible():
            annot.set_visible(False)
            fig.canvas.draw_idle()
        return

    cont, ind = station_scatter.contains(event)
    if cont:
        idx = ind["ind"][0]
        node = station_nodes[idx]
        annot.xy = pos_contract[node]
        annot.set_text(format_station_info(node))
        annot.set_visible(True)
        fig.canvas.draw_idle()
    else:
        if annot.get_visible():
            annot.set_visible(False)
            fig.canvas.draw_idle()


fig.canvas.mpl_connect("motion_notify_event", on_hover)

plt.show()