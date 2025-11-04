import numpy as py
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import time

# Importer la fonction de résolution depuis le programme principal
from mec423_heating_baseboard import solve_heating_baseboard

# ============================================================================
# SCRIPT D'OPTIMISATION POUR LE PROJET MEC423
# Ce script automatise la recherche de la configuration optimale (R, a, N)
# ============================================================================

def solve_thermal_problem(L, P, h_conv, T_air, k_c, R, a, N, verbose=False):
    """
    Résout le problème thermique pour une configuration donnée.
    Utilise la fonction complète de mec423_heating_baseboard.

    Retourne: (Tmax, Tmin, cout, success)
    """

    # Appeler la fonction du programme principal avec les paramètres de maillage par défaut
    result = solve_heating_baseboard(
        L=L, P=P, h_conv=h_conv, T_air=T_air, k_c=k_c,
        R=R, a=a, N=N,
        nr_tube=5,        # Même valeur que le programme principal
        nr_ailette=8,     # Même valeur que le programme principal
        nz_ailette=3,     # Même valeur que le programme principal
        nz_espace=10,     # Même valeur que le programme principal
        verbose=verbose,
        plot_results=False
    )

    if result['success']:
        return result['Tmax'], result['Tmin'], result['cout_total'], True
    else:
        return 999, 0, 999999, False


# ============================================================================
# FONCTION D'OPTIMISATION
# ============================================================================

