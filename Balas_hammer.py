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
        candidates = []

        print("\nPenalties:")

        # Check row penalties
        for i in active_rows:
            values = [(costs[i][j], i, j) for j in active_cols]
            penalty, min_cell = compute_penalty(values)

            print(f"Row S{i+1}: {penalty}")

            if penalty is not None:
                candidates.append({
                    "kind": "row",
                    "idx": i,
                    "penalty": penalty,
                    "cell": min_cell,
                })

        # Check column penalties
        for j in active_cols:
            values = [(costs[i][j], i, j) for i in active_rows]
            penalty, min_cell = compute_penalty(values)

            print(f"Column C{j+1}: {penalty}")

            if penalty is not None:
                candidates.append({
                    "kind": "column",
                    "idx": j,
                    "penalty": penalty,
                    "cell": min_cell,
                })

        best_penalty = max(candidate["penalty"] for candidate in candidates)
        best_candidates = [
            candidate for candidate in candidates
            if candidate["penalty"] == best_penalty
        ]
        best_candidate = best_candidates[0]
        best_select = best_candidate["kind"]
        best_idx = best_candidate["idx"]

        row_labels = [
            f"S{candidate['idx']+1}"
            for candidate in best_candidates
            if candidate["kind"] == "row"
        ]
        col_labels = [
            f"C{candidate['idx']+1}"
            for candidate in best_candidates
            if candidate["kind"] == "column"
        ]

        print(f"\nMax penalty: {best_penalty}")
        if row_labels:
            print("Row(s) with max penalty: " + ", ".join(row_labels))
        if col_labels:
            print("Column(s) with max penalty: " + ", ".join(col_labels))
        if len(best_candidates) > 1:
            print(
                f"Chosen candidate: {best_select} {best_idx+1} "
                "(tie-break: first in scan order)"
            )
        else:
            print(f"Chosen candidate: {best_select} {best_idx+1}")

        # Allocation on selected cell
        # choice of edge
        _, i, j = best_candidate["cell"]
        print(f"Selected cell: S{i+1}, C{j+1} (cost = {costs[i][j]})")
        qty = min(provisions[i], orders[j])
        proposal[i][j] = qty

        provisions[i] -= qty
        orders[j] -= qty

        # Remove satisfied row or column
        if provisions[i] == 0 and orders[j] == 0:
            active_rows.remove(i)
            active_cols.remove(j)
        elif provisions[i] == 0:
            active_rows.remove(i)
        else:
            active_cols.remove(j)

    return proposal
