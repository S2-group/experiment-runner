import heapq
from numba import jit
from numba.typed import Dict, List
from numba.types import unicode_type, int64, ListType
import numba

@jit(nopython=True)
def dijkstra_core(edges_dict, start_idx, end_idx, node_count):
    INF = 999999
    distances = [INF] * node_count
    distances[start_idx] = 0
    visited = [False] * node_count
    
    for _ in range(node_count):
        min_dist = INF
        min_node = -1
        
        for i in range(node_count):
            if not visited[i] and distances[i] < min_dist:
                min_dist = distances[i]
                min_node = i
        
        if min_node == -1:
            break
            
        visited[min_node] = True
        
        if min_node == end_idx:
            return distances[end_idx]
            
        for neighbor, weight in edges_dict[min_node]:
            if not visited[neighbor]:
                new_dist = distances[min_node] + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
    
    return -1 if distances[end_idx] == INF else distances[end_idx]

def dijkstra(graph, start, end):
    nodes = list(set([start, end] + [node for node in graph.keys()]))
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    
    edges_dict = numba.typed.Dict.empty(
        key_type=numba.types.int64,
        value_type=numba.types.ListType(numba.types.Tuple([numba.types.int64, numba.types.int64]))
    )
    
    for i in range(len(nodes)):
        edges_dict[i] = numba.typed.List.empty_list(
            numba.types.Tuple([numba.types.int64, numba.types.int64])
        )
    
    for node, neighbors in graph.items():
        if node in node_to_idx:
            node_idx = node_to_idx[node]
            for neighbor_info in neighbors:
                neighbor, weight = neighbor_info
                if neighbor in node_to_idx:
                    neighbor_idx = node_to_idx[neighbor]
                    edges_dict[node_idx].append((neighbor_idx, weight))
    
    start_idx = node_to_idx[start]
    end_idx = node_to_idx[end]
    
    return dijkstra_core(edges_dict, start_idx, end_idx, len(nodes))

G = {
    "A": [["B", 2], ["C", 5]],
    "B": [["A", 2], ["D", 3], ["E", 1], ["F", 1]],
    "C": [["A", 5], ["F", 3]],
    "D": [["B", 3]],
    "E": [["B", 4], ["F", 3]],
    "F": [["C", 3], ["E", 3]],
}

G2 = {
    "B": [["C", 1]],
    "C": [["D", 1]],
    "D": [["F", 1]],
    "E": [["B", 1], ["F", 3]],
    "F": [],
}

G3 = {
    "B": [["C", 1]],
    "C": [["D", 1]],
    "D": [["F", 1]],
    "E": [["B", 1], ["G", 2]],
    "F": [],
    "G": [["F", 1]],
}

if __name__ == "__main__":
    import time

    for _ in range(10000):
        dijkstra(G, "E", "C")
        dijkstra(G2, "E", "F")
        dijkstra(G3, "E", "F")
    print(time.time())
    for _ in range(10000):
        dijkstra(G, "E", "C")
        dijkstra(G2, "E", "F")
        dijkstra(G3, "E", "F")