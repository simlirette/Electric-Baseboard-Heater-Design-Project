import numpy as py
import matplotlib
matplotlib.use('Agg')  # Mode non-interactif pour les tests
import matplotlib.pyplot as plt

# Import de la fonction de résolution depuis mec423_optimization
import sys
sys.path.insert(0, '/home/user/Electric-Baseboard-Heater-Design-Project')
from mec423_optimization import solve_thermal_problem

# ============================================================================
# TEST RAPIDE DE LA SOLUTION
# ============================================================================

print("="*70)
print(" TEST DE LA SOLUTION - MEC423-02, Équipe 10")
print("="*70)

# Paramètres du projet
L = 3.0      # [m]
P = 3600     # [W]
h_conv = 30  # [W/m²°C]
T_air = 60   # [°C]
k_c = 150    # [W/m°C]

# Test avec des valeurs initiales raisonnables
print("\nTest 1: Configuration initiale")
R_test = 0.012    # 12 mm
a_test = 0.038    # 38 mm
N_test = 65

print(f"  R = {R_test*1000:.1f} mm")
print(f"  a = {a_test*1000:.1f} mm")
print(f"  N = {N_test}")

Tmax, Tmin, cout, success = solve_thermal_problem(
    L, P, h_conv, T_air, k_c, R_test, a_test, N_test, verbose=True
)

if success:
    print(f"\n  Résultats:")
    print(f"    T_max = {Tmax:.2f} °C")
    print(f"    T_min = {Tmin:.2f} °C")
    print(f"    Coût = {cout:.2f} $")
    print(f"    Critère T_max ≤ 250°C: {'✓ RESPECTÉ' if Tmax <= 250 else '✗ NON RESPECTÉ'}")
    print(f"    Marge: {250-Tmax:.2f} °C")
else:
    print("  ✗ ERREUR lors de la résolution")

# Test avec différentes valeurs de N pour trouver le N_min
print("\n" + "="*70)
print("Test 2: Recherche du N_min pour R=12mm, a=38mm")
print("="*70)

N_values = range(10, 120, 5)
results = []

for N in N_values:
    Tmax, Tmin, cout, success = solve_thermal_problem(
        L, P, h_conv, T_air, k_c, R_test, a_test, N, verbose=False
    )
    if success:
        results.append((N, Tmax, cout))
        status = "✓" if Tmax <= 250 else "✗"
        print(f"  N={N:3d} → T_max={Tmax:6.2f}°C, Coût={cout:7.2f}$ {status}")

        # Arrêter dès qu'on trouve le premier N qui respecte le critère
        if Tmax <= 250:
            print(f"\n  ➤ N_min trouvé: {N} ailettes")
            print(f"    T_max = {Tmax:.2f} °C")
            print(f"    Coût = {cout:.2f} $")
            break

print("\n" + "="*70)
print(" TEST TERMINÉ")
print("="*70)
print("\nLes fichiers sont prêts. Pour lancer l'optimisation complète:")
print("  python mec423_optimization.py")
