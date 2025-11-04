"""
============================================================================
PROJET MEC423 - OPTIMISATION DE LA PLINTHE CHAUFFANTE ÉLECTRIQUE
============================================================================

Objectif: Trouver les valeurs optimales de R, a et N qui:
  1. Respectent la contrainte: Tmax ≤ 250°C
  2. Minimisent le coût: Coût = 2·10⁴LR² + 1000Na((R+a)²-R²) + 3·√N

Variables de conception:
  - R: Rayon extérieur du tube [m] (précision 0.001 m)
  - a: Longueur radiale des ailettes [m] (précision 0.001 m)
  - N: Nombre d'ailettes (précision 5 ailettes)

Équipe 10, MEC423-02:
  - L = 3.0 m
  - P = 3.6 kW
  - h = 30 W/(m²·°C)
  - T_air = 60 °C
============================================================================
"""

import numpy as np
from mec423_heating_baseboard import solve_heating_baseboard
import matplotlib.pyplot as plt
import time

# ============================================================================
# PARAMÈTRES DU PROBLÈME
# ============================================================================

# Données du projet (Équipe 10, MEC423-02)
L = 3.0      # Longueur du tube [m]
P = 3600     # Puissance à dissiper [W] (3.6 kW)
h_conv = 30  # Coefficient de convection [W/(m²·°C)]
T_air = 60   # Température de l'air ambiant [°C]
k_c = 150    # Conductivité thermique [W/(m·°C)]

# Contrainte de température
T_max_contrainte = 250  # [°C]

# Paramètres de maillage (pour rapidité d'optimisation)
nr_tube = 5
nr_ailette = 8
nz_ailette = 3
nz_espace = 10

print("="*80)
print(" OPTIMISATION DE LA PLINTHE CHAUFFANTE ÉLECTRIQUE")
print("="*80)
print(f"\nDonnées du projet:")
print(f"  Longueur tube L = {L} m")
print(f"  Puissance P = {P/1000} kW")
print(f"  Convection h = {h_conv} W/(m²·°C)")
print(f"  Température air T_air = {T_air} °C")
print(f"\nContrainte: T_max ≤ {T_max_contrainte} °C")
print(f"Objectif: Minimiser le coût")
print("="*80)

# ============================================================================
# PLAGES DE RECHERCHE
# ============================================================================

# Plages de recherche (inspirées des valeurs typiques)
R_min, R_max = 0.008, 0.020    # Rayon tube: 8 à 20 mm
a_min, a_max = 0.020, 0.050    # Longueur ailettes: 20 à 50 mm
N_min, N_max = 20, 100         # Nombre d'ailettes: 20 à 100

# ============================================================================
# PHASE 1: RECHERCHE GROSSIÈRE (Balayage large)
# ============================================================================

def recherche_grossiere(R_vals, a_vals, N_vals, verbose=True):
    """
    Balayage grossier pour identifier les régions prometteuses.

    Args:
        R_vals: Liste des valeurs de R à tester
        a_vals: Liste des valeurs de a à tester
        N_vals: Liste des valeurs de N à tester
        verbose: Afficher les détails

    Returns:
        Liste de dictionnaires avec les résultats valides
    """
    solutions_valides = []
    total_tests = len(R_vals) * len(a_vals) * len(N_vals)
    test_count = 0

    if verbose:
        print(f"\n{'='*80}")
        print(f" PHASE 1: RECHERCHE GROSSIÈRE")
        print(f"{'='*80}")
        print(f"Tests à effectuer: {total_tests}")
        print(f"  R: {len(R_vals)} valeurs de {R_vals[0]*1000:.1f} à {R_vals[-1]*1000:.1f} mm")
        print(f"  a: {len(a_vals)} valeurs de {a_vals[0]*1000:.1f} à {a_vals[-1]*1000:.1f} mm")
        print(f"  N: {len(N_vals)} valeurs de {N_vals[0]} à {N_vals[-1]}")
        print(f"\nRecherche en cours...")
        start_time = time.time()

    for R in R_vals:
        for a in a_vals:
            for N in N_vals:
                test_count += 1

                # Résoudre le problème thermique
                result = solve_heating_baseboard(
                    L, P, h_conv, T_air, k_c, R, a, N,
                    nr_tube=nr_tube, nr_ailette=nr_ailette,
                    nz_ailette=nz_ailette, nz_espace=nz_espace,
                    verbose=False, plot_results=False
                )

                # Vérifier si la solution est valide
                if result['success'] and result['Tmax'] <= T_max_contrainte:
                    solutions_valides.append({
                        'R': R,
                        'a': a,
                        'N': N,
                        'Tmax': result['Tmax'],
                        'cout': result['cout_total']
                    })

                    if verbose and test_count % 20 == 0:
                        print(f"  [{test_count}/{total_tests}] Solutions valides: {len(solutions_valides)}")

    if verbose:
        elapsed = time.time() - start_time
        print(f"\nRecherche terminée en {elapsed:.1f} secondes")
        print(f"Solutions valides trouvées: {len(solutions_valides)}/{total_tests}")

    return solutions_valides


