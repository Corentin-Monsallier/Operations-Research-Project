import os

from read_problem import *
from graph_utils import *

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional optimization
    np = None


# ------------------------------
# INTERNAL BASIS HELPERS
# ------------------------------

def _create_basis_state(proposal):
    n = len(proposal)
    m = len(proposal[0])
    row_to_cols = [set() for _ in range(n)]
    col_to_rows = [set() for _ in range(m)]
    basic_count = 0

    for i in range(n):
        for j in range(m):
            if proposal[i][j] is not None:
                row_to_cols[i].add(j)
                col_to_rows[j].add(i)
                basic_count += 1

    return {
        "row_to_cols": row_to_cols,
        "col_to_rows": col_to_rows,
        "basic_count": basic_count,
        "tree_ready": basic_count == (n + m - 1),
    }


def _add_basic_cell(basis, i, j):
    if j not in basis["row_to_cols"][i]:
        basis["row_to_cols"][i].add(j)
        basis["col_to_rows"][j].add(i)
        basis["basic_count"] += 1


def _remove_basic_cell(basis, i, j):
    if j in basis["row_to_cols"][i]:
        basis["row_to_cols"][i].remove(j)
        basis["col_to_rows"][j].remove(i)
        basis["basic_count"] -= 1


def _edge_to_cell_from_nodes(node_a, node_b, n):
    if node_a < n:
        return (node_a, node_b - n)
    return (node_b, node_a - n)


def _node_path_to_cells_from_nodes(node_path, n):
    return [
        _edge_to_cell_from_nodes(node_path[k], node_path[k + 1], n)
        for k in range(len(node_path) - 1)
    ]


def _build_cycle_path_from_parents(parents, node_a, node_b):
    ancestors_a = {}
    path_a = []
    current = node_a

    while current != -1:
        ancestors_a[current] = len(path_a)
        path_a.append(current)
        current = parents[current]

    path_b = []
    current = node_b

    while current not in ancestors_a:
        path_b.append(current)
        current = parents[current]

    lca = current
    path_a_to_lca = path_a[:ancestors_a[lca] + 1]
    path_lca_to_b = list(reversed(path_b))

    return path_a_to_lca + path_lca_to_b + [node_a]


def _find_tree_path_from_parent(start, goal, parents, depths):
    path_start = []
    path_goal = []
    node_a = start
    node_b = goal

    while depths[node_a] > depths[node_b]:
        path_start.append(node_a)
        node_a = parents[node_a]

    while depths[node_b] > depths[node_a]:
        path_goal.append(node_b)
        node_b = parents[node_b]

    while node_a != node_b:
        path_start.append(node_a)
        path_goal.append(node_b)
        node_a = parents[node_a]
        node_b = parents[node_b]

    path_start.append(node_a)
    path_goal.reverse()
    return path_start + path_goal


def _find_node_path_from_basis(basis, start, goal):
    n = len(basis["row_to_cols"])
    m = len(basis["col_to_rows"])
    row_to_cols = basis["row_to_cols"]
    col_to_rows = basis["col_to_rows"]
    total_nodes = n + m
    parents = [-2] * total_nodes
    queue = [start]
    head = 0
    parents[start] = -1

    while head < len(queue):
        node = queue[head]
        head += 1

        if node == goal:
            break

        if node < n:
            for col in row_to_cols[node]:
                neighbor = n + col
                if parents[neighbor] == -2:
                    parents[neighbor] = node
                    queue.append(neighbor)
        else:
            for row in col_to_rows[node - n]:
                if parents[row] == -2:
                    parents[row] = node
                    queue.append(row)

    if parents[goal] == -2:
        return None

    path = []
    node = goal

    while node != -1:
        path.append(node)
        node = parents[node]

    path.reverse()
    return path


