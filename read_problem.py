import os

# ============================================================
#  STRUCTURE D'UN PROBLÈME DE TRANSPORT
#
#  Un problème est représenté par un dictionnaire avec :
#    - n          : nombre de fournisseurs (lignes de la matrice)
#    - m          : nombre de clients (colonnes de la matrice)
#    - costs      : matrice des coûts unitaires, taille n×m
#                   costs[i][j] = coût d'envoi du fournisseur i au client j
#    - provisions : offre de chaque fournisseur, liste de n entiers
#                   provisions[i] = quantité disponible chez le fournisseur i
#    - orders     : demande de chaque client, liste de m entiers
#                   orders[j]     = quantité demandée par le client j
# ============================================================

def create_problem(n, m, costs, provisions, orders):
    return {
        "n": n,
        "m": m,
        "costs": costs,
        "provisions": provisions,
        "orders": orders
    }

# ============================================================
#  1. LECTURE D'UN FICHIER PROBLÈME (.TXT)
#
#  Format attendu dans le fichier (les lignes non-numériques
#  comme les titres ou commentaires sont ignorées) :
#
#    n  m                          <- dimensions
#    c11 c12 ... c1m  P1           <- coûts ligne 1 + provision fournisseur 1
#    c21 c22 ... c2m  P2           <- coûts ligne 2 + provision fournisseur 2
#    ...
#    cn1 cn2 ... cnm  Pn           <- coûts ligne n + provision fournisseur n
#    C1  C2  ... Cm                <- commandes des clients
# ============================================================

def read_problem(filepath):
    """
    Lit un fichier .txt et retourne un problème de transport.

    Stratégie de parsing :
      1. Lire toutes les lignes non vides du fichier.
      2. Conserver uniquement les lignes dont tous les tokens sont des entiers
         (entiers éventuellement négatifs) — cela filtre titres et commentaires.
      3. Interpréter les lignes numériques dans l'ordre attendu du format ci-dessus.
    """
    with open(filepath, "r") as f:
        # strip() supprime les espaces/retours chariot en début et fin de chaque ligne.
        # Le "if line.strip()" dans la condition écarte les lignes entièrement vides.
        raw_lines = [line.strip() for line in f if line.strip()]

    # Les fichiers contiennent souvent des titres ou commentaires textuels
    # (ex: "Problème 3 - coûts de transport"). On veut ignorer ces lignes
    # et ne garder que celles dont TOUS les mots sont des entiers.
    #
    # Stratégie : on découpe chaque ligne en "tokens" (mots séparés par des espaces),
    # puis on vérifie que chaque token est un entier.
    #   - lstrip("-") retire un éventuel signe négatif avant de tester isdigit()
    #     car "-5".isdigit() retourne False, mais "5".isdigit() retourne True.
    #   - isdigit() retourne True si tous les caractères restants sont des chiffres.
    # Si la condition est vraie pour tous les tokens, on convertit la ligne en liste
    # d'entiers avec map(int, ...) et on l'ajoute à numeric_lines.
    numeric_lines = []
    for line in raw_lines:
        tokens = line.split()
        if all(t.lstrip("-").isdigit() for t in tokens):
            numeric_lines.append(list(map(int, tokens)))

    # Ligne 0 : dimensions du problème
    n, m = numeric_lines[0][0], numeric_lines[0][1]

    costs      = []
    provisions = []

    # Lignes 1..n : chaque ligne contient m+1 valeurs pour le fournisseur i.
    #   row[:m]  → les m premiers entiers = coûts unitaires vers chaque client
    #              (slicing Python : indices 0 à m-1 inclus)
    #   row[m]   → le dernier entier = provision (offre disponible)
    #              (index m, c'est-à-dire le (m+1)-ième élément)
    for i in range(1, n + 1):
        row = numeric_lines[i]
        costs.append(row[:m])       # ex: [12, 8, 5] si m=3
        provisions.append(row[m])   # ex: 120

    # Ligne n+1 : demandes des m clients (commandes)
    orders = numeric_lines[n + 1][:m]

    return create_problem(n, m, costs, provisions, orders)

# ============================================================
#  2. FONCTIONS D'AFFICHAGE
#
#  Toutes les fonctions d'affichage alignent leurs colonnes :
#  on calcule d'abord la largeur maximale de chaque colonne
#  (en tenant compte à la fois des valeurs et du nom d'en-tête),
#  puis on formate chaque cellule avec un alignement à droite.
# ============================================================

def _col_width(values, header=""):
    """
    Calcule la largeur minimale nécessaire pour afficher une colonne,
    c'est-à-dire le maximum entre :
      - la longueur de la valeur la plus longue de la colonne
      - la longueur du nom d'en-tête

    Exemple : valeurs [3, 120, 45], header="Prov."
      → max des longueurs = len("120") = 3
      → len("Prov.") = 5
      → résultat = 5  (on utilise la largeur de l'en-tête)

    Le paramètre default=0 dans max() évite une erreur si values est vide.
    """
    max_val = max((len(str(v)) for v in values), default=0)
    return max(max_val, len(str(header)))