def optimize_design(L, P, h_conv, T_air, k_c,
                   R_range, a_range, N_min=10, N_max=200, N_step=5,
                   T_max_target_min=248, T_max_target_max=250):
    """
    Optimise la conception en balayant R, a et N.
    Trouve 3 solutions optimales:
    1. Température la plus proche de la cible [248-250°C]
    2. Coût minimal dans la plage cible
    3. Nombre d'ailettes minimal dans la plage cible

    Paramètres:
        L, P, h_conv, T_air, k_c: Paramètres du problème
        R_range: liste ou array des valeurs de R à tester [m]
        a_range: liste ou array des valeurs de a à tester [m]
        N_min, N_max, N_step: Plage et pas pour N
        T_max_target_min, T_max_target_max: Plage de température cible [°C]

    Retourne:
        DataFrame avec tous les résultats + 3 configurations optimales
    """

    print("="*80)
    print(" OPTIMISATION DE LA PLINTHE CHAUFFANTE - 3 SOLUTIONS")
    print("="*80)
    print(f"\nParamètres du problème:")
    print(f"  L = {L} m, P = {P/1000} kW, h = {h_conv} W/m²°C, T_air = {T_air}°C")
    print(f"\nCritère de température: {T_max_target_min} ≤ T_max ≤ {T_max_target_max} °C")
    print(f"\nPlages de recherche:")
    print(f"  R: {min(R_range)*1000:.1f} à {max(R_range)*1000:.1f} mm ({len(R_range)} valeurs)")
    print(f"  a: {min(a_range)*1000:.1f} à {max(a_range)*1000:.1f} mm ({len(a_range)} valeurs)")
    print(f"  N: {N_min} à {N_max} par pas de {N_step}")
    print("="*80)

    results = []

    # Trois configurations optimales à trouver
    best_temp_match = None      # Tmax la plus proche de [248-250]
    best_cost = None            # Coût minimal dans la plage
    best_min_fins = None        # N minimal dans la plage

    min_temp_deviation = float('inf')
    min_cost = float('inf')
    min_N = float('inf')
    
    total_configs = len(R_range) * len(a_range)
    config_count = 0
    start_time = time.time()
    
    for R in R_range:
        for a in a_range:
            config_count += 1
            print(f"\n[{config_count}/{total_configs}] Test: R={R*1000:.1f}mm, a={a*1000:.1f}mm")

            # Balayer toutes les valeurs de N pour trouver toutes les solutions
            for N in range(N_min, N_max+1, N_step):
                Tmax, Tmin, cout, success = solve_thermal_problem(
                    L, P, h_conv, T_air, k_c, R, a, N, verbose=False
                )

                if not success:
                    continue

                # Calculer la déviation par rapport à la cible de température
                # Cible centrale = (T_max_target_min + T_max_target_max) / 2
                T_target_center = (T_max_target_min + T_max_target_max) / 2
                temp_deviation = abs(Tmax - T_target_center)

                # Enregistrer tous les résultats
                results.append({
                    'R_mm': R * 1000,
                    'a_mm': a * 1000,
                    'N': N,
                    'Tmax_C': Tmax,
                    'Tmin_C': Tmin,
                    'cout_$': cout,
                    'temp_deviation_C': temp_deviation
                })

                # Solution 1: Température la plus proche de la cible (248-250°C)
                if temp_deviation < min_temp_deviation:
                    min_temp_deviation = temp_deviation
                    best_temp_match = {
                        'R': R, 'a': a, 'N': N,
                        'Tmax': Tmax, 'Tmin': Tmin, 'cout': cout,
                        'deviation': temp_deviation
                    }
                    print(f"  → Nouvelle meilleure précision temp: N={N}, Tmax={Tmax:.2f}°C (dév={temp_deviation:.2f}°C)")

                # Solutions 2 et 3: Seulement si dans la plage cible [248-250]
                if T_max_target_min <= Tmax <= T_max_target_max:

                    # Solution 2: Coût minimal dans la plage
                    if cout < min_cost:
                        min_cost = cout
                        best_cost = {
                            'R': R, 'a': a, 'N': N,
                            'Tmax': Tmax, 'Tmin': Tmin, 'cout': cout,
                            'deviation': temp_deviation
                        }
                        print(f"  → Nouveau meilleur coût: N={N}, Tmax={Tmax:.2f}°C, Coût={cout:.2f}$")

                    # Solution 3: Nombre d'ailettes minimal dans la plage
                    if N < min_N:
                        min_N = N
                        best_min_fins = {
                            'R': R, 'a': a, 'N': N,
                            'Tmax': Tmax, 'Tmin': Tmin, 'cout': cout,
                            'deviation': temp_deviation
                        }
                        print(f"  → Nouveau N minimal: N={N}, Tmax={Tmax:.2f}°C, Coût={cout:.2f}$")
    
    elapsed_time = time.time() - start_time

    # Créer DataFrame
    df_results = pd.DataFrame(results)

    print("\n" + "="*80)
    print(" OPTIMISATION TERMINÉE")
    print("="*80)
    print(f"Temps écoulé: {elapsed_time:.1f} secondes")
    print(f"Configurations testées: {len(results)}")

    # Afficher les 3 solutions optimales
    print("\n" + "="*80)
    print(" 🏆 3 SOLUTIONS OPTIMALES TROUVÉES ".center(80))
    print("="*80)

    # Solution 1: Température la plus proche
    if best_temp_match:
        print("\n" + "─"*80)
        print("📌 SOLUTION 1: TEMPÉRATURE LA PLUS PROCHE DE LA CIBLE [248-250°C]")
        print("─"*80)
        print(f"  Rayon tube:        R = {best_temp_match['R']*1000:.3f} mm")
        print(f"  Longueur ailettes: a = {best_temp_match['a']*1000:.3f} mm")
        print(f"  Nombre ailettes:   N = {best_temp_match['N']}")
        print(f"\n  Température max:   T_max = {best_temp_match['Tmax']:.2f} °C  ⭐ (déviation = {best_temp_match['deviation']:.2f}°C)")
        print(f"  Température min:   T_min = {best_temp_match['Tmin']:.2f} °C")
        print(f"  Coût total:        {best_temp_match['cout']:.2f} $")
    else:
        print("\n⚠️  Solution 1 non trouvée")

    # Solution 2: Coût minimal
    if best_cost:
        print("\n" + "─"*80)
        print("💰 SOLUTION 2: COÛT MINIMAL (avec 248°C ≤ Tmax ≤ 250°C)")
        print("─"*80)
        print(f"  Rayon tube:        R = {best_cost['R']*1000:.3f} mm")
        print(f"  Longueur ailettes: a = {best_cost['a']*1000:.3f} mm")
        print(f"  Nombre ailettes:   N = {best_cost['N']}")
        print(f"\n  Température max:   T_max = {best_cost['Tmax']:.2f} °C")
        print(f"  Température min:   T_min = {best_cost['Tmin']:.2f} °C")
        print(f"  Coût total:        {best_cost['cout']:.2f} $  ⭐ (COÛT MINIMAL)")
    else:
        print("\n⚠️  Solution 2 non trouvée (aucune config dans la plage 248-250°C)")

    # Solution 3: Nombre d'ailettes minimal
    if best_min_fins:
        print("\n" + "─"*80)
        print("🔧 SOLUTION 3: NOMBRE D'AILETTES MINIMAL (avec 248°C ≤ Tmax ≤ 250°C)")
        print("─"*80)
        print(f"  Rayon tube:        R = {best_min_fins['R']*1000:.3f} mm")
        print(f"  Longueur ailettes: a = {best_min_fins['a']*1000:.3f} mm")
        print(f"  Nombre ailettes:   N = {best_min_fins['N']}  ⭐ (N MINIMAL)")
        print(f"\n  Température max:   T_max = {best_min_fins['Tmax']:.2f} °C")
        print(f"  Température min:   T_min = {best_min_fins['Tmin']:.2f} °C")
        print(f"  Coût total:        {best_min_fins['cout']:.2f} $")
    else:
        print("\n⚠️  Solution 3 non trouvée (aucune config dans la plage 248-250°C)")

    print("\n" + "="*80)

    return df_results, {'temp_match': best_temp_match, 'min_cost': best_cost, 'min_fins': best_min_fins}


