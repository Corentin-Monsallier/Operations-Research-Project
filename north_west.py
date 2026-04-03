from read_problem import read_problem, display_cost_matrix, display_transport_proposal, total_cost

# ============================================================
#  ALGORITHME NORD-OUEST
#
#  Principe :
#  - On part de la case (0, 0) en haut à gauche
#  - On alloue le maximum possible : min(provision[i], order[j])
#  - Si la provision du fournisseur i est épuisée → on descend (i++)
#  - Si la commande du client j est satisfaite   → on va à droite (j++)
#  - On s'arrête quand i == n et j == m
# ============================================================

def north_west(problem):
    """
    Calcule la proposition initiale par la méthode Nord-Ouest.
    Retourne une matrice n×m (None = case vide, entier = quantité transportée).
    """
    n, m = problem["n"], problem["m"]

    # Copies des provisions et commandes (on va les modifier)
    provisions = problem["provisions"][:]
    orders     = problem["orders"][:]

    # Initialisation de la proposition à None
    proposal = [[None] * m for _ in range(n)]

    i, j = 0, 0  # On commence en haut à gauche

    while i < n and j < m:

        # Quantité allouée = minimum de ce qui reste disponible
        qty = min(provisions[i], orders[j])
        proposal[i][j] = qty

        provisions[i] -= qty
        orders[j]     -= qty

        print(f"  Alloue {qty} de P{i+1} vers C{j+1} "
              f"(provision restante : {provisions[i]}, commande restante : {orders[j]})")

        # Avancer dans la bonne direction
        if provisions[i] == 0 and orders[j] == 0:
            # Les deux épuisés en même temps → cas dégénéré, on avance en diagonale
            i += 1
            j += 1
        elif provisions[i] == 0:
            i += 1  # Fournisseur épuisé → ligne suivante
        else:
            j += 1  # Commande satisfaite → colonne suivante

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

                print("\n--- Étapes Nord-Ouest ---")
                proposal = north_west(problem)

                display_transport_proposal(problem, proposal)
                print(f"\nCoût total (Nord-Ouest) : {total_cost(problem, proposal)}")

            except Exception as e:
                print(f"  ERREUR : {e}")