# NOTE SUR LE FORMATAGE DES CELLULES (f-strings)
# -----------------------------------------------
# Dans tout ce fichier, on utilise la syntaxe f"{valeur:>{largeur}}" pour
# aligner les cellules à droite dans une largeur fixe. Exemples :
#   f"{42:>6}"   → "    42"   (42 aligné à droite dans 6 caractères)
#   f"{'C1':>4}" → "  C1"    (texte aligné à droite dans 4 caractères)
#   f"{5:<5}"    → "5    "    (5 aligné à GAUCHE dans 5 caractères, utilisé pour les labels "Pi")
# Le :> signifie "aligner à droite", :< signifie "aligner à gauche".


def display_cost_matrix(problem):
    """
    Affiche la matrice des coûts unitaires sous forme de tableau :

        C1   C2  ...  Cm   Prov.
      --------------------------------
      P1  c11  c12  ... c1m  P1
      P2  c21  c22  ... c2m  P2
      ...
      --------------------------------
      Ord.  C1   C2  ...  Cm
    """
    n, m = problem["n"], problem["m"]
    costs      = problem["costs"]
    provisions = problem["provisions"]
    orders     = problem["orders"]

    print("\n=== MATRICE DES COÛTS ===")

    # Pour chaque colonne j, on collecte toutes les valeurs qui apparaîtront
    # dans cette colonne (coûts + commande) afin de calculer la largeur nécessaire.
    # On inclut orders[j] car la commande s'affiche aussi dans cette colonne (dernière ligne).
    col_widths = []
    for j in range(m):
        col_vals = [costs[i][j] for i in range(n)] + [orders[j]]
        col_widths.append(_col_width(col_vals, f"C{j+1}"))
    # Même logique pour la colonne provision, en incluant le libellé "Prov." comme valeur possible
    prov_width = _col_width(provisions + ["Prov."], "Prov.")

    # Construction de la ligne d'en-tête :
    #   "        " → 8 espaces pour laisser la place aux labels "P1    " en début de ligne
    #   "  ".join(...) → les noms de colonnes séparés par 2 espaces, chacun aligné à droite
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    header += f"  {'Prov.':>{prov_width}}"
    print(header)
    # Séparateur de même longueur que l'en-tête (on enlève les 2 premiers espaces du "-"*N)
    print("  " + "-" * (len(header) - 2))

    # Une ligne par fournisseur :
    #   f"P{i+1:<5} " → label aligné à gauche sur 5 caractères (ex: "P1    ")
    #   puis les coûts de la ligne, chacun aligné à droite dans sa colonne
    for i in range(n):
        row = f"P{i+1:<5} " + "  ".join(f"{costs[i][j]:>{col_widths[j]}}" for j in range(m))
        row += f"  {provisions[i]:>{prov_width}}"
        print(row)

    print("  " + "-" * (len(header) - 2))

    # Ligne des commandes (demandes clients), sans colonne provision
    orders_row = "Ord.   " + "  ".join(f"{orders[j]:>{col_widths[j]}}" for j in range(m))
    print(orders_row)


def display_transport_proposal(problem, proposal):
    """
    Affiche une proposition de transport : quantités allouées à chaque case.

    proposal : matrice n×m (liste de listes)
                proposal[i][j] = quantité transportée de P_i vers C_j
                None           = case non utilisée (affichée avec '·')
    """
    n, m = problem["n"], problem["m"]
    provisions = problem["provisions"]
    orders     = problem["orders"]

    print("\n=== PROPOSITION DE TRANSPORT ===")

    # On ignore les cases None pour calculer la largeur (elles affichent '·', 1 seul caractère).
    # On inclut quand même orders[j] car la commande s'affiche dans la même colonne.
    col_widths = []
    for j in range(m):
        col_vals = [proposal[i][j] for i in range(n) if proposal[i][j] is not None]
        col_vals += [orders[j]]
        col_widths.append(_col_width(col_vals, f"C{j+1}"))
    prov_width = _col_width(provisions + ["Prov."], "Prov.")

    # En-tête
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    header += f"  {'Prov.':>{prov_width}}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    # Une ligne par fournisseur : quantités allouées (ou '·' si case vide) + provision
    for i in range(n):
        cells = []
        for j in range(m):
            val = proposal[i][j]
            # Case utilisée → valeur numérique ; case vide → point médian '·'
            cells.append(f"{val:>{col_widths[j]}}" if val is not None else f"{'·':>{col_widths[j]}}")
        row = f"P{i+1:<5} " + "  ".join(cells) + f"  {provisions[i]:>{prov_width}}"
        print(row)

    print("  " + "-" * (len(header) - 2))

    # Ligne des commandes
    orders_row = "Ord.   " + "  ".join(f"{orders[j]:>{col_widths[j]}}" for j in range(m))
    print(orders_row)


