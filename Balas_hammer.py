from read_problem import total_cost
import numpy as np

# -----------------------------
# BALAS-HAMMER
# 1) We look at the 2 smallest costs
# 2) Look at the penalty = diff between 2 smallest costs
# 3) Choose row/column with biggest penalty
# -----------------------------


def compute_penalty_optimized(idx, is_row, active_rows, active_cols, costs):
    # optimized version with numpy
    if np is not None and hasattr(costs, "shape"):
        if is_row:
            if not active_cols:
                return -1, None

            # get all costs still possible in this row
            available_costs = costs[idx, active_cols]

            # find position of smallest cost
            best_pos = int(available_costs.argmin())
            # convert to real column index
            best_j = active_cols[best_pos]

            # if only one value = penalty
            if available_costs.size == 1:
                penalty = int(available_costs[0])
            else:
                # np.partition get the 2 smallest values
                two_smallest = np.partition(available_costs, 1)[:2]
                penalty = int(two_smallest[1] - two_smallest[0])

            return penalty, (idx, best_j)
        
        # same operations on column
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
    
    # ----------------------------------------------------------------------------
    # first version without numpy, less optimized
    best_cost = None
    second_best_cost = None
    cell = None

    if is_row:
        for j in active_cols:
            cost = costs[idx][j]

            # update best and second best
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

    # no valid cell found
    if best_cost is None:
        return -1, None

    # if only one value = penalty
    if second_best_cost is None:
        penalty = best_cost
    else:
        penalty = second_best_cost - best_cost

    return penalty, cell

# create a simple text label to display a row or a column
def _format_penalty_label(is_row, idx):
    prefix = "Row" if is_row else "Column"
    return f"{prefix} {idx + 1}"

# find the row(s) or column(s) with the highest penalty
def _best_candidates(row_penalties, col_penalties):
    max_penalty = -1
    candidates = []

    # check all rows
    for i, (pen, cell) in row_penalties.items():
        if pen > max_penalty:
            # new best penalty => replace everything
            max_penalty = pen
            candidates = [(True, i, cell)] # true = row
        elif pen == max_penalty:
            # if same value = we keep it also
            candidates.append((True, i, cell))

    # check all columns
    for j, (pen, cell) in col_penalties.items():
        if pen > max_penalty:
            max_penalty = pen
            candidates = [(False, j, cell)]
        elif pen == max_penalty:
            candidates.append((False, j, cell))

    return max_penalty, candidates


# application of the BH method, faster version with np
def _balas_hammer_vectorized(n, m, costs_np, provisions, orders):
    # result table
    proposal = [[None] * m for _ in range(n)]

    # local copies provisions and orders
    prov = list(provisions)
    ord_ = list(orders)

    ar = np.arange(n, dtype=np.int32) # active rows
    ac = np.arange(m, dtype=np.int32) # active columns

    # continue while we still have rows and columns
    while ar.size > 0 and ac.size > 0:
        nr, nc = ar.size, ac.size

        # get the remaining costs (submatrix)
        sub = costs_np[ar[:, None], ac[None, :]]

        # row penalties = difference between 2 smallest values
        if nc >= 2:
            part_r = np.partition(sub, 1, axis=1)
            row_pen = part_r[:, 1].astype(np.int32) - part_r[:, 0].astype(np.int32)
        else:
            row_pen = sub[:, 0].astype(np.int32)

        # best column for each row
        row_best_local = sub.argmin(axis=1)

        # same for column
        if nr >= 2:
            part_c = np.partition(sub, 1, axis=0)
            col_pen = part_c[1].astype(np.int32) - part_c[0].astype(np.int32)
        else:
            col_pen = sub[0].astype(np.int32)

        # best row for each column
        col_best_local = sub.argmin(axis=0)

        # compare best row vs best column
        max_r = int(row_pen.max())
        max_c = int(col_pen.max())

        if max_r >= max_c:
            # choose row
            li = int(row_pen.argmax())
            lj = int(row_best_local[li])
        else:
            # choose column
            lj = int(col_pen.argmax())
            li = int(col_best_local[lj])

        # convert local indices => real indices
        r, c = int(ar[li]), int(ac[lj])

        # quantity to send = min of supply and demand
        qty = min(prov[r], ord_[c])
        proposal[r][c] = qty
        prov[r] -= qty
        ord_[c] -= qty

        # remove row/column if finished
        if prov[r] == 0:
            ar = ar[ar != r]
        if ord_[c] == 0:
            ac = ac[ac != c]

    return proposal

# initial balas_hammer
def balas_hammer(problem, display=False):
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]
    provisions = problem["provisions"][:]
    orders = problem["orders"][:]

    # version with numpy
    if np is not None and not display:
        if isinstance(costs, np.ndarray):
            costs_np = costs
        else:
            costs_np = np.asarray(costs, dtype=np.int32)
        return _balas_hammer_vectorized(n, m, costs_np, provisions, orders)

    # explicit version
    proposal = [[None] * m for _ in range(n)]

    # Rows and columns still available.
    active_rows = list(range(n))
    active_cols = list(range(m))

    # dictionaries: key = row/column index // value = (penalty, associated best cell)
    row_penalties = {}
    col_penalties = {}

    # First calculation of all penalties.
    for i in active_rows:
        row_penalties[i] = compute_penalty_optimized(i, True, active_rows, active_cols, costs)
    for j in active_cols:
        col_penalties[j] = compute_penalty_optimized(j, False, active_rows, active_cols, costs)

    # main loop: we choose one cell to fill at each turn
    while active_rows and active_cols:
        max_penalty, candidates = _best_candidates(row_penalties, col_penalties)
        best_candidate = candidates[0] if candidates else None

        if best_candidate is None:
            break

        _is_row, _idx, (r, c) = best_candidate

        if display:
            # for the trace : we display all tied rows/columns.
            labels = [
                _format_penalty_label(candidate_is_row, candidate_idx)
                for candidate_is_row, candidate_idx, _cell in candidates
            ]
            print(f"Maximum penalty = {max_penalty}")
            print("Rows/columns with maximum penalty:", ", ".join(labels))
            print(f"Chosen edge: S{r+1}, C{c+1} (cost = {costs[r][c]})")

        # assign everything possible in the best chosen cell
        qty = min(provisions[r], orders[c])
        proposal[r][c] = qty
        provisions[r] -= qty
        orders[c] -= qty

        # booleans used to know which penalties to recompute
        removed_row = False
        removed_col = False

        # if the row has no more supply, we remove it completely
        if provisions[r] == 0:
            active_rows.remove(r)
            del row_penalties[r]
            removed_row = True

        # if the column has no more orders, we remove it completely
        if orders[c] == 0 and c in active_cols:
            active_cols.remove(c)
            del col_penalties[c]
            removed_col = True

        # when a row disappears, all still active columns may see their penalty change
        if removed_row:
            for j in active_cols:
                col_penalties[j] = compute_penalty_optimized(j, False, active_rows, active_cols, costs)

        # same with column
        if removed_col:
            for i in active_rows:
                row_penalties[i] = compute_penalty_optimized(i, True, active_rows, active_cols, costs)

        if display:
            print(f"Allocated {qty} at ({r+1},{c+1}), Penalty: {max_penalty}")

    return proposal