# ============================================================================
# PHASE 2: RECHERCHE FINE (Raffinement autour des meilleures solutions)
# ============================================================================

def recherche_fine(R_centre, a_centre, N_centre, delta_R, delta_a, delta_N,
                   pas_R, pas_a, pas_N, verbose=True):
    """
    Recherche fine autour d'un point prometteur.

    Args:
        R_centre, a_centre, N_centre: Centre de la recherche
        delta_R, delta_a, delta_N: Étendue de la recherche
        pas_R, pas_a, pas_N: Pas de recherche
        verbose: Afficher les détails

    Returns:
        Liste de dictionnaires avec les résultats valides
    """
    # Générer les plages de recherche fine
    R_vals = np.arange(max(R_min, R_centre - delta_R),
                       min(R_max, R_centre + delta_R) + pas_R/2,
                       pas_R)
    a_vals = np.arange(max(a_min, a_centre - delta_a),
                       min(a_max, a_centre + delta_a) + pas_a/2,
                       pas_a)
    N_vals = np.arange(max(N_min, N_centre - delta_N),
                       min(N_max, N_centre + delta_N) + pas_N,
                       pas_N, dtype=int)

    if verbose:
        print(f"\n{'='*80}")
        print(f" PHASE 2: RECHERCHE FINE")
        print(f"{'='*80}")
        print(f"Centre de recherche:")
        print(f"  R = {R_centre*1000:.3f} mm ± {delta_R*1000:.3f} mm")
        print(f"  a = {a_centre*1000:.3f} mm ± {delta_a*1000:.3f} mm")
        print(f"  N = {N_centre} ± {delta_N}")

    return recherche_grossiere(R_vals, a_vals, N_vals, verbose=verbose)


# ============================================================================
# FONCTION PRINCIPALE D'OPTIMISATION
# ============================================================================

