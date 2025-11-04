#!/usr/bin/env python3
"""
Test rapide de l'optimisation avec 3 solutions
Utilise une plage réduite pour tester rapidement
"""

import numpy as np
from mec423_heating_baseboard import solve_heating_baseboard
import time

# Paramètres du projet
L = 3.0
P = 3600
h_conv = 30
T_air = 60
k_c = 150

# Plage de température cible
T_target_min = 248
T_target_max = 250
T_target_center = 249

# Paramètres de maillage
nr_tube = 5
nr_ailette = 8
nz_ailette = 3
nz_espace = 10

print("="*80)
print(" TEST RAPIDE - 3 SOLUTIONS OPTIMALES")
print("="*80)
print(f"\nPlage de température cible: {T_target_min}-{T_target_max}°C")

# Plage réduite pour test rapide
R_vals = np.linspace(0.010, 0.015, 4)    # 10 à 15 mm, 4 points
a_vals = np.linspace(0.040, 0.055, 4)    # 40 à 55 mm, 4 points
N_vals = np.arange(50, 91, 10)           # 50 à 90, pas de 10

# Initialiser les 3 meilleures solutions
best_temp = None
best_cost = None
best_fins = None

min_temp_deviation = float('inf')
min_cost = float('inf')
min_N = float('inf')

total = len(R_vals) * len(a_vals) * len(N_vals)
count = 0
start = time.time()

print(f"\nTests: {total} configurations")
print(f"  R: {len(R_vals)} valeurs")
print(f"  a: {len(a_vals)} valeurs")
print(f"  N: {len(N_vals)} valeurs")
print("\nRecherche en cours...\n")

for R in R_vals:
    for a in a_vals:
        for N in N_vals:
            count += 1

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

                # Solution 1: Température la plus proche
                if temp_deviation < min_temp_deviation:
                    min_temp_deviation = temp_deviation
                    best_temp = {'R': R, 'a': a, 'N': N, 'Tmax': Tmax, 'cout': cout, 'dev': temp_deviation}
                    print(f"  [Précision] R={R*1000:.1f}mm, a={a*1000:.1f}mm, N={N}, Tmax={Tmax:.2f}°C (dév={temp_deviation:.2f}°C)")

                # Solutions 2 et 3: dans la plage cible
                if T_target_min <= Tmax <= T_target_max:
                    # Solution 2: Coût minimal
                    if cout < min_cost:
                        min_cost = cout
                        best_cost = {'R': R, 'a': a, 'N': N, 'Tmax': Tmax, 'cout': cout, 'dev': temp_deviation}
                        print(f"  [Coût Min] R={R*1000:.1f}mm, a={a*1000:.1f}mm, N={N}, Tmax={Tmax:.2f}°C, Coût={cout:.2f}$")

                    # Solution 3: N minimal
                    if N < min_N:
                        min_N = N
                        best_fins = {'R': R, 'a': a, 'N': N, 'Tmax': Tmax, 'cout': cout, 'dev': temp_deviation}
                        print(f"  [N Min] R={R*1000:.1f}mm, a={a*1000:.1f}mm, N={N}, Tmax={Tmax:.2f}°C")

elapsed = time.time() - start

# Affichage des résultats
print(f"\n{'='*80}")
print(f" RÉSULTATS - Temps: {elapsed:.1f}s")
print(f"{'='*80}")

if best_temp:
    print(f"\n📌 SOLUTION 1: PRÉCISION TEMPÉRATURE")
    print(f"   R = {best_temp['R']*1000:.3f} mm, a = {best_temp['a']*1000:.3f} mm, N = {best_temp['N']}")
    print(f"   Tmax = {best_temp['Tmax']:.2f}°C ⭐ (déviation = {best_temp['dev']:.2f}°C)")
    print(f"   Coût = {best_temp['cout']:.2f}$")

if best_cost:
    print(f"\n💰 SOLUTION 2: COÛT MINIMAL")
    print(f"   R = {best_cost['R']*1000:.3f} mm, a = {best_cost['a']*1000:.3f} mm, N = {best_cost['N']}")
    print(f"   Tmax = {best_cost['Tmax']:.2f}°C")
    print(f"   Coût = {best_cost['cout']:.2f}$ ⭐")

if best_fins:
    print(f"\n🔧 SOLUTION 3: N MINIMAL")
    print(f"   R = {best_fins['R']*1000:.3f} mm, a = {best_fins['a']*1000:.3f} mm, N = {best_fins['N']} ⭐")
    print(f"   Tmax = {best_fins['Tmax']:.2f}°C")
    print(f"   Coût = {best_fins['cout']:.2f}$")

print(f"\n{'='*80}")
print("✓ Test terminé!")
print(f"{'='*80}")
