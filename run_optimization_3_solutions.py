#!/usr/bin/env python3
"""
OPTIMISATION COMPLÈTE DE LA PLINTHE CHAUFFANTE
Recherche 3 solutions optimales pour Tmax entre 248-250°C
"""

import numpy as np
from mec423_optimization import optimize_design, plot_optimization_results

# === PARAMÈTRES DU PROJET (MEC423-02, Équipe 10) ===
L = 3.0      # [m]
P = 3600     # [W] (3.6 kW)
h_conv = 30  # [W/m²°C]
T_air = 60   # [°C]
k_c = 150    # [W/m°C]

print("\n" + "="*80)
print(" OPTIMISATION PLINTHE CHAUFFANTE - RECHERCHE DES 3 SOLUTIONS OPTIMALES")
print("="*80)
print("\nObjectifs:")
print("  1. Température max la plus proche de 248-250°C")
print("  2. Coût minimal avec 248°C ≤ Tmax ≤ 250°C")
print("  3. Nombre d'ailettes minimal avec 248°C ≤ Tmax ≤ 250°C")
print("="*80)

# === PHASE 1: EXPLORATION LARGE ===
print("\n\n🔍 PHASE 1: EXPLORATION LARGE")
print("Stratégie: Balayage large pour identifier les zones prometteuses\n")

# Plage large mais raisonnable
R_values = np.linspace(0.008, 0.015, 8)    # 8 à 15 mm, 8 points
a_values = np.linspace(0.035, 0.060, 6)    # 35 à 60 mm, 6 points

df_results, best_configs = optimize_design(
    L, P, h_conv, T_air, k_c,
    R_range=R_values,
    a_range=a_values,
    N_min=30,
    N_max=120,
    N_step=10,
    T_max_target_min=248,
    T_max_target_max=250
)

# Sauvegarder les résultats de la Phase 1
if not df_results.empty:
    df_results.to_csv('optimisation_3_solutions_phase1.csv', index=False)
    print("\n📊 Résultats Phase 1 sauvegardés: optimisation_3_solutions_phase1.csv")

    # Afficher le top 10 par coût
    print("\n📋 TOP 10 DES CONFIGURATIONS (triées par coût):")
    print("-" * 80)
    top_10 = df_results.nsmallest(10, 'cout_$')
    print(top_10[['R_mm', 'a_mm', 'N', 'Tmax_C', 'cout_$', 'temp_deviation_C']].to_string(index=False))

    # Visualisation Phase 1
    print("\n📈 Génération des graphiques Phase 1...")
    plot_optimization_results(df_results)

# === PHASE 2: RAFFINEMENT ===
# On raffine autour de la meilleure solution (coût minimal dans la plage)
if best_configs and best_configs['min_cost']:
    print("\n\n🔬 PHASE 2: RAFFINEMENT AUTOUR DE LA SOLUTION À COÛT MINIMAL")
    print("Stratégie: Grille fine autour de l'optimum de la Phase 1\n")

    best_cost_config = best_configs['min_cost']
    R_opt = best_cost_config['R']
    a_opt = best_cost_config['a']
    N_opt = best_cost_config['N']

    # Raffiner avec une grille plus fine
    delta_R = 0.002  # ±2mm
    delta_a = 0.005  # ±5mm
    delta_N = 10

    R_values_fine = np.linspace(max(0.006, R_opt - delta_R), R_opt + delta_R, 9)
    a_values_fine = np.linspace(max(0.020, a_opt - delta_a), a_opt + delta_a, 9)

    df_results_fine, best_configs_fine = optimize_design(
        L, P, h_conv, T_air, k_c,
        R_range=R_values_fine,
        a_range=a_values_fine,
        N_min=max(20, N_opt - delta_N),
        N_max=N_opt + delta_N,
        N_step=2,
        T_max_target_min=248,
        T_max_target_max=250
    )

    if not df_results_fine.empty:
        df_results_fine.to_csv('optimisation_3_solutions_phase2.csv', index=False)
        print("\n📊 Résultats Phase 2 sauvegardés: optimisation_3_solutions_phase2.csv")

        # Afficher le top 10 raffiné
        print("\n📋 TOP 10 DES CONFIGURATIONS RAFFINÉES (triées par coût):")
        print("-" * 80)
        top_10_fine = df_results_fine.nsmallest(10, 'cout_$')
        print(top_10_fine[['R_mm', 'a_mm', 'N', 'Tmax_C', 'cout_$', 'temp_deviation_C']].to_string(index=False))

        # Visualisation Phase 2
        print("\n📈 Génération des graphiques Phase 2...")
        plot_optimization_results(df_results_fine)

        # Utiliser les meilleurs résultats de Phase 2
        best_configs = best_configs_fine

