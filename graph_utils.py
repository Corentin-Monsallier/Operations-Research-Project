from collections import deque


def build_graph(proposal):
    """
    Build a bipartite graph from the transportation proposal
    """
    n = len(proposal)
    m = len(proposal[0])

    graph = {}

    for i in range(n):
        graph[f"S{i}"] = []
    for j in range(m):
        graph[f"C{j}"] = []

    for i in range(n):
        for j in range(m):
            if proposal[i][j] is not None:
                s = f"S{i}"
                c = f"C{j}"

                graph[s].append(c)
                graph[c].append(s)

    return graph


def display_graph(proposal):
    
    print("\nTRANSPORT GRAPH:")

    n = len(proposal)
    m = len(proposal[0])

    edges = []

    for i in range(n):
        for j in range(m):
            if proposal[i][j] is not None:
                edges.append(f"S{i+1} -- C{j+1} ({proposal[i][j]})")

    if not edges:
        print("No edges")
        return

    for e in edges:
        print(e)



def find_connected_components(graph):
    """
    Find all connected components using BFS
    """
    visited = set()
    components = []

    for start in graph:
        if start not in visited:
            queue = deque([start])
            component = []

            while queue:
                node = queue.popleft()

                if node not in visited:
                    visited.add(node)
                    component.append(node)

                    for neighbor in graph[node]:
                        if neighbor not in visited:
                            queue.append(neighbor)

            components.append(component)

    return components


def _display_node(node):
    return f"{node[0]}{int(node[1:]) + 1}"



def connect_graph(problem, proposal):
    costs = problem["costs"]
    all_edges = []
    for i in range(problem["n"]):
        for j in range(problem["m"]):
            if proposal[i][j] is None:
                all_edges.append((costs[i][j], i, j))
    all_edges.sort() 
    
    for cost, i, j in all_edges:
        graph = build_graph(proposal)
        components = find_connected_components(graph)
        if len(components) == 1: break
        
        s, c = f"S{i}", f"C{j}"
        comp_s = next(comp for comp in components if s in comp)
        comp_c = next(comp for comp in components if c in comp)
        
        if comp_s != comp_c:
            proposal[i][j] = 0 
    return proposal



def test_connectivity(proposal):
    graph = build_graph(proposal)
    components = find_connected_components(graph)

    print("\n=== CONNECTIVITY TEST ===")

    if len(components) == 1:
        print("Graph is already connected.")
    else:
        print("Graph is NOT connected.")

        print("\nConnected sub-graphs:")
        for i, comp in enumerate(components):
            print(f"Subgraph {i+1}: ", end="")

            readable = []
            for node in comp:
                readable.append(_display_node(node))

            print(readable)