def _find_cycle_node_path_from_basis(basis):
    n = len(basis["row_to_cols"])
    m = len(basis["col_to_rows"])
    row_to_cols = basis["row_to_cols"]
    col_to_rows = basis["col_to_rows"]
    total_nodes = n + m
    visited = [False] * total_nodes
    parents = [-2] * total_nodes

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
                for col in row_to_cols[node]:
                    neighbor = n + col
                    if neighbor == parents[node]:
                        continue

                    if visited[neighbor]:
                        return _build_cycle_path_from_parents(parents, node, neighbor)

                    visited[neighbor] = True
                    parents[neighbor] = node
                    queue.append(neighbor)
            else:
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

        queue = [start_node]
        head = 0
        visited[start_node] = True
        component = []

        while head < len(queue):
            node = queue[head]
            head += 1
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
    if np is None:
        return None

    costs_np = problem.get("_np_costs")
    if costs_np is None:
        raw = problem["costs"]
        if isinstance(raw, np.ndarray):
            costs_np = raw              # keep original dtype (int16 from generator)
        else:
            costs_np = np.asarray(raw, dtype=np.int32)
        problem["_np_costs"] = costs_np

    return costs_np


# ------------------------------
# POTENTIALS
# ------------------------------

def compute_potentials(problem, proposal, basis=None):
    if basis is None:
        basis = _create_basis_state(proposal)

    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    if np is not None:
        costs_np = _get_numpy_costs(problem)
        u = np.empty(n, dtype=np.int32)
        v = np.empty(m, dtype=np.int32)
        seen_u = bytearray(n)
        seen_v = bytearray(m)
        row_to_cols = basis["row_to_cols"]
        col_to_rows = basis["col_to_rows"]
        total_nodes = n + m
        tree_parent = [-2] * total_nodes
        tree_depth = [0] * total_nodes

        u[0] = 0
        seen_u[0] = 1
        tree_parent[0] = -1
        queue = [0]
        head = 0

        while head < len(queue):
            node = queue[head]
            head += 1

            if node >= 0:
                u_node = int(u[node])
                for j in row_to_cols[node]:
                    if not seen_v[j]:
                        v[j] = int(costs_np[node][j]) - u_node
                        seen_v[j] = 1
                        tree_parent[n + j] = node
                        tree_depth[n + j] = tree_depth[node] + 1
                        queue.append(-(j + 1))
            else:
                j = -node - 1
                v_j = int(v[j])
                for i in col_to_rows[j]:
                    if not seen_u[i]:
                        u[i] = int(costs_np[i][j]) - v_j
                        seen_u[i] = 1
                        tree_parent[i] = n + j
                        tree_depth[i] = tree_depth[n + j] + 1
                        queue.append(i)

        basis["tree_parent"] = tree_parent
        basis["tree_depth"] = tree_depth
        return u, v

    u = [None] * n
    v = [None] * m
    row_to_cols = basis["row_to_cols"]
    col_to_rows = basis["col_to_rows"]
    total_nodes = n + m
    tree_parent = [-2] * total_nodes
    tree_depth = [0] * total_nodes

    u[0] = 0
    tree_parent[0] = -1
    queue = [("u", 0)]
    head = 0

    while head < len(queue):
        node_type, idx = queue[head]
        head += 1
        if node_type == "u":
            for j in row_to_cols[idx]:
                if v[j] is None:
                    v[j] = costs[idx][j] - u[idx]
                    tree_parent[n + j] = idx
                    tree_depth[n + j] = tree_depth[idx] + 1
                    queue.append(("v", j))
        else:
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
    n, m = problem["n"], problem["m"]

    table = [[u[i] + v[j] for j in range(m)] for i in range(n)]

    print("\n=== POTENTIAL COSTS ===")
    for i in range(n):
        print(table[i])

    return table


def marginal_costs(problem, u, v):
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    table = [[costs[i][j] - u[i] - v[j] for j in range(m)] for i in range(n)]

    print("\n=== MARGINAL COSTS ===")
    for i in range(n):
        print(table[i])

    return table


