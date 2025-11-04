#!/usr/bin/env python3
"""
Test rapide du programme d'optimisation avec 3 solutions
"""

import numpy as np
from mec423_optimization import optimize_design

# === PARAMÈTRES DU PROJET ===
L = 3.0      # [m]
P = 3600     # [W] (3.6 kW)
h_conv = 30  # [W/m²°C]
T_air = 60   # [°C]
k_c = 150    # [W/m°C]

# === TEST RAPIDE: Petite plage ===
print("="*80)
print(" TEST RAPIDE - 3 SOLUTIONS OPTIMALES")
print("="*80)

# Plage réduite pour test rapide
R_values = np.linspace(0.008, 0.010, 3)    # 8 à 10 mm, 3 points
a_values = np.linspace(0.030, 0.040, 3)    # 30 à 40 mm, 3 points

df_results, best_configs = optimize_design(
    L, P, h_conv, T_air, k_c,
    R_range=R_values,
    a_range=a_values,
    N_min=20,
    N_max=60,
    N_step=10,
    T_max_target_min=248,
    T_max_target_max=250
)

# Sauvegarder
if not df_results.empty:
    df_results.to_csv('test_3_solutions.csv', index=False)
    print("\n✅ Test terminé! Résultats sauvegardés dans test_3_solutions.csv")

    # Afficher un résumé
    print("\n" + "="*80)
    print(" RÉSUMÉ DES 3 SOLUTIONS")
    print("="*80)

    if best_configs['temp_match']:
        cfg = best_configs['temp_match']
        print(f"\n1. PRÉCISION TEMP: R={cfg['R']*1000:.1f}mm, a={cfg['a']*1000:.1f}mm, N={cfg['N']}, Tmax={cfg['Tmax']:.2f}°C")

    if best_configs['min_cost']:
        cfg = best_configs['min_cost']
        print(f"2. COÛT MINIMAL:   R={cfg['R']*1000:.1f}mm, a={cfg['a']*1000:.1f}mm, N={cfg['N']}, Coût={cfg['cout']:.2f}$")

    if best_configs['min_fins']:
        cfg = best_configs['min_fins']
        print(f"3. N MINIMAL:      R={cfg['R']*1000:.1f}mm, a={cfg['a']*1000:.1f}mm, N={cfg['N']}")

    print("\n" + "="*80)
else:
    print("\n⚠️ Aucun résultat trouvé")
