# ----------------
# GRAPH
# ----------------

# build a graph associated with a transport problem
def build_graph(proposal, basis=None):
    if basis is not None:
        n = len(basis["row_to_cols"])
        m = len(basis["col_to_rows"])

        graph = {f"S{i}": [] for i in range(n)}
        graph.update({f"C{j}": [] for j in range(m)})

        for i, cols in enumerate(basis["row_to_cols"]):
            for j in cols:
                s = f"S{i}" # s = supplier vertex
                c = f"C{j}" # c = customer vertex
                graph[s].append(c)
                graph[c].append(s)

        return graph

    # if no basis, read the full matrix
    n = len(proposal)
    m = len(proposal[0])

    graph = {}

    #  creation all supplier vertices
    for i in range(n):
        graph[f"S{i}"] = []

    # creation all customer vertices
    for j in range(m):
        graph[f"C{j}"] = []

    # when value is not None => add connections
    for i in range(n):
        for j in range(m):
            if proposal[i][j] is not None:
                s = f"S{i}"
                c = f"C{j}"
                # The edge is added in both directions => the graph is undirected
                graph[s].append(c)
                graph[c].append(s)

    return graph


def display_graph(proposal):
    print("\nTRANSPORT GRAPH:")

    n = len(proposal) # nb rows
    m = len(proposal[0]) # nb columns

    edges = []

    for i in range(n):
        for j in range(m):
            if proposal[i][j] is not None:
                # display the transported value in ()
                edges.append(f"S{i+1} -- C{j+1} ({proposal[i][j]})")

    if not edges:
        print("No edges")
        return

    for e in edges:
        print(e)

# ----------------
# OPERATIONS ON GRAPH
# ----------------

# allow to find all groups of connected nodes in a graph with BFS
def find_connected_components(graph):
    visited = set()
    components = []

    for start in graph:
        if start not in visited:
            # start a BFS from every vertex noseen
            queue = [start]
            head = 0
            component = []

            while head < len(queue):
                node = queue[head]
                head += 1

                if node not in visited:
                    visited.add(node)
                    component.append(node)

                    # add all neighbors not yet visited.
                    for neighbor in graph[node]:
                        if neighbor not in visited:
                            queue.append(neighbor)

            components.append(component)

    return components


def _display_node(node):
    # vertices are stored as "S0", "C1"...
    return f"{node[0]}{int(node[1:]) + 1}" # +1 because it starts from 1 and not 0

# connect graph with the cheapest link, loop until it is fully connected
def connect_graph(problem, proposal, basis=None):
    costs = problem["costs"]
    n, m = problem["n"], problem["m"]
    total = n + m # total nb of nodes
    comp = [-1] * total
    num_comp = 0

    # find all components using BFS
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
                # Supplier vertex: neighbors = basic columns of the row
                nb_cols = basis["row_to_cols"][node] if basis is not None else [
                    j for j in range(m) if proposal[node][j] is not None
                ]
                for j in nb_cols:
                    nb = n + j # convert column to node index
                    if comp[nb] == -1:
                        comp[nb] = num_comp
                        queue.append(nb)
            else:
                # Customer vertex: neighbors = basic rows of the column
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

    # connect components 1 by 1
    while num_comp > 1:
        best_cost = None
        best_i = best_j = -1

        # search for the cheapest non-basic cell connecting two diff components
        for i in range(n):
            ci = comp[i]
            basic_cols = basis["row_to_cols"][i] if basis is not None else set()
            for j in range(m):
                # skip if already basic
                if j in basic_cols:
                    continue
                if basis is None and proposal[i][j] is not None:
                    continue

                # skip if already in same component
                if comp[n + j] == ci:
                    continue

                c = int(costs[i][j])
                if best_cost is None or c < best_cost:
                    best_cost = c
                    best_i, best_j = i, j

        if best_i == -1:
            break

        # add the link with value 0 (just to connect the graph)
        proposal[best_i][best_j] = 0

        # update basis
        if basis is not None and best_j not in basis["row_to_cols"][best_i]:
            basis["row_to_cols"][best_i].add(best_j)
            basis["col_to_rows"][best_j].add(best_i)
            basis["basic_count"] += 1

        # merge two components
        old_id = comp[n + best_j]
        new_id = comp[best_i]
        for k in range(total):
            if comp[k] == old_id:
                comp[k] = new_id

        num_comp -= 1

    return proposal


def test_connectivity(proposal, verbose=True, basis=None):
    # build the graph from the table
    graph = build_graph(proposal, basis=basis)
    # find all connected groups
    components = find_connected_components(graph)

    if verbose:
        print("\n=== CONNECTIVITY TEST ===")

    # if there is only one group => graph is connected
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

            # Convert nodes for display
            readable = [_display_node(node) for node in comp]

            if verbose:
                print(readable)

    return components