def is_degenerate(problem, proposal, basis=None):
    n, m = problem["n"], problem["m"]

    if basis is not None:
        count = basis["basic_count"]
    else:
        count = sum(
            1 for i in range(n) for j in range(m)
            if proposal[i][j] is not None
        )

    return count < (n + m - 1)


def find_improving_cell(problem, u, v, proposal, basis=None):
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
                buf = np.empty((n, m), dtype=np.int32)
                problem["_marginals_buf"] = buf

            # int32 safe: |u[i]|,|v[j]| <= 100*(n+m) << 2^31 for n<=5000
            u32 = u if isinstance(u, np.ndarray) and u.dtype == np.int32 else np.asarray(u, dtype=np.int32)
            v32 = v if isinstance(v, np.ndarray) and v.dtype == np.int32 else np.asarray(v, dtype=np.int32)
            np.copyto(buf, costs_np, casting="unsafe")  # costs -> int32, no temp
            buf -= u32[:, np.newaxis]
            buf -= v32[np.newaxis, :]

            idx = int(buf.argmin())
            min_val = int(buf.flat[idx])
            if min_val >= 0:
                return None, 0
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
            np.copyto(buf, costs_np[start:stop], casting="unsafe")
            buf -= u32[start:stop, np.newaxis]
            buf -= v32[np.newaxis, :]

            idx = int(buf.argmin())
            delta = int(buf.flat[idx])
            if delta < best_value:
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
    cells = cycle[:-1]
    rotated = cells[start_idx:] + cells[:start_idx]
    return rotated + [rotated[0]]


def _prefer_zero_on_minus(proposal, cycle):
    """
    When we correct an already-basic cycle, we prefer an orientation that puts
    a zero-valued edge on a '-' position so the cycle can be broken without
    changing the transported quantities.
    """
    cells = cycle[:-1]

    for start_idx in range(len(cells)):
        rotated = _rotate_cycle(cycle, start_idx)
        minus_cells = [rotated[k] for k in range(1, len(rotated) - 1, 2)]
        if any(proposal[i][j] == 0 for i, j in minus_cells):
            return rotated

    return cycle


def detect_cycle(proposal, verbose=True, basis=None):
    if basis is None:
        basis = _create_basis_state(proposal)

    node_cycle = _find_cycle_node_path_from_basis(basis)

    if node_cycle is None:
        return None

    n = len(basis["row_to_cols"])
    cycle_cells = _node_path_to_cells_from_nodes(node_cycle, n)
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

    minus_cells = []
    signs = []

    for k, (i, j) in enumerate(cycle[:-1]):
        sign = "+" if k % 2 == 0 else "-"
        signs.append((i, j, sign))
        if sign == "-":
            minus_cells.append((i, j))

    if verbose:
        for i, j, sign in signs:
            print(f"P{i+1}, C{j+1}: {sign}{proposal[i][j]}")

    theta = min(proposal[i][j] for i, j in minus_cells)

    if verbose:
        print(f"\nTheta (maximum transport): {theta}")
        print("\nDeleted edge(s):")

    deleted_found = False

    for i, j in minus_cells:
        if proposal[i][j] == theta:
            if verbose:
                print(f"P{i+1}, C{j+1}")
            deleted_found = True

    if not deleted_found and verbose:
        print("None")


def find_cycle(proposal, start, verbose=True, basis=None):
    if basis is None:
        basis = _create_basis_state(proposal)

    n = len(basis["row_to_cols"])
    start_row = start[0]
    start_col = n + start[1]
    parents = basis.get("tree_parent")
    depths = basis.get("tree_depth")

    if parents is not None and depths is not None and parents[start_row] != -2 and parents[start_col] != -2:
        node_path = _find_tree_path_from_parent(start_row, start_col, parents, depths)
    else:
        node_path = _find_node_path_from_basis(basis, start_row, start_col)

    if node_path is not None:
        cycle = [start] + _node_path_to_cells_from_nodes(node_path, n) + [start]

        if verbose:
            print("\nCycle found:")
            print(cycle)

        return cycle

    if verbose:
        print("\nNo valid cycle found.")
    return None


