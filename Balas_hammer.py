from read_problem import read_problem, display_cost_matrix, display_transport_proposal, total_cost
import os

# ============================================================
# BALAS-HAMMER METHOD
#
# Builds an initial solution using penalties:
# - For each row/column, compute penalty = difference between
#   the two smallest costs
# - Choose the row/column with the highest penalty
# - Allocate as much as possible to the cheapest cell
# - Remove satisfied row/column
# ============================================================

def compute_penalty(values):
    # values = list of (cost, i, j) for active cells
    if not values:
        return None, None

    values_sorted = sorted(values, key=lambda x: x[0])

    min1 = values_sorted[0]

    if len(values_sorted) == 1:
        penalty = min1[0]
    else:
        penalty = values_sorted[1][0] - values_sorted[0][0]

    return penalty, min1


def balas_hammer(problem):
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    provisions = problem["provisions"][:]
    orders = problem["orders"][:]

    proposal = [[None] * m for _ in range(n)]

    active_rows = list(range(n))
    active_cols = list(range(m))

    while active_rows and active_cols:

        best_penalty = -1
        best_is_row = True
        best_idx = None
        best_cell = None

        print("\nPenalties:")

        # Check row penalties
        for i in active_rows:
            values = [(costs[i][j], i, j) for j in active_cols]
            penalty, min_cell = compute_penalty(values)

            print(f"Row P{i+1}: {penalty}")

            if penalty is not None and penalty > best_penalty:
                best_penalty = penalty
                best_is_row = True
                best_idx = i
                best_cell = min_cell

        # Check column penalties
        for j in active_cols:
            values = [(costs[i][j], i, j) for i in active_rows]
            penalty, min_cell = compute_penalty(values)

            print(f"Column C{j+1}: {penalty}")

            if penalty is not None and penalty > best_penalty:
                best_penalty = penalty
                best_is_row = False
                best_idx = j
                best_cell = min_cell

        best_select = "row" if best_is_row else "column"
        print(f"\nMax penalty: {best_penalty} on {best_select} {best_idx+1}")
        print(f"Selected cell: P{i+1}, C{j+1} (cost = {costs[i][j]})")
        # Allocation on selected cell
        # choice of edge
        _, i, j = best_cell
        qty = min(provisions[i], orders[j])
        proposal[i][j] = qty

        provisions[i] -= qty
        orders[j] -= qty

        # Remove satisfied row or column
        if provisions[i] == 0 and orders[j] == 0:
            active_rows.remove(i)   # degenerate case
        elif provisions[i] == 0:
            active_rows.remove(i)
        else:
            active_cols.remove(j)

    return proposal


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    folder = input("Path to problem folder: ").strip()

    if not os.path.exists(folder):
        print(f"Folder not found: {folder}")
    else:
        txt_files = sorted([f for f in os.listdir(folder) if f.endswith(".txt")])

        for filename in txt_files:
            filepath = os.path.join(folder, filename)

            print("\n" + "=" * 60)
            print(f"FILE: {filename}")
            print("=" * 60)

            try:
                problem = read_problem(filepath)

                # Display input
                display_cost_matrix(problem)

                # Run Balas-Hammer
                print("\n--- Balas-Hammer solution ---")
                proposal = balas_hammer(problem)

                display_transport_proposal(problem, proposal)

                cost = total_cost(problem, proposal)
                print(f"\nTotal cost (Balas-Hammer): {cost}")

            except Exception as e:
                print(f"ERROR: {e}")