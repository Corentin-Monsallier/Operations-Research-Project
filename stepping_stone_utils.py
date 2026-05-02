import os

# read_problem mainly provides here the display functions and the calculation
# of the total cost, which allows the stepping-stone to explain what it does
# at each iteration.
from read_problem import *

# graph_utils groups the more "general" graph logic:
# graph display, reconnection by edges at 0, etc.
from graph_utils import *

# We force here the numerical libraries to use only one thread.
# This makes the calculation times more stable and matches the subject better.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np


# ------------------------------
# INTERNAL BASIS HELPERS
# ------------------------------

def _create_basis_state(proposal):
    # Number of rows of the transport table.
    n = len(proposal)

    # Number of columns of the transport table.
    m = len(proposal[0])

    # row_to_cols[i] will contain all columns j such that the cell
    # (i, j) belongs to the current basis.
    row_to_cols = [set() for _ in range(n)]

    # col_to_rows[j] does exactly the opposite:
    # for one column j, we keep the list of connected rows.
    col_to_rows = [set() for _ in range(m)]

    # Total count of basic cells.
    basic_count = 0

    # We go through each cell of the proposal table.
    for i in range(n):
        for j in range(m):
            # A cell is basic if it is not None.
            if proposal[i][j] is not None:
                # We connect row i to column j.
                row_to_cols[i].add(j)
                col_to_rows[j].add(i)

                # We count this edge one more time in the basis.
                basic_count += 1

    # We return the whole useful structure to the stepping-stone.
    return {
        "row_to_cols": row_to_cols,
        "col_to_rows": col_to_rows,
        "basic_count": basic_count,
        # A basis "ready for tree" must have n + m - 1 edges.
        "tree_ready": basic_count == (n + m - 1),
    }


def _add_basic_cell(basis, i, j):
    # We add the cell only if it is not already in the basis,
    # to avoid counting the same edge twice.
    if j not in basis["row_to_cols"][i]:
        basis["row_to_cols"][i].add(j)
        basis["col_to_rows"][j].add(i)
        basis["basic_count"] += 1


def _remove_basic_cell(basis, i, j):
    # Same idea in deletion:
    # we remove the cell only if it was really present.
    if j in basis["row_to_cols"][i]:
        basis["row_to_cols"][i].remove(j)
        basis["col_to_rows"][j].remove(i)
        basis["basic_count"] -= 1


def _edge_to_cell_from_nodes(node_a, node_b, n):
    # Internal convention of the graph:
    # - 0 .. n-1 represent the rows/suppliers
    # - n .. n+m-1 represent the columns/customers
    #
    # This function therefore translates one edge of the graph into matrix
    # coordinates (row, column).
    if node_a < n:
        # If node_a is one row, node_b is necessarily one column.
        return (node_a, node_b - n)

    # Otherwise node_b is the row and node_a the column.
    return (node_b, node_a - n)


def _node_path_to_cells_from_nodes(node_path, n):
    # If node_path = [vertex0, vertex1, vertex2, ...],
    # then each consecutive pair defines one cell of the table.
    return [
        _edge_to_cell_from_nodes(node_path[k], node_path[k + 1], n)
        for k in range(len(node_path) - 1)
    ]


def _build_cycle_path_from_parents(parents, node_a, node_b):
    # This function reconstructs one cycle from the "parents" table
    # of the BFS, once a back edge has been detected.

    # Dictionary vertex -> position in the path climbed from node_a.
    ancestors_a = {}

    # List of the ancestors of node_a, from bottom to top.
    path_a = []
    current = node_a

    # We climb all parents of node_a up to the root.
    while current != -1:
        ancestors_a[current] = len(path_a)
        path_a.append(current)
        current = parents[current]

    # Same idea from node_b, but here we stop as soon as we reach
    # one ancestor already present in the chain of node_a.
    path_b = []
    current = node_b

    while current not in ancestors_a:
        path_b.append(current)
        current = parents[current]

    # "current" is now the lowest common ancestor.
    lca = current

    # Portion of the path node_a -> ... -> LCA.
    path_a_to_lca = path_a[:ancestors_a[lca] + 1]

    # Portion LCA -> ... -> node_b.
    path_lca_to_b = list(reversed(path_b))

    # We finally close the cycle by coming back to node_a.
    return path_a_to_lca + path_lca_to_b + [node_a]


