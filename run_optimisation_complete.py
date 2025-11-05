#!/usr/bin/env python3
"""
OPTIMISATION COMPLÈTE - 3 SOLUTIONS OPTIMALES
Basé sur optimisation_plinthe.py qui fonctionne bien
"""

import numpy as np
from mec423_heating_baseboard import solve_heating_baseboard
import time

# ============================================================================
# PARAMÈTRES
# ============================================================================

L = 3.0
P = 3600
h_conv = 30
T_air = 60
k_c = 150

T_target_min = 248
T_target_max = 250
T_target_center = 249

# Maillage pour optimisation (rapide)
nr_tube = 5
nr_ailette = 8
nz_ailette = 3
nz_espace = 10

# ============================================================================
# PHASE 1: RECHERCHE GROSSIÈRE
# ============================================================================

print("="*80)
print(" OPTIMISATION COMPLÈTE - 3 SOLUTIONS OPTIMALES")
print("="*80)
print(f"\nObjectifs:")
print(f"  1. Température MAX la plus élevée avec {T_target_min}°C ≤ Tmax ≤ {T_target_max}°C")
print(f"  2. Coût minimal avec {T_target_min}°C ≤ Tmax ≤ {T_target_max}°C")
print(f"  3. Nombre d'ailettes minimal avec {T_target_min}°C ≤ Tmax ≤ {T_target_max}°C")
print("="*80)

print(f"\n{'='*80}")
print(f" PHASE 1: RECHERCHE GROSSIÈRE")
print(f"{'='*80}")

# Plages grossières
R_vals = np.arange(0.008, 0.021, 0.002)    # 8 à 20 mm, pas de 2mm
a_vals = np.arange(0.030, 0.061, 0.005)    # 30 à 60 mm, pas de 5mm
N_vals = np.arange(30, 121, 10)            # 30 à 120, pas de 10

print(f"Plages de recherche:")
print(f"  R: {R_vals[0]*1000:.1f} à {R_vals[-1]*1000:.1f} mm ({len(R_vals)} valeurs)")
print(f"  a: {a_vals[0]*1000:.1f} à {a_vals[-1]*1000:.1f} mm ({len(a_vals)} valeurs)")
print(f"  N: {N_vals[0]} à {N_vals[-1]} ({len(N_vals)} valeurs)")

total = len(R_vals) * len(a_vals) * len(N_vals)
print(f"\nTotal de configurations à tester: {total}")

# Initialiser les 3 meilleures
best_temp = None
best_cost = None
best_fins = None

max_tmax = 0  # Pour chercher la température MAX la plus élevée
min_cost = float('inf')
min_N = float('inf')

start_time = time.time()
count = 0
count_valide = 0

print(f"\nRecherche en cours...")

for R in R_vals:
    for a in a_vals:
        for N in N_vals:
            count += 1

            # Afficher la progression tous les 100 tests
            if count % 100 == 0:
                print(f"  Progression: {count}/{total} ({count/total*100:.1f}%) - Solutions dans plage: {count_valide}")

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

                # Toutes les solutions doivent être dans la plage cible
                if T_target_min <= Tmax <= T_target_max:
                    count_valide += 1

                    # Solution 1: Température MAX la plus élevée
                    if Tmax > max_tmax:
                        max_tmax = Tmax
                        best_temp = {
                            'R': R, 'a': a, 'N': N,
                            'Tmax': Tmax, 'cout': cout,
                            'temp_deviation': temp_deviation
                        }

                    # Solution 2: Coût minimal
                    if cout < min_cost:
                        min_cost = cout
                        best_cost = {
                            'R': R, 'a': a, 'N': N,
                            'Tmax': Tmax, 'cout': cout,
                            'temp_deviation': temp_deviation
                        }

                    # Solution 3: N minimal
                    if N < min_N:
                        min_N = N
                        best_fins = {
                            'R': R, 'a': a, 'N': N,
                            'Tmax': Tmax, 'cout': cout,
                            'temp_deviation': temp_deviation
                        }

elapsed = time.time() - start_time
print(f"\nPhase 1 terminée en {elapsed:.1f} secondes")
print(f"Solutions dans la plage {T_target_min}-{T_target_max}°C: {count_valide}/{count}")

# Afficher résultats Phase 1
def afficher_solution(sol, nom, critere):
    if sol:
        print(f"\n{nom}")
        print(f"  R = {sol['R']*1000:.3f} mm, a = {sol['a']*1000:.3f} mm, N = {sol['N']}")
        print(f"  Tmax = {sol['Tmax']:.2f}°C, Coût = {sol['cout']:.2f}$ {critere}")
    else:
        print(f"\n{nom}: ⚠️ Non trouvée")

print(f"\n{'='*80}")
print(f" RÉSULTATS PHASE 1")
print(f"{'='*80}")

afficher_solution(best_temp, "📌 SOLUTION 1: Température MAX la plus élevée",
                 f"⭐ (Tmax = {best_temp['Tmax']:.2f}°C)" if best_temp else "")
afficher_solution(best_cost, "💰 SOLUTION 2: Coût Minimal", "⭐" if best_cost else "")
afficher_solution(best_fins, "🔧 SOLUTION 3: N Minimal", "⭐" if best_fins else "")

# ============================================================================
# PHASE 2: RAFFINEMENT
# ============================================================================

