from read_problem import read_problem, display_cost_matrix, display_transport_proposal, total_cost

# ============================================================
#  ALGORITHME BALAS-HAMMER
#
#  Principe :
#  1. Calculer la pénalité de chaque ligne/colonne active :
#       pénalité = 2ème coût minimum - 1er coût minimum
#     (sur les cases non éliminées)
#  2. Choisir la ligne ou colonne avec la pénalité maximale
#     (en cas d'égalité : on prend la première trouvée)
#  3. Dans cette ligne/colonne, allouer le maximum possible
#     à la case ayant le coût minimum
#  4. Éliminer la ligne ou colonne saturée
#  5. Répéter jusqu'à ce que toutes les provisions et
#     commandes soient satisfaites
# ============================================================


def _compute_penalty(values):
    """
    Calcule la pénalité d'une ligne ou colonne.
    values : liste de (coût, i, j) pour les cases encore actives.
    Retourne la pénalité (2ème min - 1er min) et la case du coût minimum.
    """
    if len(values) == 0:
        return None, None

    sorted_vals = sorted(values, key=lambda x: x[0])

    min1 = sorted_vals[0]   # (coût, i, j) le moins cher
    if len(sorted_vals) == 1:
        penalty = min1[0]   # Une seule case : pénalité = coût lui-même
    else:
        penalty = sorted_vals[1][0] - sorted_vals[0][0]

    return penalty, min1


def balas_hammer(problem):
    """
    Calcule la proposition initiale par la méthode Balas-Hammer.
    Retourne une matrice n×m (None = case vide, entier = quantité transportée).
    """
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    provisions = problem["provisions"][:]
    orders     = problem["orders"][:]

    proposal = [[None] * m for _ in range(n)]

    # Lignes et colonnes encore actives
    active_rows = list(range(n))
    active_cols = list(range(m))

    iteration = 0

    while active_rows and active_cols:
        iteration += 1
        print(f"\n--- Itération {iteration} ---")

        best_penalty = -1
        best_is_row  = True   # True = ligne, False = colonne
        best_idx     = None   # index dans active_rows ou active_cols
        best_cell    = None   # (coût, i, j) de la case choisie

        # --- Calcul des pénalités pour chaque ligne active ---
        for i in active_rows:
            values = [(costs[i][j], i, j) for j in active_cols]
            penalty, min_cell = _compute_penalty(values)
            if penalty is not None and penalty > best_penalty:
                best_penalty = penalty
                best_is_row  = True
                best_idx     = i
                best_cell    = min_cell

        # --- Calcul des pénalités pour chaque colonne active ---
        for j in active_cols:
            values = [(costs[i][j], i, j) for i in active_rows]
            penalty, min_cell = _compute_penalty(values)
            if penalty is not None and penalty > best_penalty:
                best_penalty = penalty
                best_is_row  = False
                best_idx     = j
                best_cell    = min_cell

        # --- Affichage de la ligne/colonne choisie ---
        kind = f"P{best_idx+1}" if best_is_row else f"C{best_idx+1}"
        print(f"  Pénalité maximale : {best_penalty} sur {'ligne' if best_is_row else 'colonne'} {kind}")

        # --- Allocation ---
        _, i, j = best_cell
        qty = min(provisions[i], orders[j])
        proposal[i][j] = qty
        provisions[i] -= qty
        orders[j]     -= qty

        print(f"  Alloue {qty} de P{i+1} vers C{j+1} "
              f"(provision restante : {provisions[i]}, commande restante : {orders[j]})")

        # --- Élimination de la ligne ou colonne saturée ---
        if provisions[i] == 0 and orders[j] == 0:
            # Cas dégénéré : on élimine la ligne et on garde la colonne
            active_rows.remove(i)
            print(f"  → Ligne P{i+1} éliminée (provision épuisée) [cas dégénéré]")
        elif provisions[i] == 0:
            active_rows.remove(i)
            print(f"  → Ligne P{i+1} éliminée (provision épuisée)")
        else:
            active_cols.remove(j)
            print(f"  → Colonne C{j+1} éliminée (commande satisfaite)")

    return proposal


# ============================================================
#  TEST
# ============================================================

if __name__ == "__main__":
    import os

    folder = input("Chemin vers le dossier des problèmes : ").strip()

    if not os.path.exists(folder):
        print(f"Dossier introuvable : {folder}")
    else:
        txt_files = sorted([f for f in os.listdir(folder) if f.endswith(".txt")])

        for filename in txt_files:
            filepath = os.path.join(folder, filename)
            print("\n" + "=" * 60)
            print(f"  FICHIER : {filename}")
            print("=" * 60)

            try:
                problem = read_problem(filepath)
                display_cost_matrix(problem)

                print("\n--- Étapes Balas-Hammer ---")
                proposal = balas_hammer(problem)

                display_transport_proposal(problem, proposal)
                print(f"\nCoût total (Balas-Hammer) : {total_cost(problem, proposal)}")

            except Exception as e:
                print(f"  ERREUR : {e}")