# Guide d'utilisation du programme d'optimisation

## Description

Le système d'optimisation coordonne maintenant deux programmes:

1. **mec423_heating_baseboard.py** : Programme principal qui résout le problème thermique pour une configuration donnée
2. **mec423_optimization.py** : Programme d'optimisation qui teste automatiquement différentes combinaisons pour trouver la meilleure solution

## Structure

```
mec423_heating_baseboard.py
├── solve_heating_baseboard()  ← Fonction réutilisable
└── Code principal (analyse d'une config spécifique)

mec423_optimization.py
├── Importe solve_heating_baseboard()
├── optimize_design()  ← Fonction d'optimisation
└── Stratégie d'optimisation en 2 phases
```

## Utilisation

### Option 1: Analyser une configuration spécifique

```bash
python3 mec423_heating_baseboard.py
```

Ce programme:
- Analyse la configuration définie dans les variables (R, a, N)
- Affiche les résultats détaillés
- Génère des graphiques du maillage et de la distribution de température

**Paramètres à modifier dans le fichier:**
```python
# Lignes 29-31
R = 0.010    # Rayon extérieur du tube [m]
a = 0.036    # Longueur radiale des ailettes [m]
N = 60       # Nombre total d'ailettes
```

### Option 2: Optimisation automatique

```bash
python3 mec423_optimization.py
```

Ce programme:
- **Phase 1**: Explore une large plage de valeurs (R, a, N)
- **Phase 2**: Raffine autour de l'optimum trouvé
- Génère des fichiers CSV avec tous les résultats
- Crée des graphiques d'analyse multi-dimensionnels

**Résultats générés:**
- `resultats_optimisation_phase1.csv` : Résultats de l'exploration large
- `resultats_optimisation_phase2.csv` : Résultats du raffinement
- Graphiques interactifs avec 6 visualisations différentes

## Personnalisation de l'optimisation

### Modifier les plages de recherche

Dans `mec423_optimization.py`, section "EXEMPLE D'UTILISATION":

```python
# Phase 1: Exploration large
R_values = py.linspace(0.006, 0.012, 7)    # min, max, nombre de points
a_values = py.linspace(0.020, 0.050, 7)    # min, max, nombre de points

optimize_design(
    L, P, h_conv, T_air, k_c,
    R_range=R_values,
    a_range=a_values,
    N_min=10,        # N minimum à tester
    N_max=100,       # N maximum à tester
    N_step=10,       # Pas de N
    T_max_limit=250, # Température max permise [°C]
    tolerance=2      # Tolérance sur T_max [°C]
)
```

### Ajuster la précision vs vitesse

**Pour plus de précision** (calculs plus lents):
```python
result = solve_heating_baseboard(
    L, P, h_conv, T_air, k_c, R, a, N,
    nr_tube=6,        # Plus de divisions
    nr_ailette=10,
    nz_ailette=4,
    nz_espace=12
)
```

**Pour plus de vitesse** (précision réduite):
```python
result = solve_heating_baseboard(
    L, P, h_conv, T_air, k_c, R, a, N,
    nr_tube=3,        # Moins de divisions
    nr_ailette=5,
    nz_ailette=2,
    nz_espace=6
)
```

## Interprétation des résultats

### Critères d'optimisation

Le programme cherche la configuration qui:
1. ✅ Respecte le critère thermique: **T_max ≤ 250°C**
2. 💰 Minimise le coût total

### Composantes du coût

```
Coût total = Coût tube + Coût ailettes + Coût assemblage

où:
- Coût tube = 2×10⁴ × L × R²
- Coût ailettes = 1000 × N × a × [(R+a)² - R²]
- Coût assemblage = 3 × √N
```

### Résultats typiques

L'optimisation affichera:
```
🏆 CONFIGURATION OPTIMALE TROUVÉE
  Rayon tube:        R = 8.5 mm
  Longueur ailettes: a = 42.3 mm
  Nombre ailettes:   N = 75

  Température max:   T_max = 248.5 °C
  Température min:   T_min = 142.3 °C
  Marge sécurité:    1.5 °C

  COÛT MINIMUM:      35.42 $
```

## Visualisations générées

Le programme crée 6 graphiques:

1. **Coût vs Rayon** : Impact du rayon du tube sur le coût
2. **Coût vs Longueur ailettes** : Impact de la longueur des ailettes
3. **T_max vs N** : Relation entre nombre d'ailettes et température
4. **Surface de coût 3D** : Coût en fonction de (R, a)
5. **Compromis Coût-Sécurité** : Relation entre marge de sécurité et coût
6. **Répartition des coûts** : Décomposition du coût optimal

## Stratégie d'optimisation recommandée

### 1. Exploration initiale rapide
```python
R_values = py.linspace(0.006, 0.012, 5)    # 5 points
a_values = py.linspace(0.020, 0.050, 5)    # 5 points
N_step = 20  # Pas large
```
**Durée estimée:** 5-10 minutes

### 2. Raffinement autour de l'optimum
Le programme le fait automatiquement en Phase 2

### 3. Validation finale
Utiliser `mec423_heating_baseboard.py` avec la configuration optimale et un maillage fin pour validation

## Exemple complet

```bash
# 1. Lancer l'optimisation
python3 mec423_optimization.py

# 2. Attendre les résultats (peut prendre 10-30 minutes)

# 3. Consulter les fichiers CSV générés
# Les résultats sont triés par coût croissant

# 4. Valider la meilleure configuration
# Éditer mec423_heating_baseboard.py avec R, a, N optimaux
python3 mec423_heating_baseboard.py
```

## Dépannage

### Problème: "Aucune configuration optimale trouvée"
**Solution:** Élargir les plages de recherche ou réduire N_step

### Problème: Calculs trop lents
**Solution:**
- Réduire le nombre de points dans R_values et a_values
- Augmenter N_step
- Utiliser un maillage plus grossier (nr_tube, nr_ailette, etc.)

### Problème: Toutes les températures dépassent 250°C
**Solution:**
- Augmenter N_max
- Augmenter la plage de `a` (ailettes plus longues)
- Augmenter la plage de `R` (tube plus gros)

## Notes importantes

1. **Temps de calcul:** Une optimisation complète peut prendre 10-60 minutes selon les paramètres
2. **Mémoire:** Le programme stocke tous les résultats en mémoire (DataFrame pandas)
3. **Précision:** Les résultats dépendent de la finesse du maillage et des plages testées
4. **Validation:** Toujours valider la configuration finale avec le programme principal

## Contact et support

Pour toute question, consulter:
- Le code source avec commentaires détaillés
- Les résultats CSV pour analyse approfondie
- Les graphiques pour insights visuels
