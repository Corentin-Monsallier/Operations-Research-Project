from read_problem import total_cost

def compute_penalty_optimized(idx, is_row, active_rows, active_cols, costs):
    """
    Calcule la pénalité pour une ligne ou une colonne spécifique.
    """
    if is_row:
        available_costs = [costs[idx][j] for j in active_cols]
        row_or_col = "row"
    else:
        available_costs = [costs[i][idx] for i in active_rows]
        row_or_col = "col"

    if not available_costs:
        return -1, None

    sorted_costs = sorted(available_costs)
    
    if len(sorted_costs) == 1:
        penalty = sorted_costs[0]
    else:
        penalty = sorted_costs[1] - sorted_costs[0]
    
    if is_row:
        best_j = min(active_cols, key=lambda j: costs[idx][j])
        cell = (idx, best_j)
    else:
        best_i = min(active_rows, key=lambda i: costs[i][idx])
        cell = (best_i, idx)

    return penalty, cell

def balas_hammer(problem, display=False):
    """
    Version optimisée de Balas-Hammer pour les tests de complexité.
    """
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]
    provisions = problem["provisions"][:]
    orders = problem["orders"][:]

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
        max_penalty = -1
        best_candidate = None 

        for i, (pen, cell) in row_penalties.items():
            if pen > max_penalty:
                max_penalty = pen
                best_candidate = (True, i, cell)
        
        for j, (pen, cell) in col_penalties.items():
            if pen > max_penalty:
                max_penalty = pen
                best_candidate = (False, j, cell)

        if best_candidate is None: break

        is_row, idx, (r, c) = best_candidate

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
        
        if orders[c] == 0:
            if c in active_cols: 
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