def _find_tree_path_from_parent(start, goal, parents, depths):
    # In one tree, the path between two vertices is unique.
    # We obtain it by making the two vertices climb to the same level,
    # then up to their common ancestor.
    path_start = []
    path_goal = []
    node_a = start
    node_b = goal

    # We make the deepest vertex climb up to the level of the other.
    while depths[node_a] > depths[node_b]:
        path_start.append(node_a)
        node_a = parents[node_a]

    while depths[node_b] > depths[node_a]:
        path_goal.append(node_b)
        node_b = parents[node_b]

    # Once the depths are equal, we make both climb in parallel.
    while node_a != node_b:
        path_start.append(node_a)
        path_goal.append(node_b)
        node_a = parents[node_a]
        node_b = parents[node_b]

    # The first equality point is the lowest common ancestor.
    path_start.append(node_a)

    # The path climbs up from goal, so we reverse it.
    path_goal.reverse()
    return path_start + path_goal


def _find_node_path_from_basis(basis, start, goal):
    # This version is more general than _find_tree_path_from_parent:
    # it does a complete BFS in the current basis to connect "start" to "goal".
    n = len(basis["row_to_cols"])
    m = len(basis["col_to_rows"])
    row_to_cols = basis["row_to_cols"]
    col_to_rows = basis["col_to_rows"]
    total_nodes = n + m

    # parents[x] = parent of x in the BFS.
    # -2 means "never visited".
    parents = [-2] * total_nodes

    # Initialization of the queue with the start vertex.
    queue = [start]
    head = 0

    # The root of the BFS has no parent.
    parents[start] = -1

    while head < len(queue):
        node = queue[head]
        head += 1

        # If we reach the target, there is no need to continue.
        if node == goal:
            break

        if node < n:
            # Case "row vertex":
            # its neighbors are all the basic columns of this row.
            for col in row_to_cols[node]:
                neighbor = n + col
                if parents[neighbor] == -2:
                    parents[neighbor] = node
                    queue.append(neighbor)
        else:
            # Case "column vertex":
            # its neighbors are all the basic rows of this column.
            for row in col_to_rows[node - n]:
                if parents[row] == -2:
                    parents[row] = node
                    queue.append(row)

    # If goal was never visited, no path exists.
    if parents[goal] == -2:
        return None

    path = []
    node = goal

    # Reconstruction of the path by climbing the parents from goal.
    while node != -1:
        path.append(node)
        node = parents[node]

    # The path was reconstructed backward.
    path.reverse()
    return path


def _find_cycle_node_path_from_basis(basis):
    # This function looks for one cycle already present in the current basis.
    # It is mainly useful when the basis has too many edges and is therefore not yet a tree.
    n = len(basis["row_to_cols"])
    m = len(basis["col_to_rows"])
    row_to_cols = basis["row_to_cols"]
    col_to_rows = basis["col_to_rows"]
    total_nodes = n + m
    visited = [False] * total_nodes
    parents = [-2] * total_nodes

    # The graph may be split into several components.
    # So we start a BFS from each vertex not yet visited.
    for start_node in range(total_nodes):
        if visited[start_node]:
            continue

        queue = [start_node]
        head = 0
        visited[start_node] = True
        parents[start_node] = -1

        while head < len(queue):
            node = queue[head]
            head += 1

            if node < n:
                # For one row, the neighbors are columns.
                for col in row_to_cols[node]:
                    neighbor = n + col

                    # Returning to the parent is normal in an undirected graph.
                    if neighbor == parents[node]:
                        continue

                    # If the neighbor is already visited without being the parent,
                    # then we have detected a cycle.
                    if visited[neighbor]:
                        return _build_cycle_path_from_parents(parents, node, neighbor)

                    visited[neighbor] = True
                    parents[neighbor] = node
                    queue.append(neighbor)
            else:
                # For one column, the neighbors are rows.
                for row in col_to_rows[node - n]:
                    if row == parents[node]:
                        continue

                    if visited[row]:
                        return _build_cycle_path_from_parents(parents, node, row)

                    visited[row] = True
                    parents[row] = node
                    queue.append(row)

    return None


