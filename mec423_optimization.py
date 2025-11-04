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
                   T_max_limit=250, tolerance=2):
    """
    Optimise la conception en balayant R, a et N.
    
    Paramètres:
        L, P, h_conv, T_air, k_c: Paramètres du problème
        R_range: liste ou array des valeurs de R à tester [m]
        a_range: liste ou array des valeurs de a à tester [m]
        N_min, N_max, N_step: Plage et pas pour N
        T_max_limit: Température maximale permise [°C]
        tolerance: Tolérance sur T_max [°C]
    
    Retourne:
        DataFrame avec tous les résultats + configuration optimale
    """
    
    print("="*80)
    print(" OPTIMISATION DE LA PLINTHE CHAUFFANTE")
    print("="*80)
    print(f"\nParamètres du problème:")
    print(f"  L = {L} m, P = {P/1000} kW, h = {h_conv} W/m²°C, T_air = {T_air}°C")
    print(f"\nCritère: {T_max_limit-tolerance} ≤ T_max ≤ {T_max_limit+tolerance} °C")
    print(f"\nPlages de recherche:")
    print(f"  R: {min(R_range)*1000:.1f} à {max(R_range)*1000:.1f} mm ({len(R_range)} valeurs)")
    print(f"  a: {min(a_range)*1000:.1f} à {max(a_range)*1000:.1f} mm ({len(a_range)} valeurs)")
    print(f"  N: {N_min} à {N_max} par pas de {N_step}")
    print("="*80)
    
    results = []
    best_cost = float('inf')
    best_config = None
    
    total_configs = len(R_range) * len(a_range)
    config_count = 0
    start_time = time.time()
    
    for R in R_range:
        for a in a_range:
            config_count += 1
            print(f"\n[{config_count}/{total_configs}] Test: R={R*1000:.1f}mm, a={a*1000:.1f}mm")
            
            # Recherche du N_min qui respecte le critère
            N_found = None
            
            for N in range(N_min, N_max+1, N_step):
                Tmax, Tmin, cout, success = solve_thermal_problem(
                    L, P, h_conv, T_air, k_c, R, a, N, verbose=False
                )
                
                if not success:
                    continue
                
                # Vérifier si le critère est respecté
                if Tmax <= T_max_limit + tolerance:
                    N_found = N
                    print(f"  → N_min trouvé: {N} (Tmax={Tmax:.2f}°C, Coût={cout:.2f}$)")
                    
                    # Enregistrer ce résultat
                    results.append({
                        'R_mm': R * 1000,
                        'a_mm': a * 1000,
                        'N': N,
                        'Tmax_C': Tmax,
                        'Tmin_C': Tmin,
                        'cout_$': cout,
                        'marge_C': T_max_limit - Tmax
                    })
                    
                    # Vérifier si c'est la meilleure configuration
                    if cout < best_cost and Tmax <= T_max_limit :
                        best_cost = cout
                        best_config = {
                            'R': R,
                            'a': a,
                            'N': N,
                            'Tmax': Tmax,
                            'Tmin': Tmin,
                            'cout': cout,
                            'marge': T_max_limit - Tmax
                        }
                    
                    break  # Passer à la prochaine combinaison (R, a)
            
            if N_found is None:
                print(f"  → Aucun N trouvé (Tmax toujours > {T_max_limit+tolerance}°C)")
    
    elapsed_time = time.time() - start_time
    
    # Créer DataFrame
    df_results = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print(" OPTIMISATION TERMINÉE")
    print("="*80)
    print(f"Temps écoulé: {elapsed_time:.1f} secondes")
    print(f"Configurations testées: {len(results)}")
    
    if best_config:
        print("\n" + "🏆 CONFIGURATION OPTIMALE TROUVÉE ".center(80, "="))
        print(f"\n  Rayon tube:        R = {best_config['R']*1000:.3f} mm")
        print(f"  Longueur ailettes: a = {best_config['a']*1000:.3f} mm")
        print(f"  Nombre ailettes:   N = {best_config['N']}")
        print(f"\n  Température max:   T_max = {best_config['Tmax']:.2f} °C")
        print(f"  Température min:   T_min = {best_config['Tmin']:.2f} °C")
        print(f"  Marge sécurité:    {best_config['marge']:.2f} °C")
        print(f"\n  COÛT MINIMUM:      {best_config['cout']:.2f} $")
        print("="*80)
    else:
        print("\n⚠️  Aucune configuration optimale trouvée dans les plages données!")
    
    return df_results, best_config


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
    
    # 5. Marge de sécurité vs Coût
    ax5 = plt.subplot(2, 3, 5)
    scatter = ax5.scatter(df_results['marge_C'], df_results['cout_$'], 
                         c=df_results['N'], cmap='coolwarm', s=50, alpha=0.6)
    ax5.set_xlabel('Marge de sécurité [°C]')
    ax5.set_ylabel('Coût [$]')
    ax5.set_title('Compromis Coût-Sécurité')
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
    df_results, best_config = optimize_design(
        L, P, h_conv, T_air, k_c,
        R_range=R_values,
        a_range=a_values,
        N_min=10,
        N_max=100,
        N_step=10,
        T_max_limit=250,
        tolerance=2
    )
    
    # Sauvegarder les résultats
    if not df_results.empty:
        df_results.to_csv('resultats_optimisation_phase1.csv', index=False)
        print("\n📊 Résultats sauvegardés: resultats_optimisation_phase1.csv")
        
        # Afficher le top 10
        print("\n📋 TOP 10 DES CONFIGURATIONS:")
        print(df_results.nsmallest(10, 'cout_$').to_string(index=False))
        
        # Visualisation
        plot_optimization_results(df_results)
    
    # === PHASE 2: RAFFINEMENT (optionnel) ===
    if best_config:
        print("\n\n🔬 PHASE 2: RAFFINEMENT AUTOUR DE L'OPTIMUM")

        R_opt = best_config['R']
        a_opt = best_config['a']

        # Raffiner avec une grille plus fine autour de l'optimum
        R_values_fine = py.linspace(R_opt - 0.002, R_opt + 0.002, 9)  # ±2mm, 9 points
        a_values_fine = py.linspace(a_opt - 0.005, a_opt + 0.005, 9)  # ±5mm, 9 points

        df_results_fine, best_config_fine = optimize_design(
            L, P, h_conv, T_air, k_c,
            R_range=R_values_fine,
            a_range=a_values_fine,
            N_min=max(10, best_config['N'] - 10),
            N_max=best_config['N'] + 10,
            N_step=2,
            T_max_limit=250,
            tolerance=2
        )
        
        if not df_results_fine.empty:
            df_results_fine.to_csv('resultats_optimisation_phase2.csv', index=False)
            print("\n📊 Résultats raffinés sauvegardés: resultats_optimisation_phase2.csv")
            plot_optimization_results(df_results_fine)
    
    print("\n✅ Optimisation terminée!")
    print("Vérifiez les fichiers CSV et les graphiques générés.")
