from read_problem import total_cost

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional optimization
    np = None


def compute_penalty_optimized(idx, is_row, active_rows, active_cols, costs):
    """
    Calcule la penalite pour une ligne ou une colonne specifique sans
    trier toute la liste des couts disponibles.
    """
    if np is not None and hasattr(costs, "shape"):
        if is_row:
            if not active_cols:
                return -1, None

            available_costs = costs[idx, active_cols]
            best_pos = int(available_costs.argmin())
            best_j = active_cols[best_pos]

            if available_costs.size == 1:
                penalty = int(available_costs[0])
            else:
                two_smallest = np.partition(available_costs, 1)[:2]
                penalty = int(two_smallest[1] - two_smallest[0])

            return penalty, (idx, best_j)

        if not active_rows:
            return -1, None

        available_costs = costs[active_rows, idx]
        best_pos = int(available_costs.argmin())
        best_i = active_rows[best_pos]

        if available_costs.size == 1:
            penalty = int(available_costs[0])
        else:
            two_smallest = np.partition(available_costs, 1)[:2]
            penalty = int(two_smallest[1] - two_smallest[0])

        return penalty, (best_i, idx)

    best_cost = None
    second_best_cost = None
    cell = None

    if is_row:
        for j in active_cols:
            cost = costs[idx][j]

            if best_cost is None or cost < best_cost:
                second_best_cost = best_cost
                best_cost = cost
                cell = (idx, j)
            elif second_best_cost is None or cost < second_best_cost:
                second_best_cost = cost
    else:
        for i in active_rows:
            cost = costs[i][idx]

            if best_cost is None or cost < best_cost:
                second_best_cost = best_cost
                best_cost = cost
                cell = (i, idx)
            elif second_best_cost is None or cost < second_best_cost:
                second_best_cost = cost

    if best_cost is None:
        return -1, None

    if second_best_cost is None:
        penalty = best_cost
    else:
        penalty = second_best_cost - best_cost

    return penalty, cell


def _format_penalty_label(is_row, idx):
    prefix = "Row" if is_row else "Column"
    return f"{prefix} {idx + 1}"


def _best_candidates(row_penalties, col_penalties):
    max_penalty = -1
    candidates = []

    for i, (pen, cell) in row_penalties.items():
        if pen > max_penalty:
            max_penalty = pen
            candidates = [(True, i, cell)]
        elif pen == max_penalty:
            candidates.append((True, i, cell))

    for j, (pen, cell) in col_penalties.items():
        if pen > max_penalty:
            max_penalty = pen
            candidates = [(False, j, cell)]
        elif pen == max_penalty:
            candidates.append((False, j, cell))

    return max_penalty, candidates


def _balas_hammer_vectorized(n, m, costs_np, provisions, orders):
    """
    Fast BH for display=False using np.partition on the active sub-matrix.
    All penalties are recomputed each step via vectorized numpy — no Python
    loops over rows/cols.  Same algorithm, different execution path.
    """
    proposal = [[None] * m for _ in range(n)]
    prov = list(provisions)
    ord_ = list(orders)
    ar = np.arange(n, dtype=np.int32)
    ac = np.arange(m, dtype=np.int32)

    while ar.size > 0 and ac.size > 0:
        nr, nc = ar.size, ac.size

        # Sub-matrix for active (row, col) pairs
        sub = costs_np[ar[:, None], ac[None, :]]  # (nr, nc), copy

        # --- Row penalties: second_min - min along axis=1 ---
        if nc >= 2:
            part_r = np.partition(sub, 1, axis=1)
            row_pen = part_r[:, 1].astype(np.int32) - part_r[:, 0].astype(np.int32)
        else:
            row_pen = sub[:, 0].astype(np.int32)
        row_best_local = sub.argmin(axis=1)   # local col index of min per row

        # --- Col penalties: second_min - min along axis=0 ---
        if nr >= 2:
            part_c = np.partition(sub, 1, axis=0)
            col_pen = part_c[1].astype(np.int32) - part_c[0].astype(np.int32)
        else:
            col_pen = sub[0].astype(np.int32)
        col_best_local = sub.argmin(axis=0)   # local row index of min per col

        max_r = int(row_pen.max())
        max_c = int(col_pen.max())

        if max_r >= max_c:
            li = int(row_pen.argmax())
            lj = int(row_best_local[li])
        else:
            lj = int(col_pen.argmax())
            li = int(col_best_local[lj])

        r, c = int(ar[li]), int(ac[lj])
        qty = min(prov[r], ord_[c])
        proposal[r][c] = qty
        prov[r] -= qty
        ord_[c] -= qty

        if prov[r] == 0:
            ar = ar[ar != r]
        if ord_[c] == 0:
            ac = ac[ac != c]

    return proposal


def balas_hammer(problem, display=False):
    """
    Version optimisee de Balas-Hammer pour les tests de complexite.
    """
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]
    provisions = problem["provisions"][:]
    orders = problem["orders"][:]

    # Fast vectorized path for benchmark (display=False)
    if np is not None and not display:
        if isinstance(costs, np.ndarray):
            costs_np = costs
        else:
            costs_np = np.asarray(costs, dtype=np.int32)
        return _balas_hammer_vectorized(n, m, costs_np, provisions, orders)

    # --- Verbose path (display=True): original incremental logic ---
    proposal = [[None] * m for _ in range(n)]
    active_rows = list(range(n))
    active_cols = list(range(m))

    row_penalties = {}
    col_penalties = {}

    for i in active_rows:
        row_penalties[i] = compute_penalty_optimized(i, True, active_rows, active_cols, costs)
    for j in active_cols:
        col_penalties[j] = compute_penalty_optimized(j, False, active_rows, active_cols, costs)

    while active_rows and active_cols:
        max_penalty, candidates = _best_candidates(row_penalties, col_penalties)
        best_candidate = candidates[0] if candidates else None

        if best_candidate is None:
            break

        _is_row, _idx, (r, c) = best_candidate

        if display:
            labels = [
                _format_penalty_label(candidate_is_row, candidate_idx)
                for candidate_is_row, candidate_idx, _cell in candidates
            ]
            print(f"Maximum penalty = {max_penalty}")
            print("Rows/columns with maximum penalty:", ", ".join(labels))
            print(f"Chosen edge: S{r+1}, C{c+1} (cost = {costs[r][c]})")

        qty = min(provisions[r], orders[c])
        proposal[r][c] = qty
        provisions[r] -= qty
        orders[c] -= qty

        removed_row = False
        removed_col = False

        if provisions[r] == 0:
            active_rows.remove(r)
            del row_penalties[r]
            removed_row = True

        if orders[c] == 0 and c in active_cols:
            active_cols.remove(c)
            del col_penalties[c]
            removed_col = True

        if removed_row:
            for j in active_cols:
                col_penalties[j] = compute_penalty_optimized(j, False, active_rows, active_cols, costs)

        if removed_col:
            for i in active_rows:
                row_penalties[i] = compute_penalty_optimized(i, True, active_rows, active_cols, costs)

        if display:
            print(f"Allocated {qty} at ({r+1},{c+1}), Penalty: {max_penalty}")

    return proposal