# ============================================================================
# VISUALISATION DES RÉSULTATS
# ============================================================================

def plot_optimization_results(df_results):
    """
    Crée des graphiques pour visualiser les résultats d'optimisation.
    """
    
    if df_results.empty:
        print("Aucun résultat à visualiser!")
        return
    
    fig = plt.figure(figsize=(16, 10))
    
    # 1. Coût vs R (pour chaque a)
    ax1 = plt.subplot(2, 3, 1)
    for a_val in df_results['a_mm'].unique():
        data = df_results[df_results['a_mm'] == a_val]
        ax1.plot(data['R_mm'], data['cout_$'], 'o-', label=f'a={a_val:.1f}mm')
    ax1.set_xlabel('Rayon R [mm]')
    ax1.set_ylabel('Coût [$]')
    ax1.set_title('Coût vs Rayon du tube')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Coût vs a (pour chaque R)
    ax2 = plt.subplot(2, 3, 2)
    for R_val in df_results['R_mm'].unique():
        data = df_results[df_results['R_mm'] == R_val]
        ax2.plot(data['a_mm'], data['cout_$'], 's-', label=f'R={R_val:.1f}mm')
    ax2.set_xlabel('Longueur ailettes a [mm]')
    ax2.set_ylabel('Coût [$]')
    ax2.set_title('Coût vs Longueur ailettes')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Tmax vs N
    ax3 = plt.subplot(2, 3, 3)
    sample_data = df_results[df_results['R_mm'] == df_results['R_mm'].median()]
    ax3.plot(sample_data['N'], sample_data['Tmax_C'], 'o-', color='red')
    ax3.axhline(y=250, color='k', linestyle='--', label='Limite T_max=250°C')
    ax3.set_xlabel('Nombre d\'ailettes N')
    ax3.set_ylabel('T_max [°C]')
    ax3.set_title('Température maximale vs N')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Surface 3D: Coût(R, a)
    ax4 = plt.subplot(2, 3, 4, projection='3d')
    R_unique = sorted(df_results['R_mm'].unique())
    a_unique = sorted(df_results['a_mm'].unique())
    
    # Créer une grille régulière
    R_grid, a_grid = py.meshgrid(R_unique, a_unique)
    cout_grid = py.zeros_like(R_grid)
    
    for i, R_val in enumerate(R_unique):
        for j, a_val in enumerate(a_unique):
            matching = df_results[(df_results['R_mm'] == R_val) & 
                                 (df_results['a_mm'] == a_val)]
            if not matching.empty:
                cout_grid[j, i] = matching['cout_$'].values[0]
            else:
                cout_grid[j, i] = py.nan
    
    surf = ax4.plot_surface(R_grid, a_grid, cout_grid, cmap='viridis', alpha=0.8)
    ax4.set_xlabel('R [mm]')
    ax4.set_ylabel('a [mm]')
    ax4.set_zlabel('Coût [$]')
    ax4.set_title('Surface de coût')
    
    # 5. Déviation de température vs Coût
    ax5 = plt.subplot(2, 3, 5)
    scatter = ax5.scatter(df_results['temp_deviation_C'], df_results['cout_$'],
                         c=df_results['N'], cmap='coolwarm', s=50, alpha=0.6)
    ax5.set_xlabel('Déviation de température (par rapport à 249°C) [°C]')
    ax5.set_ylabel('Coût [$]')
    ax5.set_title('Compromis Coût-Précision de Température')
    plt.colorbar(scatter, ax=ax5, label='Nombre ailettes N')
    ax5.grid(True, alpha=0.3)
    
    # 6. Répartition des coûts pour l'optimal
    ax6 = plt.subplot(2, 3, 6)
    best_row = df_results.loc[df_results['cout_$'].idxmin()]
    R_best = best_row['R_mm'] / 1000
    a_best = best_row['a_mm'] / 1000
    N_best = int(best_row['N'])
    L = 3.0  # Longueur du tube

    cout_tube = 2e4 * L * R_best**2
    cout_ailettes = 1000 * N_best * a_best * ((R_best+a_best)**2 - R_best**2)
    cout_assemblage = 3 * py.sqrt(N_best)
    
    categories = ['Tube', 'Ailettes', 'Assemblage']
    couts = [cout_tube, cout_ailettes, cout_assemblage]
    colors = ['#ff9999', '#66b3ff', '#99ff99']
    
    ax6.bar(categories, couts, color=colors, edgecolor='black')
    ax6.set_ylabel('Coût [$]')
    ax6.set_title('Répartition des coûts (config. optimale)')
    ax6.grid(True, alpha=0.3, axis='y')
    
    # Ajouter les valeurs sur les barres
    for i, v in enumerate(couts):
        ax6.text(i, v + max(couts)*0.02, f'{v:.2f}$', ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.show()


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    
    # === PARAMÈTRES DU PROJET (MEC423-02, Équipe 10) ===
    L = 3.0      # [m]
    P = 3600     # [W] (3.6 kW)
    h_conv = 30  # [W/m²°C]
    T_air = 60   # [°C]
    k_c = 150    # [W/m°C]
    
    # === PLAGES D'OPTIMISATION ===
    # Stratégie: Exploration large puis raffinement

    # Première itération: exploration large avec moins de points pour vitesse
    R_values = py.linspace(0.006, 0.012, 7)    # 6 à 12 mm, 7 points
    a_values = py.linspace(0.020, 0.050, 7)    # 20 à 50 mm, 7 points

    print("\n🔍 PHASE 1: EXPLORATION LARGE")
    df_results, best_configs = optimize_design(
        L, P, h_conv, T_air, k_c,
        R_range=R_values,
        a_range=a_values,
        N_min=10,
        N_max=100,
        N_step=10,
        T_max_target_min=248,
        T_max_target_max=250
    )

    # Sauvegarder les résultats
    if not df_results.empty:
        df_results.to_csv('resultats_optimisation_phase1.csv', index=False)
        print("\n📊 Résultats sauvegardés: resultats_optimisation_phase1.csv")

        # Afficher le top 10 par coût
        print("\n📋 TOP 10 DES CONFIGURATIONS (par coût):")
        top_10 = df_results.nsmallest(10, 'cout_$')
        print(top_10[['R_mm', 'a_mm', 'N', 'Tmax_C', 'cout_$', 'temp_deviation_C']].to_string(index=False))

        # Visualisation
        plot_optimization_results(df_results)

    # === PHASE 2: RAFFINEMENT (optionnel) ===
    # On raffine autour de la solution à coût minimal
    if best_configs and best_configs['min_cost']:
        print("\n\n🔬 PHASE 2: RAFFINEMENT AUTOUR DE LA SOLUTION À COÛT MINIMAL")

        best_cost_config = best_configs['min_cost']
        R_opt = best_cost_config['R']
        a_opt = best_cost_config['a']
        N_opt = best_cost_config['N']

        # Raffiner avec une grille plus fine autour de l'optimum
        R_values_fine = py.linspace(max(0.006, R_opt - 0.002), R_opt + 0.002, 9)  # ±2mm, 9 points
        a_values_fine = py.linspace(max(0.020, a_opt - 0.005), a_opt + 0.005, 9)  # ±5mm, 9 points

        df_results_fine, best_configs_fine = optimize_design(
            L, P, h_conv, T_air, k_c,
            R_range=R_values_fine,
            a_range=a_values_fine,
            N_min=max(10, N_opt - 10),
            N_max=N_opt + 10,
            N_step=2,
            T_max_target_min=248,
            T_max_target_max=250
        )

        if not df_results_fine.empty:
            df_results_fine.to_csv('resultats_optimisation_phase2.csv', index=False)
            print("\n📊 Résultats raffinés sauvegardés: resultats_optimisation_phase2.csv")
            plot_optimization_results(df_results_fine)
    
    print("\n✅ Optimisation terminée!")
    print("Vérifiez les fichiers CSV et les graphiques générés.")
