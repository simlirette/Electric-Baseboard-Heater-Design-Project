import numpy as py
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import time

# ============================================================================
# SCRIPT D'OPTIMISATION POUR LE PROJET MEC423
# Ce script automatise la recherche de la configuration optimale (R, a, N)
# ============================================================================

# IMPORTANT: Copiez/collez la fonction solve_thermal_problem() depuis le code principal
# ou importez-la si vous avez structuré votre code en modules

def solve_thermal_problem(L, P, h_conv, T_air, k_c, R, a, N, verbose=False):
    """
    Résout le problème thermique pour une configuration donnée.
    
    Retourne: (Tmax, Tmin, cout, success)
    """
    
    pi = py.pi
    
    # Géométrie
    t1 = R / 5
    R_int = R - t1
    t_a = a / 100
    pas_ailette = L / N
    
    # Paramètres de maillage (adapter selon la précision souhaitée)
    nr_tube = 4
    nr_ailette = 6
    nz_ailette = 2
    nz_espace = 8
    
    z_max = pas_ailette / 2
    
    # Génération du maillage
    r_tube = py.linspace(R_int, R, nr_tube)
    r_ailette_sans_tube = py.linspace(R, R+a, nr_ailette+1)[1:]
    r_coords = py.concatenate([r_tube, r_ailette_sans_tube])

    z_ailette = py.linspace(0, t_a/2, nz_ailette)
    z_espace = py.linspace(t_a/2, z_max, nz_espace+1)[1:]
    z_coords = py.concatenate([z_ailette, z_espace])
    
    nz_total = len(z_coords)
    nr_total = len(r_coords)
    nn_total = nz_total * nr_total
    
    # Coordonnées des noeuds
    xy = py.zeros((nn_total, 2))
    node_id = 0
    for iz in range(nz_total):
        for ir in range(nr_total):
            xy[node_id, 0] = r_coords[ir]
            xy[node_id, 1] = z_coords[iz]
            node_id += 1
    
    # Fonction pour numérotation
    def get_node_number(ir, iz):
        return iz * nr_total + ir + 1
    
    # Connectivités
    elements = []
    for iz in range(nz_total - 1):
        for ir in range(nr_total - 1):
            n1 = get_node_number(ir, iz)
            n2 = get_node_number(ir+1, iz)
            n3 = get_node_number(ir+1, iz+1)
            n4 = get_node_number(ir, iz+1)
            elements.append([n1, n2, n3])
            elements.append([n1, n3, n4])
    
    cn = py.array(elements)
    ne = cn.shape[0]
    kc = py.full(ne, k_c)
    Q = 0
    
    # Conditions frontières - Convection
    convection_faces = []
    idx_R = py.where(py.isclose(r_coords, R, rtol=1e-6))[0][0]
    idx_Ra = len(r_coords) - 1
    idx_ta2 = len(z_ailette) - 1
    idx_0 = 0
    idx_zmax = nz_total - 1
    
    for iz in range(idx_ta2, idx_zmax):
        ni = get_node_number(idx_R, iz)
        nj = get_node_number(idx_R, iz+1)
        convection_faces.append([ni, nj, h_conv, T_air])
    
    for ir in range(idx_R, idx_Ra):
        ni = get_node_number(ir, idx_ta2)
        nj = get_node_number(ir+1, idx_ta2)
        convection_faces.append([ni, nj, h_conv, T_air])
    
    for iz in range(idx_0, idx_ta2):
        ni = get_node_number(idx_Ra, iz)
        nj = get_node_number(idx_Ra, iz+1)
        convection_faces.append([ni, nj, h_conv, T_air])
    
    ijhTf = py.array(convection_faces)
    nh = ijhTf.shape[0]

    # Conditions frontières - Flux
    sigma_i = P / (2 * pi * R_int * L)
    flux_faces = []
    idx_Rint = 0
    for iz in range(nz_total - 1):
        ni = get_node_number(idx_Rint, iz)
        nj = get_node_number(idx_Rint, iz+1)
        flux_faces.append([ni, nj, sigma_i])

    ijflux = py.array(flux_faces)
    nflux = ijflux.shape[0]

    # Résolution
    nn = xy.shape[0]
    kg = py.zeros((nn, nn))
    fg = py.zeros(nn)
    
    # Matrices de conduction
    for ie in range(ne):
        ni, nj, nk = cn[ie, 0], cn[ie, 1], cn[ie, 2]
        xi, yi = xy[ni-1, 0], xy[ni-1, 1]
        xj, yj = xy[nj-1, 0], xy[nj-1, 1]
        xk, yk = xy[nk-1, 0], xy[nk-1, 1]
        
        Vi = py.array([xk-xj, yk-yj])
        Vj = py.array([xi-xk, yi-yk])
        Vk = py.array([xj-xi, yj-yi])

        A = 0.5 * ((xj-xi)*(yk-yj) - (yj-yi)*(xk-xj))
        xm = (xi + xj + xk) / 3

        K = kc[ie] * xm / (4 * abs(A)) * py.array([
            [py.dot(Vi, Vi), py.dot(Vi, Vj), py.dot(Vi, Vk)],
            [py.dot(Vj, Vi), py.dot(Vj, Vj), py.dot(Vj, Vk)],
            [py.dot(Vk, Vi), py.dot(Vk, Vj), py.dot(Vk, Vk)]
        ])

        fV = Q * abs(A) / 12 * py.array([2*xi + xj + xk, xi + 2*xj + xk, xi + xj + 2*xk])

        ind = py.array([ni-1, nj-1, nk-1])
        ix, iy = py.meshgrid(ind, ind)
        kg[ix, iy] += K
        fg[ind] += fV
    
    # Convection
    for fi in range(nh):
        ni, nj = int(ijhTf[fi, 0]), int(ijhTf[fi, 1])
        hij, Tfij = ijhTf[fi, 2], ijhTf[fi, 3]
        xi, yi = xy[ni-1, 0], xy[ni-1, 1]
        xj, yj = xy[nj-1, 0], xy[nj-1, 1]
        Lij = py.sqrt((xj-xi)**2 + (yj-yi)**2)

        H = Lij * hij / 12 * py.array([[3*xi + xj, xi + xj], [xi + xj, xi + 3*xj]])
        fh = Lij * hij * Tfij / 6 * py.array([2*xi + xj, xi + 2*xj])

        ind = py.array([ni-1, nj-1])
        ix, iy = py.meshgrid(ind, ind)
        kg[ix, iy] += H
        fg[ind] += fh
    
    # Flux
    for fi in range(nflux):
        ni, nj = int(ijflux[fi, 0]), int(ijflux[fi, 1])
        sij = ijflux[fi, 2]
        xi, yi = xy[ni-1, 0], xy[ni-1, 1]
        xj, yj = xy[nj-1, 0], xy[nj-1, 1]
        Lij = py.sqrt((xj-xi)**2 + (yj-yi)**2)

        fs = Lij * sij / 6 * py.array([2*xi + xj, xi + 2*xj])
        ind = py.array([ni-1, nj-1])
        fg[ind] += fs
    
    # Solution
    try:
        T = py.linalg.solve(kg, fg)
        Tmax = py.max(T)
        Tmin = py.min(T)

        # Calcul du coût
        cout = 2e4 * L * R**2 + 1000 * N * a * ((R+a)**2 - R**2) + 3 * py.sqrt(N)
        
        if verbose:
            print(f"  R={R*1000:.1f}mm, a={a*1000:.1f}mm, N={N:3d} → Tmax={Tmax:.1f}°C, Coût={cout:.2f}$")
        
        return Tmax, Tmin, cout, True
        
    except:
        if verbose:
            print(f"  R={R*1000:.1f}mm, a={a*1000:.1f}mm, N={N:3d} → ERREUR")
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
    L = 2.2  # Adapter selon vos données
    
    cout_tube = 2e4 * L * R_best**2
    cout_ailettes = 1000 * N_best * a_best * ((R_best+a_best)**2 - R_best**2)
    cout_assemblage = 3 * np.sqrt(N_best)
    
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
    # Suggestion: Commencer avec des plages larges et peu de points
    # puis raffiner autour de l'optimum trouvé
    
    # Première itération: exploration large
    R_values = py.linspace(0.005, 0.008, 100)  # 5 à 8 mm, 100 points
    a_values = py.linspace(0.050, 0.070, 100)  # 50 à 70 mm, 100 points
    
    print("\n🔍 PHASE 1: EXPLORATION LARGE")
    df_results, best_config = optimize_design(
        L, P, h_conv, T_air, k_c,
        R_range=R_values,
        a_range=a_values,
        N_min=5,
        N_max=30,
        N_step=5,
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
        
        # Raffiner avec une grille plus fine
        R_values_fine = py.linspace(R_opt - 0.001, R_opt + 0.001, 10)  # ±1mm
        a_values_fine = py.linspace(a_opt - 0.001, a_opt + 0.001, 10)  # ±1mm
        
        df_results_fine, best_config_fine = optimize_design(
            L, P, h_conv, T_air, k_c,
            R_range=R_values_fine,
            a_range=a_values_fine,
            N_min=max(10, best_config['N'] - 20),
            N_max=best_config['N'] + 20,
            N_step=5,
            T_max_limit=250,
            tolerance=2
        )
        
        if not df_results_fine.empty:
            df_results_fine.to_csv('resultats_optimisation_phase2.csv', index=False)
            print("\n📊 Résultats raffinés sauvegardés: resultats_optimisation_phase2.csv")
            plot_optimization_results(df_results_fine)
    
    print("\n✅ Optimisation terminée!")
    print("Vérifiez les fichiers CSV et les graphiques générés.")