# === RÉSUMÉ FINAL ===
print("\n" + "="*80)
print(" 📊 RÉSUMÉ FINAL DES 3 SOLUTIONS OPTIMALES")
print("="*80)

if best_configs:
    # Tableau récapitulatif
    print("\n{:<25} {:>10} {:>10} {:>5} {:>10} {:>10} {:>12}".format(
        "Solution", "R (mm)", "a (mm)", "N", "Tmax (°C)", "Coût ($)", "Dév. (°C)"
    ))
    print("-" * 90)

    if best_configs['temp_match']:
        cfg = best_configs['temp_match']
        print("{:<25} {:>10.3f} {:>10.3f} {:>5} {:>10.2f} {:>10.2f} {:>12.2f}".format(
            "1. Précision Temp ⭐",
            cfg['R']*1000, cfg['a']*1000, cfg['N'],
            cfg['Tmax'], cfg['cout'], cfg['deviation']
        ))

    if best_configs['min_cost']:
        cfg = best_configs['min_cost']
        print("{:<25} {:>10.3f} {:>10.3f} {:>5} {:>10.2f} {:>10.2f} {:>12.2f}".format(
            "2. Coût Minimal 💰",
            cfg['R']*1000, cfg['a']*1000, cfg['N'],
            cfg['Tmax'], cfg['cout'], cfg['deviation']
        ))

    if best_configs['min_fins']:
        cfg = best_configs['min_fins']
        print("{:<25} {:>10.3f} {:>10.3f} {:>5} {:>10.2f} {:>10.2f} {:>12.2f}".format(
            "3. N Minimal 🔧",
            cfg['R']*1000, cfg['a']*1000, cfg['N'],
            cfg['Tmax'], cfg['cout'], cfg['deviation']
        ))

    print("="*90)

    # Comparer les 3 solutions
    print("\n💡 COMPARAISON DES SOLUTIONS:")
    print("-" * 80)

    if best_configs['temp_match'] and best_configs['min_cost']:
        temp_cfg = best_configs['temp_match']
        cost_cfg = best_configs['min_cost']

        print(f"\n• Solution 1 (Précision Temp) vs Solution 2 (Coût Min):")
        cost_diff = temp_cfg['cout'] - cost_cfg['cout']
        temp_diff = abs(temp_cfg['deviation']) - abs(cost_cfg['deviation'])
        print(f"  - Différence de coût: {cost_diff:+.2f}$ ({cost_diff/cost_cfg['cout']*100:+.1f}%)")
        print(f"  - Différence de précision: {temp_diff:+.2f}°C")

    if best_configs['min_cost'] and best_configs['min_fins']:
        cost_cfg = best_configs['min_cost']
        fins_cfg = best_configs['min_fins']

        print(f"\n• Solution 2 (Coût Min) vs Solution 3 (N Min):")
        cost_diff = fins_cfg['cout'] - cost_cfg['cout']
        N_diff = cost_cfg['N'] - fins_cfg['N']
        print(f"  - Différence de coût: {cost_diff:+.2f}$ ({cost_diff/cost_cfg['cout']*100:+.1f}%)")
        print(f"  - Différence d'ailettes: {N_diff:+d} ailettes")

print("\n" + "="*80)
print(" ✅ OPTIMISATION TERMINÉE!")
print("="*80)
print("\nFichiers générés:")
print("  • optimisation_3_solutions_phase1.csv")
if best_configs and best_configs['min_cost']:
    print("  • optimisation_3_solutions_phase2.csv")
print("\nGraphiques: Fermez les fenêtres matplotlib pour terminer.")
print("="*80)