if best_cost:  # Raffiner autour de la solution à coût minimal
    print(f"\n{'='*80}")
    print(f" PHASE 2: RAFFINEMENT AUTOUR DE LA SOLUTION À COÛT MINIMAL")
    print(f"{'='*80}")

    R_centre = best_cost['R']
    a_centre = best_cost['a']
    N_centre = best_cost['N']

    # Plages fines
    delta_R = 0.003  # ±3mm
    delta_a = 0.007  # ±7mm
    delta_N = 15

    R_vals_fine = np.arange(max(0.006, R_centre - delta_R),
                           min(0.022, R_centre + delta_R) + 0.0005,
                           0.001)
    a_vals_fine = np.arange(max(0.020, a_centre - delta_a),
                           min(0.065, a_centre + delta_a) + 0.0005,
                           0.001)
    N_vals_fine = np.arange(max(20, N_centre - delta_N),
                           min(130, N_centre + delta_N) + 1,
                           5)

    print(f"Centre: R={R_centre*1000:.1f}mm, a={a_centre*1000:.1f}mm, N={N_centre}")
    print(f"Plages fines:")
    print(f"  R: {R_vals_fine[0]*1000:.1f} à {R_vals_fine[-1]*1000:.1f} mm ({len(R_vals_fine)} valeurs)")
    print(f"  a: {a_vals_fine[0]*1000:.1f} à {a_vals_fine[-1]*1000:.1f} mm ({len(a_vals_fine)} valeurs)")
    print(f"  N: {N_vals_fine[0]} à {N_vals_fine[-1]} ({len(N_vals_fine)} valeurs)")

    total_fine = len(R_vals_fine) * len(a_vals_fine) * len(N_vals_fine)
    print(f"\nTotal raffinement: {total_fine} configurations")

    start_time = time.time()
    count = 0

    for R in R_vals_fine:
        for a in a_vals_fine:
            for N in N_vals_fine:
                count += 1

                if count % 100 == 0:
                    print(f"  Progression: {count}/{total_fine} ({count/total_fine*100:.1f}%)")

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

                    # Toutes les solutions doivent être dans la plage cible
                    if T_target_min <= Tmax <= T_target_max:
                        # Solution 1: Température MAX la plus élevée
                        if Tmax > max_tmax:
                            max_tmax = Tmax
                            best_temp = {
                                'R': R, 'a': a, 'N': N,
                                'Tmax': Tmax, 'cout': cout,
                                'temp_deviation': temp_deviation
                            }

                        # Solution 2: Coût minimal
                        if cout < min_cost:
                            min_cost = cout
                            best_cost = {
                                'R': R, 'a': a, 'N': N,
                                'Tmax': Tmax, 'cout': cout,
                                'temp_deviation': temp_deviation
                            }

                        # Solution 3: N minimal
                        if N < min_N:
                            min_N = N
                            best_fins = {
                                'R': R, 'a': a, 'N': N,
                                'Tmax': Tmax, 'cout': cout,
                                'temp_deviation': temp_deviation
                            }

    elapsed = time.time() - start_time
    print(f"\nPhase 2 terminée en {elapsed:.1f} secondes")

# ============================================================================
# RÉSULTATS FINAUX
# ============================================================================

print(f"\n{'='*80}")
print(f" 🏆 RÉSULTATS FINAUX - 3 SOLUTIONS OPTIMALES")
print(f"{'='*80}")

afficher_solution(best_temp, "📌 SOLUTION 1: Température MAX la plus élevée",
                 f"⭐ (Tmax = {best_temp['Tmax']:.2f}°C)" if best_temp else "")
afficher_solution(best_cost, "💰 SOLUTION 2: Coût Minimal", "⭐" if best_cost else "")
afficher_solution(best_fins, "🔧 SOLUTION 3: N Minimal", "⭐" if best_fins else "")

# Tableau récapitulatif
if best_temp or best_cost or best_fins:
    print(f"\n{'='*80}")
    print(f" TABLEAU RÉCAPITULATIF")
    print(f"{'='*80}")
    print(f"\n{'':<25} {'R (mm)':<10} {'a (mm)':<10} {'N':<6} {'Tmax (°C)':<12} {'Coût ($)':<12}")
    print(f"{'-'*80}")

    if best_temp:
        sol = best_temp
        print(f"{'1. Tmax Élevée ⭐':<25} {sol['R']*1000:<10.3f} {sol['a']*1000:<10.3f} "
              f"{sol['N']:<6} {sol['Tmax']:<12.2f} {sol['cout']:<12.2f}")

    if best_cost:
        sol = best_cost
        print(f"{'2. Coût Minimal 💰':<25} {sol['R']*1000:<10.3f} {sol['a']*1000:<10.3f} "
              f"{sol['N']:<6} {sol['Tmax']:<12.2f} {sol['cout']:<12.2f}")

    if best_fins:
        sol = best_fins
        print(f"{'3. N Minimal 🔧':<25} {sol['R']*1000:<10.3f} {sol['a']*1000:<10.3f} "
              f"{sol['N']:<6} {sol['Tmax']:<12.2f} {sol['cout']:<12.2f}")

print(f"\n{'='*80}")
print("✓ Optimisation terminée!")
print(f"{'='*80}")
