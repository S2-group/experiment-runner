# cython: language_level=3
import heapq
from typing import Dict, List, Tuple

cdef int dijkstra_cython(dict graph, str start, str end):
    cdef list heap = [(0, start)]
    cdef set visited = set()
    cdef int cost
    cdef str u, v
    cdef int c, next_item
    
    while heap:
        cost, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        if u == end:
            return cost
        for edge in graph[u]:
            v, c = edge
            if v in visited:
                continue
            next_item = cost + c
            heapq.heappush(heap, (next_item, v))
    return -1

def dijkstra(graph, start, end):
    return dijkstra_cython(graph, start, end)

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

short_distance = dijkstra(G, "E", "C")
print(short_distance)

short_distance = dijkstra(G2, "E", "F")
print(short_distance)

short_distance = dijkstra(G3, "E", "F")
print(short_distance)

if __name__ == "__main__":
    import doctest
    doctest.testmod()