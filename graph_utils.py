from collections import deque

# --------------------------------------------------
# BUILD GRAPH
# --------------------------------------------------

def build_graph(proposal):
    """
    Build a bipartite graph from the transportation proposal
    """
    n = len(proposal)
    m = len(proposal[0])

    graph = {}

    # Create nodes
    for i in range(n):
        graph[f"S{i}"] = []
    for j in range(m):
        graph[f"C{j}"] = []

    # Add edges
    for i in range(n):
        for j in range(m):
            if proposal[i][j] is not None:
                s = f"S{i}"
                c = f"C{j}"

                graph[s].append(c)
                graph[c].append(s)

    return graph

# --------------------------------------------------
# DISPLAY GRAPH
# --------------------------------------------------

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


# --------------------------------------------------
# CONNECTED COMPONENTS (BFS)
# --------------------------------------------------

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


# --------------------------------------------------
# CONNECT GRAPH (FIX NON-CONNECTED)
# --------------------------------------------------

def connect_graph(problem, proposal):
    costs = problem["costs"]

    while True:
        graph = build_graph(proposal)
        components = find_connected_components(graph)

        # If already connected => stop
        if len(components) == 1:
            print("\nGraph is now connected.")
            break

        print("\nGraph not connected => we add the edges:")

        best_edge = None
        best_cost = float("inf")

        # Try all non-basic cells
        for i in range(problem["n"]):
            for j in range(problem["m"]):

                if proposal[i][j] is None:

                    s = f"S{i}"
                    c = f"C{j}"

                    comp_s = None
                    comp_c = None

                    # Find components of S and C
                    for comp in components:
                        if s in comp:
                            comp_s = comp
                        if c in comp:
                            comp_c = comp

                    # Only connect different components
                    if comp_s != comp_c:
                        if costs[i][j] < best_cost:
                            best_cost = costs[i][j]
                            best_edge = (i, j)

        if best_edge is None:
            print("No possible edge to connect components.")
            break

        i, j = best_edge

        # Add edge with zero flow
        proposal[i][j] = 0

        print(f"Added edge: S{i+1}, C{j+1} (cost = {costs[i][j]})")

    return proposal


# --------------------------------------------------
# TEST CONNECTIVITY
# --------------------------------------------------

def test_connectivity(proposal):
    # Check if the graph is connected and display connected subgraphs.
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
                if node.startswith("S"):
                    readable.append(f"S{int(node[1])+1}")
                else:
                    readable.append(f"C{int(node[1])+1}")

            print(readable)