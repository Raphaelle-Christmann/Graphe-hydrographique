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

#NECESSITE LA PRESENCE DU GRAPHE CONTRACTÉ


import pickle
import geopandas as gpd
import networkx as nx

def snap_key(coord, ndigits=6):
    return (round(coord[0], ndigits), round(coord[1], ndigits))


def dfs(graph, node):
    visited = set((node,))
    dg = nx.DiGraph()
    stack = [(node,0.,node)]
    dg.add_node(node)
    dg.nodes[node]["site_id"]=graph.nodes[node]["site_id"]
    dg.nodes[node]["source"]=graph.nodes[node].get("source")
    dg.nodes[node]["libelle_cours_eau"]=graph.nodes[node].get("libelle_cours_eau")
    dg.nodes[node]["dist_exut"] = 0.
    while stack:
        node,d,parent = stack.pop()
        if node not in visited:
            visited.add(node)
        for next_node,attrs in graph[node].items():
            if next_node not in visited:
                if graph.nodes[next_node].get("site_id") is not None :
                    dg.add_edge(next_node,parent,weight = d + attrs["weight"])
                    dg.nodes[next_node]["site_id"] = graph.nodes[next_node].get("site_id")
                    dg.nodes[next_node]["source"] = graph.nodes[next_node].get("source")
                    dg.nodes[next_node]["libelle_cours_eau"] = graph.nodes[next_node].get("libelle_cours_eau")
                    dg.nodes[next_node]["dist_exut"] = d + dg.nodes[parent].get("dist_exut")
                    stack.append((next_node,0.,next_node))
                else :
                    stack.append((next_node,d+attrs["weight"],parent))
    return dg


def debit(graph, s):
    visited = set((s,))
    stations = []
    stack = [s]
    if graph.nodes[s].get("source") == "hubeau" :
        graph.nodes[s]["debits"] = [s]
        return
    else :
        while stack:
            node = stack[-1]
            stack.pop()
            if node not in visited:
                visited.add(node)
            for next_node in graph.predecessors(node):
                if next_node not in visited:
                    if graph.nodes[next_node].get("source") == "hubeau" :
                        stations.append(next_node)
                    else :
                        stack.append(next_node)
        graph.nodes[s]["debits"] = stations

def debits(graph) :
    for n in graph.nodes :
        debit(graph,n)


# Bassin de la seine
Seine_Code = "03C00000020008"
Root_Name = "Balise fond"

# %%
sites = gpd.read_file("Sites/Sites.shp").to_crs("EPSG:2154")

# %%
sites2 = sites[~sites.is_empty]

# %%
# Gc = pickle.load(open('contract.pickle', 'rb'))
Gc = pickle.load(open('../Graphs/G_connexe_contracted.pickle', 'rb'))

root_node = sites2.loc[sites2["Libellé"] == Root_Name, "geometry"]
root_node = root_node.squeeze().coords[0]


OG = dfs(Gc,snap_key(root_node))


debits(OG)

# pickle.dump(OG, open('ograph.pickle', 'wb'))
pickle.dump(OG, open('../Graphs/G_oriented.pickle', 'wb'))

