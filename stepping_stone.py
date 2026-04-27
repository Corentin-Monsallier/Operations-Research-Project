from read_problem import read_problem, display_cost_matrix, display_transport_proposal, total_cost
from graph_utils import *
import os
from collections import deque


#------------------------------
# POTENTIALS
#------------------------------

def compute_potentials(problem, proposal):
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    u = [None] * n
    v = [None] * m

    u[0] = 0

    changed = True
    while changed:
        changed = False

        for i in range(n):
            for j in range(m):
                if proposal[i][j] is not None:  # basic cell
                    if u[i] is not None and v[j] is None:
                        v[j] = costs[i][j] - u[i]
                        changed = True
                    elif v[j] is not None and u[i] is None:
                        u[i] = costs[i][j] - v[j]
                        changed = True

    return u, v

def potential_costs(problem, u, v):
    n, m = problem["n"], problem["m"]

    table = [[u[i] + v[j] for j in range(m)] for i in range(n)]

    print("\n=== POTENTIAL COSTS ===")
    for i in range(n):
        print(table[i])

    return table

#------------------------------
# MARGINAL COSTS
#------------------------------

def marginal_costs(problem, u, v):
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    table = [[costs[i][j] - u[i] - v[j] for j in range(m)] for i in range(n)]

    print("\n=== MARGINAL COSTS ===")
    for i in range(n):
        print(table[i])

    return table

#-------------------------------
# CYCLE PART
#-------------------------------

def find_improving_cell(problem, u, v, proposal):
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    best_value = 0
    best_cell = None

    for i in range(n):
        for j in range(m):
            if proposal[i][j] is None:  # non-basic cell
                delta = costs[i][j] - u[i] - v[j]

                if delta < best_value:
                    best_value = delta
                    best_cell = (i, j)

    return best_cell, best_value

# Test acyclic
def detect_cycle(graph):
    visited = set()

    for start in graph:
        if start not in visited:
            queue = deque([(start, None)])
            parent_map = {start: None}

            while queue:
                node, parent = queue.popleft()

                if node in visited:
                    # reconstruct cycle
                    cycle = [node]
                    p = parent
                    while p and p not in cycle:
                        cycle.append(p)
                        p = parent_map[p]
                    cycle.append(node)

                    print("Cycle found:", cycle)
                    return True

                visited.add(node)

                for neighbor in graph[node]:
                    if neighbor != parent:
                        parent_map[neighbor] = node
                        queue.append((neighbor, node))

    return False

def transportation_maximization(proposal, cycle):
    """
    Perform the 'transportation maximization' step once a cycle is detected.

    Steps:
    1. Assign alternating signs (+ / -) to the cells of the cycle
    2. Compute theta = minimum value among '-' cells
    3. Identify and display the edge(s) that will be removed (value becomes 0)

    Parameters:
        proposal : current transportation matrix (n x m)
        cycle    : list of (i, j) tuples representing the cycle
    """

    print("\n=== TRANSPORTATION MAXIMIZATION ===")

    # --------------------------------------------------------
    # Step 1: Display conditions (+ / -) for each box
    # --------------------------------------------------------
    print("\nConditions for each box:")

    minus_cells = []  # store cells with '-' sign

    for k, (i, j) in enumerate(cycle):
        if k % 2 == 0:
            sign = "+"
        else:
            sign = "-"
            minus_cells.append((i, j))

        print(f"{sign} P{i+1}, C{j+1}")

    # --------------------------------------------------------
    # Step 2: Compute theta
    # Theta = minimum value among cells with '-' sign
    # --------------------------------------------------------
    theta = min(proposal[i][j] for i, j in minus_cells)

    print(f"\nTheta (maximum transport): {theta}")

    # --------------------------------------------------------
    # Step 3: Identify deleted edges
    # A deleted edge is a '-' cell that becomes 0 after subtraction
    # --------------------------------------------------------
    print("\nDeleted edge(s):")

    deleted_found = False

    for (i, j) in minus_cells:
        if proposal[i][j] == theta:
            print(f"P{i+1}, C{j+1}")
            deleted_found = True

    if not deleted_found:
        print("None")

# --------------------------------------------------------------------------------------------------------------------------



# ---------------------------------------
# test if connected BFS
# ---------------------------------------

if __name__ == "__main__":
    import os

    from read_problem import (
        read_problem,
        display_cost_matrix,
        display_transport_proposal,
        total_cost
    )

    from north_west import north_west
    # from balas_hammer import balas_hammer  # optional

    from graph_utils import (
        build_graph,
        find_connected_components,
        connect_graph,
        test_connectivity
    )

    from stepping_stone import (
        compute_potentials,
        potential_costs,
        marginal_costs
    )

    # -----------------------------------
    # SELECT FILE
    # -----------------------------------
    folder = input("Path to problem folder: ").strip()

    if not os.path.exists(folder):
        print("Folder not found")
        exit()

    files = sorted([f for f in os.listdir(folder) if f.endswith(".txt")])

    if not files:
        print("No .txt files found")
        exit()

    print("\nAvailable files:")
    for i, f in enumerate(files):
        print(f"{i+1}. {f}")

    choice = int(input("\nChoose file: ")) - 1

    if choice < 0 or choice >= len(files):
        print("Invalid choice")
        exit()

    filepath = os.path.join(folder, files[choice])

    print("\n" + "=" * 60)
    print(f"FILE: {files[choice]}")
    print("=" * 60)

    # -----------------------------------
    # 1. READ PROBLEM
    # -----------------------------------
    problem = read_problem(filepath)

    # -----------------------------------
    # 2. DISPLAY COST MATRIX
    # -----------------------------------
    display_cost_matrix(problem)

    # -----------------------------------
    # 3. INITIAL SOLUTION
    # -----------------------------------
    proposal = north_west(problem)
    # proposal = balas_hammer(problem)

    display_transport_proposal(problem, proposal)

    print(f"\nTotal cost: {total_cost(problem, proposal)}")

    # -----------------------------------
    # 4. CONNECTIVITY BEFORE FIX
    # -----------------------------------
    print("\n=== BEFORE CONNECT ===")
    test_connectivity(proposal)

    # -----------------------------------
    # 5. FIX CONNECTIVITY (CRUCIAL STEP)
    # -----------------------------------
    proposal = connect_graph(problem, proposal)

    # -----------------------------------
    # 6. CONNECTIVITY AFTER FIX
    # -----------------------------------
    print("\n=== AFTER CONNECT ===")
    test_connectivity(proposal)

    # -----------------------------------
    # 7. DISPLAY UPDATED PROPOSAL
    # -----------------------------------
    display_transport_proposal(problem, proposal)

    # -----------------------------------
    # 8. COMPUTE POTENTIALS
    # -----------------------------------
    u, v = compute_potentials(problem, proposal)

    print("\nPotentials:")
    print("u =", u)
    print("v =", v)

    # -----------------------------------
    # 9. COST TABLES
    # -----------------------------------
    potential_costs(problem, u, v)
    marginal_costs(problem, u, v)