def _find_connected_components_from_basis(basis):
    # This function splits the basis into connected components.
    # Each component corresponds to one independent subgraph.
    n = len(basis["row_to_cols"])
    m = len(basis["col_to_rows"])
    row_to_cols = basis["row_to_cols"]
    col_to_rows = basis["col_to_rows"]
    total_nodes = n + m
    visited = [False] * total_nodes
    components = []

    for start_node in range(total_nodes):
        if visited[start_node]:
            continue

        # New BFS to build a new component.
        queue = [start_node]
        head = 0
        visited[start_node] = True
        component = []

        while head < len(queue):
            node = queue[head]
            head += 1

            # We store the vertex in the current component.
            component.append(node)

            if node < n:
                for col in row_to_cols[node]:
                    neighbor = n + col
                    if not visited[neighbor]:
                        visited[neighbor] = True
                        queue.append(neighbor)
            else:
                for row in col_to_rows[node - n]:
                    if not visited[row]:
                        visited[row] = True
                        queue.append(row)

        components.append(component)

    return components


def _display_basis_components(components, n, verbose):
    # If no display is requested, we exit immediately.
    if not verbose:
        return

    print("\n=== CONNECTIVITY TEST ===")

    if len(components) == 1:
        print("Graph is already connected.")
        return

    print("Graph is NOT connected.")
    print("\nConnected sub-graphs:")

    for idx, component in enumerate(components):
        labels = []
        for node in component:
            if node < n:
                labels.append(f"S{node + 1}")
            else:
                labels.append(f"C{node - n + 1}")
        print(f"Subgraph {idx + 1}: {labels}")


def _get_numpy_costs(problem):
    # Without numpy, no conversion is possible.
    if np is None:
        return None

    # We first look for whether the matrix has already been converted.
    costs_np = problem.get("_np_costs")
    if costs_np is None:
        raw = problem["costs"]
        if isinstance(raw, np.ndarray):
            # If it is already one ndarray, we reuse it as is.
            costs_np = raw
        else:
            # Otherwise we convert to int32 only once.
            costs_np = np.asarray(raw, dtype=np.int32)

        # We cache the conversion for the next calls.
        problem["_np_costs"] = costs_np

    return costs_np


# ------------------------------
# POTENTIALS
# ------------------------------

def compute_potentials(problem, proposal, basis=None):
    # If the caller did not provide an already calculated basis,
    # we rebuild it from the proposal.
    if basis is None:
        basis = _create_basis_state(proposal)

    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    if np is not None:
        # Optimized version with numpy.
        costs_np = _get_numpy_costs(problem)
        u = np.empty(n, dtype=np.int32)
        v = np.empty(m, dtype=np.int32)

        # seen_u / seen_v say whether one potential has already been determined.
        seen_u = bytearray(n)
        seen_v = bytearray(m)
        row_to_cols = basis["row_to_cols"]
        col_to_rows = basis["col_to_rows"]
        total_nodes = n + m

        # These two arrays store the traversal tree of the BFS.
        # They will then be reused to quickly reconstruct
        # one cycle when adding one improving cell.
        tree_parent = [-2] * total_nodes
        tree_depth = [0] * total_nodes

        # Because the potentials are defined up to one constant,
        # we arbitrarily set u[0] = 0.
        u[0] = 0
        seen_u[0] = 1
        tree_parent[0] = -1
        queue = [0]
        head = 0

        while head < len(queue):
            node = queue[head]
            head += 1

            if node >= 0:
                # Local convention:
                # node >= 0  -> we are talking about one row
                # node < 0   -> we are talking about one column coded as -(j + 1)
                u_node = int(u[node])
                for j in row_to_cols[node]:
                    if not seen_v[j]:
                        # On one basic edge:
                        # u[i] + v[j] = c[i][j]
                        # therefore v[j] = c[i][j] - u[i]
                        v[j] = int(costs_np[node][j]) - u_node
                        seen_v[j] = 1
                        tree_parent[n + j] = node
                        tree_depth[n + j] = tree_depth[node] + 1
                        queue.append(-(j + 1))
            else:
                # We decode the column.
                j = -node - 1
                v_j = int(v[j])
                for i in col_to_rows[j]:
                    if not seen_u[i]:
                        # Same equation, written this time to recover u[i].
                        u[i] = int(costs_np[i][j]) - v_j
                        seen_u[i] = 1
                        tree_parent[i] = n + j
                        tree_depth[i] = tree_depth[n + j] + 1
                        queue.append(i)

        # We store the calculation tree in "basis" for the next steps.
        basis["tree_parent"] = tree_parent
        basis["tree_depth"] = tree_depth
        return u, v

    # Pure Python version, same logic but without numpy.
    u = [None] * n
    v = [None] * m
    row_to_cols = basis["row_to_cols"]
    col_to_rows = basis["col_to_rows"]
    total_nodes = n + m
    tree_parent = [-2] * total_nodes
    tree_depth = [0] * total_nodes

    # Once again, we arbitrarily set the first potential.
    u[0] = 0
    tree_parent[0] = -1
    queue = [("u", 0)]
    head = 0

    while head < len(queue):
        node_type, idx = queue[head]
        head += 1
        if node_type == "u":
            # From one row, we deduce the column potentials.
            for j in row_to_cols[idx]:
                if v[j] is None:
                    v[j] = costs[idx][j] - u[idx]
                    tree_parent[n + j] = idx
                    tree_depth[n + j] = tree_depth[idx] + 1
                    queue.append(("v", j))
        else:
            # From one column, we deduce the row potentials.
            for i in col_to_rows[idx]:
                if u[i] is None:
                    u[i] = costs[i][idx] - v[idx]
                    tree_parent[i] = n + idx
                    tree_depth[i] = tree_depth[n + idx] + 1
                    queue.append(("u", i))

    basis["tree_parent"] = tree_parent
    basis["tree_depth"] = tree_depth
    return u, v


