#!/usr/bin/python
"""
Optimized (Unroll-4) version of Breadth-First Search.
Reference baseline: Omkar Pathak BFS.
Optimizations:
  - replace queue.Queue() with collections.deque (no thread locks)
  - unroll adjacency loop by 4 neighbors per iteration
"""

from __future__ import annotations
from collections import deque


class Graph:
    def __init__(self) -> None:
        self.vertices: dict[int, list[int]] = {}

    def print_graph(self) -> None:
        for i in self.vertices:
            print(i, " : ", " -> ".join([str(j) for j in self.vertices[i]]))

    def add_edge(self, from_vertex: int, to_vertex: int) -> None:
        if from_vertex in self.vertices:
            self.vertices[from_vertex].append(to_vertex)
        else:
            self.vertices[from_vertex] = [to_vertex]

    def bfs(self, start_vertex: int) -> set[int]:
        """
        >>> g = Graph()
        >>> g.add_edge(0, 1)
        >>> g.add_edge(0, 2)
        >>> g.add_edge(1, 2)
        >>> g.add_edge(2, 0)
        >>> g.add_edge(2, 3)
        >>> g.add_edge(3, 3)
        >>> sorted(g.bfs(2))
        [0, 1, 2, 3]
        """
        visited = set()
        queue: deque[int] = deque()

        visited.add(start_vertex)
        queue.append(start_vertex)

        while queue:
            vertex = queue.popleft()
            neighbors = self.vertices.get(vertex, [])
            n = len(neighbors)
            i = 0
            # unroll adjacency visits 4 at a time
            while i + 3 < n:
                v0, v1, v2, v3 = neighbors[i:i+4]
                if v0 not in visited:
                    visited.add(v0)
                    queue.append(v0)
                if v1 not in visited:
                    visited.add(v1)
                    queue.append(v1)
                if v2 not in visited:
                    visited.add(v2)
                    queue.append(v2)
                if v3 not in visited:
                    visited.add(v3)
                    queue.append(v3)
                i += 4
            # remaining neighbors
            while i < n:
                v = neighbors[i]
                if v not in visited:
                    visited.add(v)
                    queue.append(v)
                i += 1
        return visited


if __name__ == "__main__":
    from doctest import testmod

    testmod(verbose=True)

    g = Graph()
    g.add_edge(0, 1)
    g.add_edge(0, 2)
    g.add_edge(1, 2)
    g.add_edge(2, 0)
    g.add_edge(2, 3)
    g.add_edge(3, 3)

    g.print_graph()
    assert sorted(g.bfs(2)) == [0, 1, 2, 3]