def update_proposal(proposal, cycle, verbose=True, basis=None):
    minus_cells = []

    for k, (i, j) in enumerate(cycle[:-1]):
        if k % 2 == 1:
            minus_cells.append((i, j))

    theta = min(proposal[i][j] for (i, j) in minus_cells)

    if verbose:
        print("\n=== APPLYING UPDATE ===")
        print(f"Theta = {theta}\n")
        print("Before update:")

    for k, (i, j) in enumerate(cycle[:-1]):
        if k % 2 == 0:
            if proposal[i][j] is None:
                proposal[i][j] = 0
                if basis is not None:
                    _add_basic_cell(basis, i, j)
            proposal[i][j] += theta
        else:
            proposal[i][j] -= theta

    if verbose:
        print("\nAfter update:")
        print("\nRemoved edges:")

    removed = False
    removed_count = 0

    for i, j in minus_cells:
        if proposal[i][j] == 0:
            proposal[i][j] = None
            if basis is not None:
                _remove_basic_cell(basis, i, j)
            removed = True
            removed_count += 1

    if not removed and verbose:
        print("None")

    if basis is not None:
        expected_basic_count = len(basis["row_to_cols"]) + len(basis["col_to_rows"]) - 1
        basis["tree_ready"] = (
            removed_count == 1 and basis["basic_count"] == expected_basic_count
        )


def _normalize_transport_graph(problem, proposal, verbose=True, basis=None):
    if basis is None:
        basis = _create_basis_state(proposal)

    expected_basic_count = len(basis["row_to_cols"]) + len(basis["col_to_rows"]) - 1

    if basis["tree_ready"] and basis["basic_count"] == expected_basic_count:
        return proposal

    while True:
        cycle = detect_cycle(proposal, verbose=verbose, basis=basis)
        if cycle:
            if verbose:
                print("Graph contains a cycle.")
                transportation_maximization(proposal, cycle, verbose=True)
            update_proposal(proposal, cycle, verbose=verbose, basis=basis)
            continue

        n = len(basis["row_to_cols"])
        components = _find_connected_components_from_basis(basis)
        _display_basis_components(components, n, verbose)

        if len(components) == 1:
            basis["tree_ready"] = basis["basic_count"] == expected_basic_count
            return proposal

        proposal = connect_graph(problem, proposal, basis=basis)


def solve_stepping_stone(problem, proposal, verbose=True):
    iteration = 0
    basis = _create_basis_state(proposal)

    while True:
        iteration += 1

        if verbose:
            print("\n-----------")
            print(f" ITERATION {iteration}")
            print("-----------")
            display_transport_proposal(problem, proposal)
            display_graph(proposal)
            print(f"Current cost: {total_cost(problem, proposal)}")

            if is_degenerate(problem, proposal, basis=basis):
                print("The proposal is degenerate")

        proposal = _normalize_transport_graph(problem, proposal, verbose=verbose, basis=basis)

        u, v = compute_potentials(problem, proposal, basis=basis)

        if verbose:
            print("\nPotentials:")
            print("u =", u)
            print("v =", v)
            display_potential_costs(problem, u, v)
            display_marginal_costs(problem, u, v)
            print("\n--- Checking optimality ---")

        cell, value = find_improving_cell(problem, u, v, proposal, basis=basis)

        if cell is None:
            if verbose:
                print("=> IT IS THE OPTIMAL SOLUTION")
            return proposal

        if verbose:
            print(f"Improving edge: S{cell[0]+1}, C{cell[1]+1} (delta = {value})")

        cycle = find_cycle(proposal, cell, verbose=verbose, basis=basis)

        if not cycle:
            if verbose:
                print("No cycle found => STOP")
            return proposal

        if verbose:
            transportation_maximization(proposal, cycle, verbose=True)
        update_proposal(proposal, cycle, verbose=verbose, basis=basis)