def optimiser_plinthe(methode='complete'):
    """
    Optimise la conception de la plinthe chauffante.

    Args:
        methode: 'complete' (recherche exhaustive en 2 phases) ou
                'rapide' (recherche grossière uniquement)

    Returns:
        dict: Meilleure solution trouvée
    """

    # -------------------------------------------------------------------------
    # PHASE 1: RECHERCHE GROSSIÈRE
    # -------------------------------------------------------------------------

    # Définir les plages de recherche grossière
    R_vals_grossier = np.arange(R_min, R_max + 0.001, 0.002)  # Pas de 2 mm
    a_vals_grossier = np.arange(a_min, a_max + 0.001, 0.005)  # Pas de 5 mm
    N_vals_grossier = np.arange(N_min, N_max + 1, 10, dtype=int)  # Pas de 10 ailettes

    # Effectuer la recherche grossière
    solutions_grossieres = recherche_grossiere(
        R_vals_grossier, a_vals_grossier, N_vals_grossier, verbose=True
    )

    if len(solutions_grossieres) == 0:
        print("\n⚠ AUCUNE SOLUTION VALIDE trouvée dans la recherche grossière!")
        print("  → Élargissez les plages de recherche ou relâchez les contraintes.")
        return None

    # Trier par coût croissant
    solutions_grossieres.sort(key=lambda x: x['cout'])

    # Afficher les 5 meilleures solutions de la recherche grossière
    print(f"\n{'='*80}")
    print(f" TOP 5 - RECHERCHE GROSSIÈRE")
    print(f"{'='*80}")
    print(f"{'Rang':<6} {'R (mm)':<10} {'a (mm)':<10} {'N':<6} {'Tmax (°C)':<12} {'Coût ($)':<12}")
    print(f"{'-'*80}")
    for i, sol in enumerate(solutions_grossieres[:5]):
        print(f"{i+1:<6} {sol['R']*1000:<10.1f} {sol['a']*1000:<10.1f} "
              f"{sol['N']:<6} {sol['Tmax']:<12.2f} {sol['cout']:<12.2f}")

    meilleure_grossiere = solutions_grossieres[0]

    # Si méthode rapide, retourner le meilleur de la recherche grossière
    if methode == 'rapide':
        return meilleure_grossiere

    # -------------------------------------------------------------------------
    # PHASE 2: RECHERCHE FINE
    # -------------------------------------------------------------------------

    # Recherche fine autour des 3 meilleures solutions
    nb_raffinements = min(3, len(solutions_grossieres))
    toutes_solutions_fines = []

    for i in range(nb_raffinements):
        sol = solutions_grossieres[i]

        print(f"\n{'='*80}")
        print(f" RAFFINEMENT #{i+1} autour de la solution #{i+1}")
        print(f"{'='*80}")

        solutions_fines = recherche_fine(
            R_centre=sol['R'],
            a_centre=sol['a'],
            N_centre=sol['N'],
            delta_R=0.003,      # ±3 mm
            delta_a=0.007,      # ±7 mm
            delta_N=15,         # ±15 ailettes
            pas_R=0.001,        # Pas de 1 mm (précision demandée)
            pas_a=0.001,        # Pas de 1 mm (précision demandée)
            pas_N=5,            # Pas de 5 ailettes (précision demandée)
            verbose=True
        )

        toutes_solutions_fines.extend(solutions_fines)

    # Trier toutes les solutions fines par coût
    if len(toutes_solutions_fines) > 0:
        toutes_solutions_fines.sort(key=lambda x: x['cout'])
        meilleure_fine = toutes_solutions_fines[0]
    else:
        print("\n⚠ Aucune solution fine trouvée, on garde la meilleure grossière")
        meilleure_fine = meilleure_grossiere

    # -------------------------------------------------------------------------
    # AFFICHAGE DES RÉSULTATS FINAUX
    # -------------------------------------------------------------------------

    print(f"\n{'='*80}")
    print(f" SOLUTION OPTIMALE TROUVÉE")
    print(f"{'='*80}")
    print(f"\nVariables de conception:")
    print(f"  Rayon tube:          R = {meilleure_fine['R']*1000:.3f} mm")
    print(f"  Longueur ailettes:   a = {meilleure_fine['a']*1000:.3f} mm")
    print(f"  Nombre d'ailettes:   N = {meilleure_fine['N']}")
    print(f"\nPerformances:")
    print(f"  Température maximale: T_max = {meilleure_fine['Tmax']:.2f} °C")
    print(f"  Marge de sécurité:    ΔT = {T_max_contrainte - meilleure_fine['Tmax']:.2f} °C")
    print(f"  Coût total:           {meilleure_fine['cout']:.2f} $")

    # Décomposition du coût
    R_opt = meilleure_fine['R']
    a_opt = meilleure_fine['a']
    N_opt = meilleure_fine['N']

    cout_tube = 2e4 * L * R_opt**2
    cout_ailettes = 1000 * N_opt * a_opt * ((R_opt + a_opt)**2 - R_opt**2)
    cout_assemblage = 3 * np.sqrt(N_opt)

    print(f"\nDécomposition des coûts:")
    print(f"  Coût tube:        {cout_tube:.2f} $ ({cout_tube/meilleure_fine['cout']*100:.1f}%)")
    print(f"  Coût ailettes:    {cout_ailettes:.2f} $ ({cout_ailettes/meilleure_fine['cout']*100:.1f}%)")
    print(f"  Coût assemblage:  {cout_assemblage:.2f} $ ({cout_assemblage/meilleure_fine['cout']*100:.1f}%)")
    print(f"{'='*80}")

    return meilleure_fine


# ============================================================================
# FONCTION D'ANALYSE DE SENSIBILITÉ
# ============================================================================