def potential_costs(problem, u, v):
    # This function does only one thing:
    # explicitly build the table u[i] + v[j] for display.
    n, m = problem["n"], problem["m"]

    table = [[u[i] + v[j] for j in range(m)] for i in range(n)]

    print("\n=== POTENTIAL COSTS ===")
    for i in range(n):
        print(table[i])

    return table


def marginal_costs(problem, u, v):
    # Here we build the delta table:
    # real cost - row potential - column potential.
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    table = [[costs[i][j] - u[i] - v[j] for j in range(m)] for i in range(n)]

    print("\n=== MARGINAL COSTS ===")
    for i in range(n):
        print(table[i])

    return table


def is_degenerate(problem, proposal, basis=None):
    # One non-degenerate basis must contain n + m - 1 basic cells.
    n, m = problem["n"], problem["m"]

    if basis is not None:
        # If the basis is already maintained, we directly read the counter.
        count = basis["basic_count"]
    else:
        # Otherwise we recount all non-empty cells.
        count = sum(
            1 for i in range(n) for j in range(m)
            if proposal[i][j] is not None
        )

    return count < (n + m - 1)


def find_improving_cell(problem, u, v, proposal, basis=None):
    # This function looks for the cell whose marginal cost is the smallest.
    # If this best delta is negative, then adding this cell
    # allows decreasing the total cost.
    if basis is None:
        basis = _create_basis_state(proposal)

    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    if np is not None:
        costs_np = _get_numpy_costs(problem)

        if n * m <= 25_000_000:
            # Full-matrix vectorized approach.
            # Insight: potentials guarantee u[i]+v[j] == c[i][j] for all basic
            # cells, so their marginal is exactly 0. No masking needed: if
            # min < 0, argmin is necessarily a non-basic cell.
            buf = problem.get("_marginals_buf")
            if buf is None or buf.shape != (n, m):
                # "buf" is one reusable work array.
                # We create it only if needed to avoid repetitive
                # allocations at each iteration.
                buf = np.empty((n, m), dtype=np.int32)
                problem["_marginals_buf"] = buf

            # int32 safe: |u[i]|,|v[j]| <= 100*(n+m) << 2^31 for n<=5000
            u32 = u if isinstance(u, np.ndarray) and u.dtype == np.int32 else np.asarray(u, dtype=np.int32)
            v32 = v if isinstance(v, np.ndarray) and v.dtype == np.int32 else np.asarray(v, dtype=np.int32)

            # We first copy the costs into the buffer.
            np.copyto(buf, costs_np, casting="unsafe")  # costs -> int32, no temp

            # Then we subtract the row potentials.
            buf -= u32[:, np.newaxis]

            # Then the column potentials.
            buf -= v32[np.newaxis, :]

            # "idx" is the flat index of the smallest delta.
            idx = int(buf.argmin())
            min_val = int(buf.flat[idx])

            # If everything is >= 0, the solution is optimal.
            if min_val >= 0:
                return None, 0

            # We convert the flat index into coordinates (i, j).
            best_i, best_j = divmod(idx, m)
            return (best_i, best_j), min_val

        # Row-by-row for n*m > 25M (memory-constrained).
        # Chunked vectorized approach for very large matrices.
        # This keeps memory bounded while avoiding one argmin per row.
        u32 = u if isinstance(u, np.ndarray) and u.dtype == np.int32 else np.asarray(u, dtype=np.int32)
        v32 = v if isinstance(v, np.ndarray) and v.dtype == np.int32 else np.asarray(v, dtype=np.int32)
        chunk_rows = max(1, min(n, 4_000_000 // max(m, 1)))
        chunk_buf = problem.get("_marginals_chunk_buf")
        if chunk_buf is None or chunk_buf.shape != (chunk_rows, m):
            chunk_buf = np.empty((chunk_rows, m), dtype=np.int32)
            problem["_marginals_chunk_buf"] = chunk_buf

        best_value = 0
        best_cell = None

        for start in range(0, n, chunk_rows):
            stop = min(start + chunk_rows, n)
            rows = stop - start
            buf = chunk_buf[:rows]

            # The temporary buffer receives this block of rows.
            np.copyto(buf, costs_np[start:stop], casting="unsafe")
            buf -= u32[start:stop, np.newaxis]
            buf -= v32[np.newaxis, :]

            idx = int(buf.argmin())
            delta = int(buf.flat[idx])
            if delta < best_value:
                # We keep the best global cell found so far.
                local_i, j_min = divmod(idx, m)
                best_value = delta
                best_cell = (start + local_i, j_min)

        return best_cell, best_value

    # Pure Python fallback.
    # Basic cells have marginal = 0 by potential equations; no masking needed.
    best_value = 0
    best_cell = None
    for i in range(n):
        ui = u[i]
        for j in range(m):
            delta = costs[i][j] - ui - v[j]
            if delta < best_value:
                best_value = delta
                best_cell = (i, j)
    return best_cell, best_value


def _rotate_cycle(cycle, start_idx):
    # "cycle" is stored in closed form:
    # the last element repeats the first.
    cells = cycle[:-1]

    # We choose one new starting point.
    rotated = cells[start_idx:] + cells[:start_idx]

    # We close the cycle again.
    return rotated + [rotated[0]]


def _prefer_zero_on_minus(proposal, cycle):
    """
    When we correct an already-basic cycle, we prefer an orientation that puts
    a zero-valued edge on a '-' position so the cycle can be broken without
    changing the transported quantities.
    """
    cells = cycle[:-1]

    for start_idx in range(len(cells)):
        # We test each possible rotation of the cycle.
        rotated = _rotate_cycle(cycle, start_idx)

        # In one alternating cycle, the odd positions are '-' cells.
        minus_cells = [rotated[k] for k in range(1, len(rotated) - 1, 2)]

        # If one of these cells is already worth 0, this orientation is practical:
        # it will make it possible to break the cycle without modifying the positive flows.
        if any(proposal[i][j] == 0 for i, j in minus_cells):
            return rotated

    return cycle


def detect_cycle(proposal, verbose=True, basis=None):
    # Search for one cycle already existing in the current basis.
    if basis is None:
        basis = _create_basis_state(proposal)

    node_cycle = _find_cycle_node_path_from_basis(basis)

    if node_cycle is None:
        return None

    # We translate the vertex cycle into one cycle of matrix cells.
    n = len(basis["row_to_cols"])
    cycle_cells = _node_path_to_cells_from_nodes(node_cycle, n)

    # We explicitly close the cycle to simplify the rest of the code.
    cycle = cycle_cells + [cycle_cells[0]]
    cycle = _prefer_zero_on_minus(proposal, cycle)

    if verbose:
        print("\nCycle found:")
        print(cycle)
    return cycle


def transportation_maximization(proposal, cycle, verbose=True):
    """
    Perform the 'transportation maximization' step once a cycle is detected.

    Steps:
    1. Assign alternating signs (+ / -) to the cells of the cycle
    2. Compute theta = minimum value among '-' cells
    3. Identify and display the edge(s) that will be removed (value becomes 0)
    """

    if verbose:
        print("\n=== TRANSPORTATION MAXIMIZATION ===")
        print("\nConditions for each box:")

    # minus_cells will keep only the cells with one '-' sign.
    minus_cells = []

    # signs is used only for pedagogical display.
    signs = []

    for k, (i, j) in enumerate(cycle[:-1]):
        # The cycle always alternates:
        # + on the even positions, - on the odd positions.
        sign = "+" if k % 2 == 0 else "-"
        signs.append((i, j, sign))
        if sign == "-":
            minus_cells.append((i, j))

    if verbose:
        for i, j, sign in signs:
            print(f"P{i+1}, C{j+1}: {sign}{proposal[i][j]}")

    # Theta is constrained by the '-' cells:
    # we cannot remove more than the smallest present value.
    theta = min(proposal[i][j] for i, j in minus_cells)

    if verbose:
        print(f"\nTheta (maximum transport): {theta}")
        print("\nDeleted edge(s):")

    deleted_found = False

    for i, j in minus_cells:
        # Every '-' cell equal to theta will fall exactly to 0 after the update.
        if proposal[i][j] == theta:
            if verbose:
                print(f"P{i+1}, C{j+1}")
            deleted_found = True

    if not deleted_found and verbose:
        print("None")


def find_cycle(proposal, start, verbose=True, basis=None):
    # This function looks for the cycle created if we add the cell "start"
    # to the current basis.
    if basis is None:
        basis = _create_basis_state(proposal)

    n = len(basis["row_to_cols"])

    # "start_row" is the supplier vertex corresponding to the row of start.
    start_row = start[0]

    # "start_col" is the customer vertex corresponding to the column of start.
    # It is coded as n + j in the internal bipartite graph.
    start_col = n + start[1]

    # These informations exist if compute_potentials has already been called.
    parents = basis.get("tree_parent")
    depths = basis.get("tree_depth")

    if parents is not None and depths is not None and parents[start_row] != -2 and parents[start_col] != -2:
        # Fast case: we exploit the tree already calculated by the potentials.
        node_path = _find_tree_path_from_parent(start_row, start_col, parents, depths)
    else:
        # General case: we recover one path with one BFS in the basis.
        node_path = _find_node_path_from_basis(basis, start_row, start_col)

    if node_path is not None:
        # The cycle is made of:
        # - the new cell "start"
        # - the existing path in the tree
        # - then one final return to start
        cycle = [start] + _node_path_to_cells_from_nodes(node_path, n) + [start]

        if verbose:
            print("\nCycle found:")
            print(cycle)

        return cycle

    if verbose:
        print("\nNo valid cycle found.")
    return None


def update_proposal(proposal, cycle, verbose=True, basis=None):
    # This function really applies the transport modification
    # along one alternating cycle.
    minus_cells = []

    for k, (i, j) in enumerate(cycle[:-1]):
        # The cells in odd position carry the '-' sign.
        if k % 2 == 1:
            minus_cells.append((i, j))

    # Theta is limited by the '-' cells.
    theta = min(proposal[i][j] for (i, j) in minus_cells)

    if verbose:
        print("\n=== APPLYING UPDATE ===")
        print(f"Theta = {theta}\n")
        print("Before update:")

    for k, (i, j) in enumerate(cycle[:-1]):
        if k % 2 == 0:
            # If the '+' cell was not already in the basis, we add it there
            # first in the form of one edge of weight 0.
            if proposal[i][j] is None:
                proposal[i][j] = 0
                if basis is not None:
                    _add_basic_cell(basis, i, j)

            # Then we increase its transport by theta.
            proposal[i][j] += theta
        else:
            # On the '-' cells, we remove theta.
            proposal[i][j] -= theta

    if verbose:
        print("\nAfter update:")
        print("\nRemoved edges:")

    removed = False
    removed_count = 0

    for i, j in minus_cells:
        # One '-' cell that reaches 0 must leave the basis.
        if proposal[i][j] == 0:
            proposal[i][j] = None
            if basis is not None:
                _remove_basic_cell(basis, i, j)
            removed = True
            removed_count += 1

    if not removed and verbose:
        print("None")

    if basis is not None:
        # Number of basic cells expected to form one tree.
        expected_basic_count = len(basis["row_to_cols"]) + len(basis["col_to_rows"]) - 1

        # tree_ready becomes true only if:
        # - one unique edge disappeared on the cycle
        # - the total number of edges corresponds to one tree
        basis["tree_ready"] = (
            removed_count == 1 and basis["basic_count"] == expected_basic_count
        )


def _normalize_transport_graph(problem, proposal, verbose=True, basis=None):
    # Before calculating the potentials, the basis must be "cleaned":
    # no cycle, connected graph, and correct number of edges.
    if basis is None:
        basis = _create_basis_state(proposal)

    expected_basic_count = len(basis["row_to_cols"]) + len(basis["col_to_rows"]) - 1

    # If the state already seems correct, we touch nothing.
    if basis["tree_ready"] and basis["basic_count"] == expected_basic_count:
        return proposal

    while True:
        # 1. We first look for one existing cycle to remove.
        cycle = detect_cycle(proposal, verbose=verbose, basis=basis)
        if cycle:
            if verbose:
                print("Graph contains a cycle.")
                transportation_maximization(proposal, cycle, verbose=True)
            update_proposal(proposal, cycle, verbose=verbose, basis=basis)
            continue

        # 2. If there is no more cycle, we check connectivity.
        n = len(basis["row_to_cols"])
        components = _find_connected_components_from_basis(basis)
        _display_basis_components(components, n, verbose)

        if len(components) == 1:
            # The basis is finally connected; we store whether it has the right size.
            basis["tree_ready"] = basis["basic_count"] == expected_basic_count
            return proposal

        # 3. Otherwise we reconnect the components with edges at 0
        # of minimum cost.
        proposal = connect_graph(problem, proposal, basis=basis)


def solve_stepping_stone(problem, proposal, verbose=True):
    # Main function of the algorithm.
    # It repeats the stepping-stone steps until it can no longer find
    # any improving cell.
    iteration = 0
    basis = _create_basis_state(proposal)

    while True:
        iteration += 1

        if verbose:
            print("\n-----------")
            print(f" ITERATION {iteration}")
            print("-----------")

            # Current state of the transport plan.
            display_transport_proposal(problem, proposal)

            # Graph associated with the basic cells.
            display_graph(proposal)

            # Total cost of the current plan.
            print(f"Current cost: {total_cost(problem, proposal)}")

            if is_degenerate(problem, proposal, basis=basis):
                print("The proposal is degenerate")

        # Step 1: make the basis usable like one tree.
        proposal = _normalize_transport_graph(problem, proposal, verbose=verbose, basis=basis)

        # Step 2: calculate the potentials on this basis.
        u, v = compute_potentials(problem, proposal, basis=basis)

        if verbose:
            print("\nPotentials:")
            print("u =", u)
            print("v =", v)
            display_potential_costs(problem, u, v)
            display_marginal_costs(problem, u, v)
            print("\n--- Checking optimality ---")

        # Step 3: look for the best cell to add.
        cell, value = find_improving_cell(problem, u, v, proposal, basis=basis)

        if cell is None:
            if verbose:
                print("=> IT IS THE OPTIMAL SOLUTION")
            return proposal

        if verbose:
            print(f"Improving edge: S{cell[0]+1}, C{cell[1]+1} (delta = {value})")

        # Step 4: find the cycle created by the addition of this cell.
        cycle = find_cycle(proposal, cell, verbose=verbose, basis=basis)

        if not cycle:
            if verbose:
                print("No cycle found => STOP")
            return proposal

        # Step 5: display then apply the adjustment on the cycle.
        if verbose:
            transportation_maximization(proposal, cycle, verbose=True)
        update_proposal(proposal, cycle, verbose=verbose, basis=basis)
