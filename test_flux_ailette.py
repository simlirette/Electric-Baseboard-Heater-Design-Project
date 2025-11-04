#!/usr/bin/env python3
"""
Test: flux appliqué seulement sous l'ailette (pas dans l'espace)
"""
import numpy as py
from numpy.linalg import solve

pi = py.pi

# Paramètres
L = 3.0
P = 3600
h_conv = 30
T_air = 60
k_c = 150
R = 0.010
a = 0.034
N = 60

t1 = R / 5
R_int = R - t1
t_a = a / 100
pas_ailette = L / N

print("="*70)
print(" ANALYSE DU FLUX")
print("="*70)

# Hypothèse 1: Flux sur toute la longueur (actuel)
sigma_1 = P / (2 * pi * R_int * L)
print(f"\nHypothèse 1: Flux uniforme sur toute la longueur L")
print(f"  σ_1 = P / (2π R_int L) = {sigma_1:.2f} W/m²")
P_verifsubscribe = sigma_1 * 2 * pi * R_int * L
print(f"  Vérification: {P_verifsubscribe:.2f} W")

# Hypothèse 2: Flux seulement sous les ailettes
longueur_ailettes = N * t_a
sigma_2 = P / (2 * pi * R_int * longueur_ailettes)
print(f"\nHypothèse 2: Flux seulement sous les ailettes")
print(f"  Longueur totale d'ailettes: N × t_a = {longueur_ailettes*1000:.2f} mm")
print(f"  σ_2 = P / (2π R_int N×t_a) = {sigma_2:.2f} W/m²")
print(f"  Rapport σ_2/σ_1 = {sigma_2/sigma_1:.2f}")
P_verif = sigma_2 * 2 * pi * R_int * longueur_ailettes
print(f"  Vérification: {P_verif:.2f} W")

# Hypothèse 3: La formule du PDF pourrait être mal interprétée
# Peut-être que le flux moyen doit être ajusté pour la portion modélisée?
print(f"\nHypothèse 3: Ajustement pour la portion modélisée")
print(f"  Le modèle Python modélise 1/(2N) = 1/{2*N} de la longueur totale")
print(f"  Portion modélisée: {(pas_ailette/2)*1000:.2f} mm")
print(f"  Part d'ailette: {(t_a/2)*1000:.3f} mm")
print(f"  Part d'espace: {((pas_ailette/2)-(t_a/2))*1000:.2f} mm")

# Rapport entre épaisseur d'ailette et pas
rapport_ailette = t_a / pas_ailette
print(f"  Rapport t_a/pas_ailette = {rapport_ailette:.4f}")

print("\n" + "="*70)
print(" CONCLUSION")
print("="*70)
print("Si le flux doit être appliqué seulement sous les ailettes:")
print(f"  Le flux devrait être {sigma_2/sigma_1:.2f}x plus élevé")
print(f"  Soit σ = {sigma_2:.2f} W/m² au lieu de {sigma_1:.2f} W/m²")
print("="*70)