def analyse_sensibilite(sol_optimale):
    """
    Analyse la sensibilité de la solution optimale.
    """
    print(f"\n{'='*80}")
    print(f" ANALYSE DE SENSIBILITÉ")
    print(f"{'='*80}")

    R_opt = sol_optimale['R']
    a_opt = sol_optimale['a']
    N_opt = sol_optimale['N']

    # Variation de ±10% autour de l'optimum
    variations = {
        'R': np.linspace(R_opt * 0.9, R_opt * 1.1, 5),
        'a': np.linspace(a_opt * 0.9, a_opt * 1.1, 5),
        'N': np.linspace(int(N_opt * 0.9), int(N_opt * 1.1), 5, dtype=int)
    }

    # Sensibilité par rapport à R (a et N fixes)
    print(f"\nSensibilité par rapport à R (a={a_opt*1000:.1f}mm, N={N_opt}):")
    print(f"{'R (mm)':<10} {'Tmax (°C)':<12} {'Coût ($)':<12} {'Valide?':<10}")
    print(f"{'-'*50}")
    for R in variations['R']:
        result = solve_heating_baseboard(
            L, P, h_conv, T_air, k_c, R, a_opt, N_opt,
            nr_tube=nr_tube, nr_ailette=nr_ailette,
            nz_ailette=nz_ailette, nz_espace=nz_espace,
            verbose=False, plot_results=False
        )
        valide = "✓" if result['Tmax'] <= T_max_contrainte else "✗"
        print(f"{R*1000:<10.1f} {result['Tmax']:<12.2f} {result['cout_total']:<12.2f} {valide:<10}")

    # Sensibilité par rapport à a (R et N fixes)
    print(f"\nSensibilité par rapport à a (R={R_opt*1000:.1f}mm, N={N_opt}):")
    print(f"{'a (mm)':<10} {'Tmax (°C)':<12} {'Coût ($)':<12} {'Valide?':<10}")
    print(f"{'-'*50}")
    for a in variations['a']:
        result = solve_heating_baseboard(
            L, P, h_conv, T_air, k_c, R_opt, a, N_opt,
            nr_tube=nr_tube, nr_ailette=nr_ailette,
            nz_ailette=nz_ailette, nz_espace=nz_espace,
            verbose=False, plot_results=False
        )
        valide = "✓" if result['Tmax'] <= T_max_contrainte else "✗"
        print(f"{a*1000:<10.1f} {result['Tmax']:<12.2f} {result['cout_total']:<12.2f} {valide:<10}")

    # Sensibilité par rapport à N (R et a fixes)
    print(f"\nSensibilité par rapport à N (R={R_opt*1000:.1f}mm, a={a_opt*1000:.1f}mm):")
    print(f"{'N':<10} {'Tmax (°C)':<12} {'Coût ($)':<12} {'Valide?':<10}")
    print(f"{'-'*50}")
    for N in variations['N']:
        result = solve_heating_baseboard(
            L, P, h_conv, T_air, k_c, R_opt, a_opt, N,
            nr_tube=nr_tube, nr_ailette=nr_ailette,
            nz_ailette=nz_ailette, nz_espace=nz_espace,
            verbose=False, plot_results=False
        )
        valide = "✓" if result['Tmax'] <= T_max_contrainte else "✗"
        print(f"{N:<10} {result['Tmax']:<12.2f} {result['cout_total']:<12.2f} {valide:<10}")


# ============================================================================
# FONCTION DE VISUALISATION
# ============================================================================

def visualiser_solution_optimale(sol_optimale):
    """
    Visualise la solution optimale avec distribution de température.
    """
    print(f"\n{'='*80}")
    print(f" VISUALISATION DE LA SOLUTION OPTIMALE")
    print(f"{'='*80}")

    R_opt = sol_optimale['R']
    a_opt = sol_optimale['a']
    N_opt = sol_optimale['N']

    # Résoudre avec maillage plus fin pour meilleure visualisation
    result = solve_heating_baseboard(
        L, P, h_conv, T_air, k_c, R_opt, a_opt, N_opt,
        nr_tube=8, nr_ailette=12, nz_ailette=5, nz_espace=15,
        verbose=True, plot_results=True
    )

    return result


# ============================================================================
# EXÉCUTION PRINCIPALE
# ============================================================================

if __name__ == "__main__":

    # Choisir la méthode d'optimisation
    # 'complete' = recherche en 2 phases (recommandé)
    # 'rapide' = recherche grossière uniquement
    methode = 'complete'

    # Lancer l'optimisation
    print("\nDémarrage de l'optimisation...")
    sol_optimale = optimiser_plinthe(methode=methode)

    if sol_optimale is not None:
        # Analyse de sensibilité
        analyse_sensibilite(sol_optimale)

        # Visualisation (demander seulement si en mode interactif)
        try:
            reponse = input("\nSouhaitez-vous visualiser la solution optimale? (o/n): ")
            if reponse.lower() == 'o':
                visualiser_solution_optimale(sol_optimale)
        except EOFError:
            # Mode non-interactif, passer la visualisation
            print("\nMode non-interactif détecté, visualisation ignorée.")

        print("\n✓ Optimisation terminée avec succès!")
    else:
        print("\n✗ Optimisation échouée - aucune solution trouvée.")
