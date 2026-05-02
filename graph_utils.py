def build_graph(proposal, basis=None):
    """
    Build a bipartite graph from the transportation proposal.
    """
    if basis is not None:
        n = len(basis["row_to_cols"])
        m = len(basis["col_to_rows"])

        graph = {f"S{i}": [] for i in range(n)}
        graph.update({f"C{j}": [] for j in range(m)})

        for i, cols in enumerate(basis["row_to_cols"]):
            for j in cols:
                s = f"S{i}"
                c = f"C{j}"
                graph[s].append(c)
                graph[c].append(s)

        return graph

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
    Find all connected components using BFS.
    """
    visited = set()
    components = []

    for start in graph:
        if start not in visited:
            queue = [start]
            head = 0
            component = []

            while head < len(queue):
                node = queue[head]
                head += 1

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


def connect_graph(problem, proposal, basis=None):
    """
    Add minimum-cost non-basic edges until the graph is connected.

    Uses integer-indexed BFS (rows 0..n-1, cols n..n+m-1) and a linear scan
    per bridge edge — O(k * n*m) instead of O(n*m * log(n*m)) for the sort.
    Typically k == 1 so the total cost is O(n*m).
    """
    costs = problem["costs"]
    n, m = problem["n"], problem["m"]
    total = n + m

    # --- BFS to label connected components with integer ids ---
    comp = [-1] * total
    num_comp = 0

    for start in range(total):
        if comp[start] != -1:
            continue
        queue = [start]
        head = 0
        comp[start] = num_comp
        while head < len(queue):
            node = queue[head]
            head += 1
            if node < n:
                nb_cols = basis["row_to_cols"][node] if basis is not None else [
                    j for j in range(m) if proposal[node][j] is not None
                ]
                for j in nb_cols:
                    nb = n + j
                    if comp[nb] == -1:
                        comp[nb] = num_comp
                        queue.append(nb)
            else:
                col = node - n
                nb_rows = basis["col_to_rows"][col] if basis is not None else [
                    i for i in range(n) if proposal[i][col] is not None
                ]
                for i in nb_rows:
                    if comp[i] == -1:
                        comp[i] = num_comp
                        queue.append(i)
        num_comp += 1

    if num_comp == 1:
        return proposal

    # --- Greedily add cheapest bridge edges until connected ---
    while num_comp > 1:
        best_cost = None
        best_i = best_j = -1

        for i in range(n):
            ci = comp[i]
            basic_cols = basis["row_to_cols"][i] if basis is not None else set()
            for j in range(m):
                if j in basic_cols:
                    continue
                if basis is None and proposal[i][j] is not None:
                    continue
                if comp[n + j] == ci:
                    continue
                c = int(costs[i][j])
                if best_cost is None or c < best_cost:
                    best_cost = c
                    best_i, best_j = i, j

        if best_i == -1:
            break

        proposal[best_i][best_j] = 0
        if basis is not None and best_j not in basis["row_to_cols"][best_i]:
            basis["row_to_cols"][best_i].add(best_j)
            basis["col_to_rows"][best_j].add(best_i)
            basis["basic_count"] += 1

        # Merge: relabel old component → new component throughout comp[]
        old_id = comp[n + best_j]
        new_id = comp[best_i]
        for k in range(total):
            if comp[k] == old_id:
                comp[k] = new_id
        num_comp -= 1

    return proposal


def test_connectivity(proposal, verbose=True, basis=None):
    graph = build_graph(proposal, basis=basis)
    components = find_connected_components(graph)

    if verbose:
        print("\n=== CONNECTIVITY TEST ===")

    if len(components) == 1:
        if verbose:
            print("Graph is already connected.")
    else:
        if verbose:
            print("Graph is NOT connected.")
            print("\nConnected sub-graphs:")

        for i, comp in enumerate(components):
            if verbose:
                print(f"Subgraph {i+1}: ", end="")

            readable = [_display_node(node) for node in comp]

            if verbose:
                print(readable)

    return components