def display_potential_costs(problem, u, v):
    """
    Affiche le tableau des coûts potentiels u[i] + v[j].

    Dans la méthode du simplexe de transport, u et v sont les potentiels
    (variables duales) associés respectivement aux fournisseurs et aux clients.
    Pour toute case de base (i, j), on a : c[i][j] = u[i] + v[j].
    Ce tableau permet de visualiser ces valeurs reconstruites.

    u : liste de n potentiels fournisseurs
    v : liste de m potentiels clients
    """
    n, m = problem["n"], problem["m"]

    print("\n=== TABLEAU DES COÛTS POTENTIELS (u[i] + v[j]) ===")

    # Double list comprehension : pour chaque ligne i, on calcule u[i]+v[j] pour chaque colonne j.
    # Résultat : une matrice n×m, pot_costs[i][j] = u[i] + v[j].
    pot_costs = [[u[i] + v[j] for j in range(m)] for i in range(n)]

    col_widths = []
    for j in range(m):
        col_vals = [pot_costs[i][j] for i in range(n)]
        col_widths.append(_col_width(col_vals, f"C{j+1}"))

    # En-tête
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    print(header)
    print("  " + "-" * (len(header) - 2))

    for i in range(n):
        row = f"P{i+1:<5} " + "  ".join(f"{pot_costs[i][j]:>{col_widths[j]}}" for j in range(m))
        print(row)


def display_marginal_costs(problem, u, v):
    """
    Affiche le tableau des coûts marginaux (ou coûts réduits) :
        delta[i][j] = c[i][j] - u[i] - v[j]

    Interprétation :
      - delta[i][j] = 0  → case de base (dans la solution courante)
      - delta[i][j] > 0  → entrer cette case augmenterait le coût total
      - delta[i][j] < 0  → entrer cette case réduirait le coût total
                           (critère d'amélioration dans le simplexe de transport)

    u : liste de n potentiels fournisseurs
    v : liste de m potentiels clients
    """
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    print("\n=== TABLEAU DES COÛTS MARGINAUX (c[i][j] - u[i] - v[j]) ===")

    # Même structure que pot_costs, mais on soustrait le coût réel :
    # marginals[i][j] = c[i][j] - u[i] - v[j]
    marginals = [[costs[i][j] - u[i] - v[j] for j in range(m)] for i in range(n)]

    col_widths = []
    for j in range(m):
        col_vals = [marginals[i][j] for i in range(n)]
        col_widths.append(_col_width(col_vals, f"C{j+1}"))

    # En-tête
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    print(header)
    print("  " + "-" * (len(header) - 2))

    for i in range(n):
        cells = [f"{marginals[i][j]:>{col_widths[j]}}" for j in range(m)]
        print(f"P{i+1:<5} " + "  ".join(cells))


# ============================================================
#  3. CALCUL DU COÛT TOTAL D'UNE SOLUTION
# ============================================================

def total_cost(problem, proposal):
    """
    Calcule le coût total d'une proposition de transport.

    Pour chaque case (i, j) utilisée (valeur > 0 et non None),
    on ajoute la contribution : coût_unitaire[i][j] × quantité[i][j].

    Retourne la somme totale (entier ou flottant).
    """
    n, m = problem["n"], problem["m"]
    cost = 0
    for i in range(n):
        for j in range(m):
            if proposal[i][j] is not None and proposal[i][j] > 0:
                cost += problem["costs"][i][j] * proposal[i][j]
    return cost


# ============================================================
#  4. UTILITAIRE : TESTER TOUS LES FICHIERS D'UN DOSSIER
#
#  Parcourt tous les .txt du dossier indiqué, charge chaque
#  problème et affiche sa matrice des coûts. Utile pour vérifier
#  que tous les fichiers sont bien formatés et lisibles.
# ============================================================

def test_all_problems(folder):
    # os.listdir() renvoie tous les fichiers du dossier (sans ordre garanti).
    # On filtre sur l'extension .txt, puis sorted() trie par nom alphabétique
    # pour traiter les problèmes dans un ordre prévisible (problem_1, problem_2, ...).
    txt_files = sorted([f for f in os.listdir(folder) if f.endswith(".txt")])
    if not txt_files:
        print(f"Aucun fichier .txt trouvé dans : {folder}")
        return
    for filename in txt_files:
        filepath = os.path.join(folder, filename)
        print("\n" + "=" * 60)
        print(f"  FICHIER : {filename}")
        print("=" * 60)
        try:
            problem = read_problem(filepath)
            print(f"Problème chargé : {problem['n']} fournisseurs, {problem['m']} clients")
            display_cost_matrix(problem)
        except Exception as e:
            print(f"  ERREUR : {e}")


if __name__ == "__main__":
    folder = input("Chemin vers le dossier des problèmes : ").strip()
    if not os.path.exists(folder):
        print(f"Dossier introuvable : {folder}")
    else:
        test_all_problems(folder)
