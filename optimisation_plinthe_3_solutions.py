"""
============================================================================
PROJET MEC423 - OPTIMISATION DE LA PLINTHE CHAUFFANTE ÉLECTRIQUE
============================================================================

Objectif: Trouver 3 solutions optimales pour:
  1. Température max la plus proche de 248-250°C (précision)
  2. Coût minimal avec 248°C ≤ Tmax ≤ 250°C
  3. Nombre d'ailettes minimal avec 248°C ≤ Tmax ≤ 250°C

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

# Plage de température cible
T_target_min = 248  # [°C]
T_target_max = 250  # [°C]
T_target_center = (T_target_min + T_target_max) / 2  # 249°C

# Paramètres de maillage (pour rapidité d'optimisation)
nr_tube = 5
nr_ailette = 8
nz_ailette = 3
nz_espace = 10

print("="*80)
print(" OPTIMISATION PLINTHE CHAUFFANTE - 3 SOLUTIONS OPTIMALES")
print("="*80)
print(f"\nDonnées du projet:")
print(f"  Longueur tube L = {L} m")
print(f"  Puissance P = {P/1000} kW")
print(f"  Convection h = {h_conv} W/(m²·°C)")
print(f"  Température air T_air = {T_air} °C")
print(f"\nCritère de température: {T_target_min} ≤ T_max ≤ {T_target_max} °C")
print(f"\nObjectifs:")
print(f"  1. Température max la plus proche de la cible")
print(f"  2. Coût minimal dans la plage cible")
print(f"  3. Nombre d'ailettes minimal dans la plage cible")
print("="*80)

# ============================================================================
# PLAGES DE RECHERCHE
# ============================================================================

# Plages de recherche (inspirées des valeurs typiques)
R_min, R_max = 0.008, 0.020    # Rayon tube: 8 à 20 mm
a_min, a_max = 0.020, 0.060    # Longueur ailettes: 20 à 60 mm
N_min, N_max = 20, 120         # Nombre d'ailettes: 20 à 120

# ============================================================================
# PHASE 1: RECHERCHE GROSSIÈRE (Balayage large)
# ============================================================================

def recherche_grossiere(R_vals, a_vals, N_vals, verbose=True):
    """
    Balayage grossier pour identifier toutes les solutions.
    Cherche les 3 solutions optimales simultanément.

    Args:
        R_vals: Liste des valeurs de R à tester
        a_vals: Liste des valeurs de a à tester
        N_vals: Liste des valeurs de N à tester
        verbose: Afficher les détails

    Returns:
        Tuple: (toutes_solutions, best_temp, best_cost, best_fins)
    """
    toutes_solutions = []
    total_tests = len(R_vals) * len(a_vals) * len(N_vals)
    test_count = 0

    # Initialiser les 3 meilleures solutions
    best_temp = None      # Température la plus proche de la cible
    best_cost = None      # Coût minimal dans la plage
    best_fins = None      # N minimal dans la plage

    min_temp_deviation = float('inf')
    min_cost = float('inf')
    min_N = float('inf')

    if verbose:
        print(f"\n{'='*80}")
        print(f" RECHERCHE DES 3 SOLUTIONS OPTIMALES")
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

                # Vérifier si la solution converge
                if result['success']:
                    Tmax = result['Tmax']
                    cout = result['cout_total']
                    temp_deviation = abs(Tmax - T_target_center)

                    # Enregistrer toutes les solutions
                    toutes_solutions.append({
                        'R': R,
                        'a': a,
                        'N': N,
                        'Tmax': Tmax,
                        'cout': cout,
                        'temp_deviation': temp_deviation
                    })

                    # Solution 1: Température la plus proche de la cible
                    if temp_deviation < min_temp_deviation:
                        min_temp_deviation = temp_deviation
                        best_temp = {
                            'R': R, 'a': a, 'N': N,
                            'Tmax': Tmax, 'cout': cout,
                            'temp_deviation': temp_deviation
                        }
                        if verbose:
                            print(f"  [Précision] Nouvelle meilleure: R={R*1000:.1f}mm, a={a*1000:.1f}mm, N={N}, Tmax={Tmax:.2f}°C (dév={temp_deviation:.2f}°C)")

                    # Solutions 2 et 3: Seulement si dans la plage cible
                    if T_target_min <= Tmax <= T_target_max:
                        # Solution 2: Coût minimal
                        if cout < min_cost:
                            min_cost = cout
                            best_cost = {
                                'R': R, 'a': a, 'N': N,
                                'Tmax': Tmax, 'cout': cout,
                                'temp_deviation': temp_deviation
                            }
                            if verbose:
                                print(f"  [Coût Min] Nouvelle meilleure: R={R*1000:.1f}mm, a={a*1000:.1f}mm, N={N}, Tmax={Tmax:.2f}°C, Coût={cout:.2f}$")

                        # Solution 3: N minimal
                        if N < min_N:
                            min_N = N
                            best_fins = {
                                'R': R, 'a': a, 'N': N,
                                'Tmax': Tmax, 'cout': cout,
                                'temp_deviation': temp_deviation
                            }
                            if verbose:
                                print(f"  [N Min] Nouvelle meilleure: R={R*1000:.1f}mm, a={a*1000:.1f}mm, N={N}, Tmax={Tmax:.2f}°C")

    if verbose:
        elapsed = time.time() - start_time
        print(f"\nRecherche terminée en {elapsed:.1f} secondes")
        print(f"Solutions testées: {len(toutes_solutions)}/{total_tests}")

    return toutes_solutions, best_temp, best_cost, best_fins


# ============================================================================
# PHASE 2: RECHERCHE FINE (Raffinement)
# ============================================================================

def recherche_fine_3_solutions(best_temp, best_cost, best_fins,
                               delta_R, delta_a, delta_N,
                               pas_R, pas_a, pas_N, verbose=True):
    """
    Recherche fine autour des 3 meilleures solutions.

    Returns:
        Tuple: (toutes_solutions, best_temp_fine, best_cost_fine, best_fins_fine)
    """
    toutes_solutions_fines = []
    best_temp_fine = best_temp
    best_cost_fine = best_cost
    best_fins_fine = best_fins

    min_temp_deviation = best_temp['temp_deviation'] if best_temp else float('inf')
    min_cost = best_cost['cout'] if best_cost else float('inf')
    min_N = best_fins['N'] if best_fins else float('inf')

    # Raffiner autour des 3 solutions (si elles existent et sont différentes)
    solutions_a_raffiner = []

    if best_temp:
        solutions_a_raffiner.append(('Précision Temp', best_temp))
    if best_cost and (not best_temp or best_cost['R'] != best_temp['R'] or best_cost['a'] != best_temp['a']):
        solutions_a_raffiner.append(('Coût Min', best_cost))
    if best_fins and (not best_cost or best_fins['R'] != best_cost['R'] or best_fins['a'] != best_cost['a']):
        solutions_a_raffiner.append(('N Min', best_fins))

    for nom, sol in solutions_a_raffiner:
        print(f"\n{'='*80}")
        print(f" RAFFINEMENT: {nom}")
        print(f"{'='*80}")
        print(f"Centre: R={sol['R']*1000:.3f}mm, a={sol['a']*1000:.3f}mm, N={sol['N']}")

        # Générer les plages de recherche fine
        R_vals = np.arange(max(R_min, sol['R'] - delta_R),
                           min(R_max, sol['R'] + delta_R) + pas_R/2,
                           pas_R)
        a_vals = np.arange(max(a_min, sol['a'] - delta_a),
                           min(a_max, sol['a'] + delta_a) + pas_a/2,
                           pas_a)
        N_vals = np.arange(max(N_min, sol['N'] - delta_N),
                           min(N_max, sol['N'] + delta_N) + pas_N,
                           pas_N, dtype=int)

        print(f"Plages: R=[{R_vals[0]*1000:.1f}, {R_vals[-1]*1000:.1f}]mm, "
              f"a=[{a_vals[0]*1000:.1f}, {a_vals[-1]*1000:.1f}]mm, "
              f"N=[{N_vals[0]}, {N_vals[-1]}]")

        # Rechercher
        for R in R_vals:
            for a in a_vals:
                for N in N_vals:
                    result = solve_heating_baseboard(
                        L, P, h_conv, T_air, k_c, R, a, N,
                        nr_tube=nr_tube, nr_ailette=nr_ailette,
                        nz_ailette=nz_ailette, nz_espace=nz_espace,
                        verbose=False, plot_results=False
                    )

                    if result['success']:
                        Tmax = result['Tmax']
                        cout = result['cout_total']
                        temp_deviation = abs(Tmax - T_target_center)

                        toutes_solutions_fines.append({
                            'R': R, 'a': a, 'N': N,
                            'Tmax': Tmax, 'cout': cout,
                            'temp_deviation': temp_deviation
                        })

                        # Mettre à jour les meilleures solutions
                        if temp_deviation < min_temp_deviation:
                            min_temp_deviation = temp_deviation
                            best_temp_fine = {
                                'R': R, 'a': a, 'N': N,
                                'Tmax': Tmax, 'cout': cout,
                                'temp_deviation': temp_deviation
                            }

                        if T_target_min <= Tmax <= T_target_max:
                            if cout < min_cost:
                                min_cost = cout
                                best_cost_fine = {
                                    'R': R, 'a': a, 'N': N,
                                    'Tmax': Tmax, 'cout': cout,
                                    'temp_deviation': temp_deviation
                                }

                            if N < min_N:
                                min_N = N
                                best_fins_fine = {
                                    'R': R, 'a': a, 'N': N,
                                    'Tmax': Tmax, 'cout': cout,
                                    'temp_deviation': temp_deviation
                                }

        print(f"Solutions trouvées dans ce raffinement: {len(toutes_solutions_fines)}")

    return toutes_solutions_fines, best_temp_fine, best_cost_fine, best_fins_fine


# ============================================================================
# FONCTION PRINCIPALE D'OPTIMISATION
# ============================================================================

def optimiser_plinthe_3_solutions(methode='complete'):
    """
    Optimise la conception de la plinthe chauffante.
    Trouve 3 solutions optimales différentes.

    Args:
        methode: 'complete' (recherche en 2 phases) ou 'rapide' (phase 1 uniquement)

    Returns:
        dict: {'temp': best_temp, 'cost': best_cost, 'fins': best_fins}
    """

    # -------------------------------------------------------------------------
    # PHASE 1: RECHERCHE GROSSIÈRE
    # -------------------------------------------------------------------------

    # Définir les plages de recherche grossière
    R_vals_grossier = np.arange(R_min, R_max + 0.001, 0.002)  # Pas de 2 mm
    a_vals_grossier = np.arange(a_min, a_max + 0.001, 0.005)  # Pas de 5 mm
    N_vals_grossier = np.arange(N_min, N_max + 1, 10, dtype=int)  # Pas de 10

    # Effectuer la recherche
    toutes_sol, best_temp, best_cost, best_fins = recherche_grossiere(
        R_vals_grossier, a_vals_grossier, N_vals_grossier, verbose=True
    )

    if len(toutes_sol) == 0:
        print("\n⚠ AUCUNE SOLUTION trouvée!")
        return None

    # Affichage intermédiaire
    afficher_3_solutions(best_temp, best_cost, best_fins, "PHASE 1")

    # Si méthode rapide, retourner
    if methode == 'rapide':
        return {'temp': best_temp, 'cost': best_cost, 'fins': best_fins}

    # -------------------------------------------------------------------------
    # PHASE 2: RECHERCHE FINE
    # -------------------------------------------------------------------------

    print(f"\n{'='*80}")
    print(f" PHASE 2: RAFFINEMENT DES 3 SOLUTIONS")
    print(f"{'='*80}")

    toutes_sol_fines, best_temp_fine, best_cost_fine, best_fins_fine = \
        recherche_fine_3_solutions(
            best_temp, best_cost, best_fins,
            delta_R=0.003,      # ±3 mm
            delta_a=0.007,      # ±7 mm
            delta_N=15,         # ±15 ailettes
            pas_R=0.001,        # Pas de 1 mm
            pas_a=0.001,        # Pas de 1 mm
            pas_N=5,            # Pas de 5
            verbose=True
        )

    # Affichage final
    afficher_3_solutions(best_temp_fine, best_cost_fine, best_fins_fine, "FINALE")

    return {'temp': best_temp_fine, 'cost': best_cost_fine, 'fins': best_fins_fine}


# ============================================================================
# FONCTION D'AFFICHAGE DES 3 SOLUTIONS
# ============================================================================

def afficher_3_solutions(best_temp, best_cost, best_fins, phase_name):
    """
    Affiche les 3 solutions optimales de manière claire.
    """
    print(f"\n{'='*80}")
    print(f" 🏆 3 SOLUTIONS OPTIMALES - {phase_name}")
    print(f"{'='*80}")

    # Solution 1: Précision température
    if best_temp:
        print(f"\n{'─'*80}")
        print(f"📌 SOLUTION 1: TEMPÉRATURE LA PLUS PROCHE DE {T_target_min}-{T_target_max}°C")
        print(f"{'─'*80}")
        print(f"  Rayon tube:          R = {best_temp['R']*1000:.3f} mm")
        print(f"  Longueur ailettes:   a = {best_temp['a']*1000:.3f} mm")
        print(f"  Nombre d'ailettes:   N = {best_temp['N']}")
        print(f"  Température max:     T_max = {best_temp['Tmax']:.2f} °C  ⭐ (déviation = {best_temp['temp_deviation']:.2f}°C)")
        print(f"  Coût total:          {best_temp['cout']:.2f} $")
    else:
        print(f"\n⚠️  Solution 1 non trouvée")

    # Solution 2: Coût minimal
    if best_cost:
        print(f"\n{'─'*80}")
        print(f"💰 SOLUTION 2: COÛT MINIMAL (avec {T_target_min}°C ≤ Tmax ≤ {T_target_max}°C)")
        print(f"{'─'*80}")
        print(f"  Rayon tube:          R = {best_cost['R']*1000:.3f} mm")
        print(f"  Longueur ailettes:   a = {best_cost['a']*1000:.3f} mm")
        print(f"  Nombre d'ailettes:   N = {best_cost['N']}")
        print(f"  Température max:     T_max = {best_cost['Tmax']:.2f} °C")
        print(f"  Coût total:          {best_cost['cout']:.2f} $  ⭐ (COÛT MINIMAL)")
    else:
        print(f"\n⚠️  Solution 2 non trouvée (aucune config dans la plage {T_target_min}-{T_target_max}°C)")

    # Solution 3: N minimal
    if best_fins:
        print(f"\n{'─'*80}")
        print(f"🔧 SOLUTION 3: NOMBRE D'AILETTES MINIMAL (avec {T_target_min}°C ≤ Tmax ≤ {T_target_max}°C)")
        print(f"{'─'*80}")
        print(f"  Rayon tube:          R = {best_fins['R']*1000:.3f} mm")
        print(f"  Longueur ailettes:   a = {best_fins['a']*1000:.3f} mm")
        print(f"  Nombre d'ailettes:   N = {best_fins['N']}  ⭐ (N MINIMAL)")
        print(f"  Température max:     T_max = {best_fins['Tmax']:.2f} °C")
        print(f"  Coût total:          {best_fins['cout']:.2f} $")
    else:
        print(f"\n⚠️  Solution 3 non trouvée (aucune config dans la plage {T_target_min}-{T_target_max}°C)")

    print(f"\n{'='*80}")


# ============================================================================
# FONCTION DE VISUALISATION
# ============================================================================

def visualiser_solution(sol, nom):
    """
    Visualise une solution avec distribution de température.
    """
    print(f"\n{'='*80}")
    print(f" VISUALISATION: {nom}")
    print(f"{'='*80}")

    R = sol['R']
    a = sol['a']
    N = sol['N']

    # Résoudre avec maillage plus fin pour meilleure visualisation
    result = solve_heating_baseboard(
        L, P, h_conv, T_air, k_c, R, a, N,
        nr_tube=8, nr_ailette=12, nz_ailette=5, nz_espace=15,
        verbose=True, plot_results=True
    )

    return result


# ============================================================================
# EXÉCUTION PRINCIPALE
# ============================================================================

if __name__ == "__main__":

    # Choisir la méthode d'optimisation
    methode = 'complete'  # ou 'rapide'

    # Lancer l'optimisation
    print("\nDémarrage de l'optimisation...")
    solutions = optimiser_plinthe_3_solutions(methode=methode)

    if solutions is not None:
        # Tableau récapitulatif
        print(f"\n{'='*80}")
        print(f" 📊 TABLEAU RÉCAPITULATIF")
        print(f"{'='*80}")

        print(f"\n{'':<25} {'R (mm)':<10} {'a (mm)':<10} {'N':<6} {'Tmax (°C)':<12} {'Coût ($)':<12}")
        print(f"{'-'*80}")

        if solutions['temp']:
            sol = solutions['temp']
            print(f"{'1. Précision Temp ⭐':<25} {sol['R']*1000:<10.3f} {sol['a']*1000:<10.3f} "
                  f"{sol['N']:<6} {sol['Tmax']:<12.2f} {sol['cout']:<12.2f}")

        if solutions['cost']:
            sol = solutions['cost']
            print(f"{'2. Coût Minimal 💰':<25} {sol['R']*1000:<10.3f} {sol['a']*1000:<10.3f} "
                  f"{sol['N']:<6} {sol['Tmax']:<12.2f} {sol['cout']:<12.2f}")

        if solutions['fins']:
            sol = solutions['fins']
            print(f"{'3. N Minimal 🔧':<25} {sol['R']*1000:<10.3f} {sol['a']*1000:<10.3f} "
                  f"{sol['N']:<6} {sol['Tmax']:<12.2f} {sol['cout']:<12.2f}")

        print(f"{'='*80}")

        # Visualisation (en mode interactif)
        try:
            reponse = input("\nVisualiser les solutions? (1/2/3/n): ")
            if reponse == '1' and solutions['temp']:
                visualiser_solution(solutions['temp'], "Solution 1 - Précision Temp")
            elif reponse == '2' and solutions['cost']:
                visualiser_solution(solutions['cost'], "Solution 2 - Coût Minimal")
            elif reponse == '3' and solutions['fins']:
                visualiser_solution(solutions['fins'], "Solution 3 - N Minimal")
        except (EOFError, KeyboardInterrupt):
            print("\nMode non-interactif, visualisation ignorée.")

        print("\n✓ Optimisation terminée avec succès!")
    else:
        print("\n✗ Optimisation échouée - aucune solution trouvée.")
