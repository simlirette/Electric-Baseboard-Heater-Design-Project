import numpy as py
from mec423_heating_baseboard import solve_heating_baseboard
import time

# ============================================================================
# TEST RAPIDE DE L'OPTIMISATION
# Ce script teste rapidement quelques configurations pour vérifier que
# le système fonctionne correctement avant de lancer une optimisation complète
# ============================================================================

print("="*70)
print(" TEST RAPIDE DU SYSTÈME D'OPTIMISATION")
print("="*70)

# Paramètres du projet
L = 3.0
P = 3600
h_conv = 30
T_air = 60
k_c = 150

# Configurations de test
test_configs = [
    {"R": 0.008, "a": 0.030, "N": 50, "nom": "Config 1: Petit tube, ailettes moyennes"},
    {"R": 0.010, "a": 0.035, "N": 60, "nom": "Config 2: Tube moyen, ailettes moyennes"},
    {"R": 0.012, "a": 0.040, "N": 70, "nom": "Config 3: Gros tube, grandes ailettes"},
]

print("\nTest de 3 configurations...")
print("-"*70)

results = []

for i, config in enumerate(test_configs, 1):
    print(f"\n{i}. {config['nom']}")
    print(f"   R = {config['R']*1000:.1f} mm, a = {config['a']*1000:.1f} mm, N = {config['N']}")

    start = time.time()

    result = solve_heating_baseboard(
        L=L, P=P, h_conv=h_conv, T_air=T_air, k_c=k_c,
        R=config['R'], a=config['a'], N=config['N'],
        nr_tube=4,  # Maillage réduit pour vitesse
        nr_ailette=6,
        nz_ailette=2,
        nz_espace=8,
        verbose=False,
        plot_results=False
    )

    elapsed = time.time() - start

    if result['success']:
        results.append(result)
        print(f"   ✓ Tmax = {result['Tmax']:.1f}°C")
        print(f"   ✓ Coût = {result['cout_total']:.2f} $")

        if result['Tmax'] <= 250:
            print(f"   ✓ CRITÈRE RESPECTÉ (marge: {250-result['Tmax']:.1f}°C)")
        else:
            print(f"   ✗ Critère non respecté (dépassement: {result['Tmax']-250:.1f}°C)")

        print(f"   ⏱ Temps: {elapsed:.2f}s")
    else:
        print(f"   ✗ ERREUR lors du calcul")

print("\n" + "="*70)
print(" RÉSUMÉ")
print("="*70)

if results:
    # Trouver la meilleure config
    valid_results = [r for r in results if r['Tmax'] <= 250]

    if valid_results:
        best = min(valid_results, key=lambda x: x['cout_total'])
        best_idx = results.index(best)

        print(f"\n🏆 MEILLEURE CONFIGURATION (parmi celles testées):")
        print(f"   Configuration {best_idx + 1}")
        print(f"   Tmax = {best['Tmax']:.1f}°C")
        print(f"   Coût = {best['cout_total']:.2f} $")
        print(f"   Répartition:")
        print(f"     - Tube:       {best['cout_tube']:.2f} $")
        print(f"     - Ailettes:   {best['cout_ailettes']:.2f} $")
        print(f"     - Assemblage: {best['cout_assemblage']:.2f} $")
    else:
        print(f"\n⚠️  Aucune des configurations testées ne respecte T_max ≤ 250°C")
        print(f"   Il faudra tester avec:")
        print(f"   - Plus d'ailettes (N plus grand)")
        print(f"   - Ailettes plus longues (a plus grand)")
        print(f"   - Tube plus gros (R plus grand)")

    print(f"\n✓ Le système fonctionne correctement!")
    print(f"  Vous pouvez maintenant lancer: python3 mec423_optimization.py")
    print(f"  pour une optimisation complète avec exploration de toutes les combinaisons.")
else:
    print(f"\n✗ Erreurs détectées. Vérifier le code.")

print("="*70)
