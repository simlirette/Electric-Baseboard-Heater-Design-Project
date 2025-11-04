# MÉTHODOLOGIE - PROJET PLINTHE CHAUFFANTE MEC423

## Vue d'ensemble

Ce document explique comment utiliser les fichiers `mec423_heating_baseboard.py` et `run_optimisation_complete.py` pour répondre aux exigences du projet.

---

## DONNÉES DU PROJET

Selon le PDF, chaque équipe a des données uniques:
- **L** : Longueur du tube [m]
- **P** : Puissance à dissiper [W]
- **h** : Coefficient de convection [W/(m²·°C)]
- **T_air** : Température de l'air ambiant [°C]

**Exemple (MEC423-02, Équipe 10):**
- L = 3.0 m
- P = 3600 W (3.6 kW)
- h = 30 W/(m²·°C)
- T_air = 60°C

---

## CONTRAINTES ET OBJECTIFS

### Contrainte principale:
**T_max ≤ 250±2 °C** → Donc: **248°C ≤ T_max ≤ 250°C**

### Objectif:
**Minimiser le coût:**
```
Coût = 2×10⁴ × L × R² + 1000 × N × a × ((R+a)² - R²) + 3 × √N
       └─────────┬─────────┘   └────────────┬────────────┘   └────┬───┘
          Coût tube           Coût ailettes            Coût assemblage
```

### Précision requise:
- R : à 0.001 m près (1 mm)
- a : à 0.001 m près (1 mm)
- N : à 5 ailettes près

---

## PARTIE 1: MODÈLE ÉLÉMENTS FINIS (mec423_heating_baseboard.py)

### Étape 1.1: Comprendre le modèle axisymétrique

**Fichier:** `mec423_heating_baseboard.py`

**Ce que fait ce fichier:**
1. Crée un maillage 2D axisymétrique (r, z) représentant:
   - Le tube cylindrique
   - Une ailette annulaire
   - Exploite la symétrie pour modéliser seulement 1/2 ailette

2. Applique les conditions frontières:
   - **Flux imposé** sur surface intérieure: σᵢ = P / (2π × R_int × L)
   - **Convection** sur surfaces extérieures: h, T_air

3. Résout le système d'équations par éléments finis

4. Retourne: T_max, T_min, coûts

### Étape 1.2: Utiliser la fonction solve_heating_baseboard()

**Syntaxe:**
```python
from mec423_heating_baseboard import solve_heating_baseboard

result = solve_heating_baseboard(
    L=3.0,           # Longueur tube [m]
    P=3600,          # Puissance [W]
    h_conv=30,       # Convection [W/(m²·°C)]
    T_air=60,        # Température air [°C]
    k_c=150,         # Conductivité [W/(m·°C)]
    R=0.010,         # Rayon tube [m] - VARIABLE DE CONCEPTION
    a=0.036,         # Longueur ailette [m] - VARIABLE DE CONCEPTION
    N=60,            # Nombre ailettes - VARIABLE DE CONCEPTION
    verbose=True,    # Afficher résultats
    plot_results=True # Afficher graphiques
)

# Récupérer les résultats
Tmax = result['Tmax']           # Température max [°C]
Tmin = result['Tmin']           # Température min [°C]
cout_total = result['cout_total'] # Coût total [$]
```

### Étape 1.3: Vérifier un cas de conception

Pour répondre à l'énoncé (1) du PDF: "résoudre un cas pour trouver Tmax et Tmin"

**Action:** Exécuter le fichier tel quel
```bash
python mec423_heating_baseboard.py
```

**Ce qui se passe:**
- Génère le maillage
- Résout le problème thermique
- Affiche: T_max, T_min, coûts
- Montre 2 graphiques:
  1. Maillage avec conditions frontières
  2. Distribution de température T(r,z)

---

## PARTIE 2: OPTIMISATION SIMPLE (Méthodologie suggérée du PDF)

### Énoncé (2): Déterminer N_min pour un R et a donnés

**Objectif:** Trouver le nombre minimal d'ailettes qui respecte 248°C ≤ T_max ≤ 250°C

**Procédure:**

```python
# Fixer L, R, a (exemple)
L = 3.0
R = 0.010  # 10 mm
a = 0.036  # 36 mm

# Tester différentes valeurs de N
for N in range(30, 121, 5):  # De 30 à 120, par pas de 5
    result = solve_heating_baseboard(L, P, h_conv, T_air, k_c, R, a, N)

    if 248 <= result['Tmax'] <= 250:
        print(f"✓ N={N}: Tmax={result['Tmax']:.1f}°C, Coût={result['cout_total']:.2f}$")
        break
```

**Résultat:** N_min et son coût associé

### Énoncé (3): Changer 'a' et trouver la meilleure conception

**Objectif:** Pour L et R fixés, varier 'a' pour minimiser le coût

**Procédure:**

```python
L = 3.0
R = 0.010

meilleure_conception = None
cout_min = float('inf')

# Varier a de 30 à 60 mm
for a in np.arange(0.030, 0.061, 0.001):  # Pas de 1 mm

    # Pour chaque a, trouver N_min
    for N in range(30, 121, 5):
        result = solve_heating_baseboard(L, P, h_conv, T_air, k_c, R, a, N)

        if 248 <= result['Tmax'] <= 250:
            if result['cout_total'] < cout_min:
                cout_min = result['cout_total']
                meilleure_conception = {'R': R, 'a': a, 'N': N}
            break
```

**Résultat:** Meilleure valeur de 'a' pour R et L fixés

### Énoncé (4): Changer 'R' et refaire (2) et (3)

**Objectif:** Pour L fixé, varier R puis a, pour minimiser le coût

**Procédure:**

```python
L = 3.0

meilleure_conception_globale = None
cout_min_global = float('inf')

# Varier R de 8 à 20 mm
for R in np.arange(0.008, 0.021, 0.001):

    # Pour chaque R, varier a
    for a in np.arange(0.030, 0.061, 0.001):

        # Pour chaque (R,a), trouver N_min
        for N in range(30, 121, 5):
            result = solve_heating_baseboard(L, P, h_conv, T_air, k_c, R, a, N)

            if 248 <= result['Tmax'] <= 250:
                if result['cout_total'] < cout_min_global:
                    cout_min_global = result['cout_total']
                    meilleure_conception_globale = {'R': R, 'a': a, 'N': N}
                break
```

**Résultat:** Meilleures valeurs de R, a, N pour L fixé

### Énoncé (5): Changer 'L' et refaire tout

**Note:** Dans la plupart des cas, L est fixé par les données de l'équipe. Cette étape peut être ignorée si L est unique pour votre équipe.

---

## PARTIE 3: OPTIMISATION AUTOMATIQUE (run_optimisation_complete.py)

### Pourquoi utiliser ce fichier?

L'approche manuelle (Partie 2) prend énormément de temps. Le fichier `run_optimisation_complete.py` automatise tout le processus et trouve **3 solutions optimales**.

### Étape 3.1: Comprendre les 3 solutions recherchées

**Solution 1 - Précision Température:**
- T_max le plus proche de 248-250°C
- Respecte au mieux la contrainte thermique
- Peut ne pas avoir le coût minimal

**Solution 2 - Coût Minimal:**
- Coût le plus bas possible
- Sous contrainte: 248°C ≤ T_max ≤ 250°C
- **C'est la solution principale demandée par le projet**

**Solution 3 - N Minimal:**
- Nombre d'ailettes minimal
- Sous contrainte: 248°C ≤ T_max ≤ 250°C
- Utile pour la fabrication (moins d'assemblage)

### Étape 3.2: Exécuter l'optimisation complète

**Action:**
```bash
python run_optimisation_complete.py
```

**Ce qui se passe:**

#### PHASE 1: Recherche grossière
- Teste une grille de combinaisons (R, a, N)
- Plages typiques:
  - R: 8 à 20 mm (pas de 2 mm)
  - a: 30 à 60 mm (pas de 5 mm)
  - N: 30 à 120 (pas de 10)
- Identifie les 3 meilleures solutions

#### PHASE 2: Raffinement
- Concentre la recherche autour de la solution à coût minimal
- Plages fines (pas de 1 mm pour R et a, pas de 5 pour N)
- Améliore les 3 solutions

### Étape 3.3: Interpréter les résultats

**Sortie typique:**
```
================================================================================
 🏆 RÉSULTATS FINAUX - 3 SOLUTIONS OPTIMALES
================================================================================

📌 SOLUTION 1: Précision Température
  R = 10.000 mm, a = 36.000 mm, N = 60
  Tmax = 249.15°C, Coût = 7234.56$ ⭐ (déviation = 0.15°C)

💰 SOLUTION 2: Coût Minimal
  R = 9.000 mm, a = 42.000 mm, N = 55
  Tmax = 249.82°C, Coût = 6891.23$ ⭐

🔧 SOLUTION 3: N Minimal
  R = 12.000 mm, a = 38.000 mm, N = 45
  Tmax = 248.56°C, Coût = 7456.78$ ⭐
```

### Étape 3.4: Choix de la solution pour le rapport

**Pour le projet:** Utilisez la **Solution 2 (Coût Minimal)**

C'est celle qui répond directement à l'énoncé: "avoir le coût minimum" tout en respectant T_max ≤ 250±2°C.

---

## CORRESPONDANCE AVEC LES ÉNONCÉS DU PDF

### Énoncé (1): Justifier deux modèles

**Modèle 1 - Workbench (non fourni dans les fichiers Python):**
- À créer séparément dans ANSYS Workbench
- Modèle axisymétrique d'une ailette

**Modèle 2 - Python (mec423_heating_baseboard.py):**
- ✓ Modèle axisymétrique fourni
- ✓ Plans de symétrie: entre ailettes et au milieu de l'épaisseur
- ✓ Conditions frontières: flux et convection
- ✓ Résout et retourne T_max, T_min

**Action:** Dans le rapport, expliquer les deux approches et leurs justifications.

### Énoncé (2): Déterminer N_min

**Comment le faire:**
- Méthode manuelle: voir Partie 2, Énoncé (2)
- Méthode automatique: `run_optimisation_complete.py` le trouve automatiquement

**Dans le rapport:** Montrer un exemple de calcul pour un (R, a) donné.

### Énoncés (3), (4), (5): Optimisation complète

**Comment le faire:**
- Méthode manuelle: voir Partie 2
- **Méthode recommandée:** `run_optimisation_complete.py`

**Dans le rapport:**
- Décrire l'algorithme d'optimisation (Phase 1 + Phase 2)
- Présenter les 3 solutions trouvées
- Justifier le choix de la Solution 2 (coût minimal)

---

## RÉSUMÉ DE LA PROCÉDURE COMPLÈTE

### Pour répondre au projet:

1. **Vérifier vos données uniques** (L, P, h, T_air) dans le Tableau 1 du PDF

2. **Modifier les paramètres** dans `run_optimisation_complete.py`:
   ```python
   L = 3.0      # Votre valeur
   P = 3600     # Votre valeur
   h_conv = 30  # Votre valeur
   T_air = 60   # Votre valeur
   ```

3. **Exécuter l'optimisation:**
   ```bash
   python run_optimisation_complete.py
   ```

4. **Récupérer la Solution 2 (Coût Minimal):**
   - Noter les valeurs: R, a, N
   - Noter: T_max, Coût total

5. **Valider avec le modèle détaillé:**
   ```python
   # Modifier dans mec423_heating_baseboard.py
   R = 0.009  # Valeur trouvée
   a = 0.042  # Valeur trouvée
   N = 55     # Valeur trouvée

   # Exécuter
   python mec423_heating_baseboard.py
   ```

6. **Capturer les graphiques** pour le rapport:
   - Maillage
   - Distribution de température T(r,z)

7. **Vérifier la contrainte:**
   - 248°C ≤ T_max ≤ 250°C ✓

8. **Rédiger le rapport** avec:
   - Description du modèle
   - Méthodologie d'optimisation
   - Résultats (3 solutions)
   - Discussion et conclusion
   - Recommandation: Solution 2

---

## PARAMÈTRES DE MAILLAGE

Les fichiers utilisent des paramètres de maillage optimisés:

```python
nr_tube = 5      # Divisions radiales dans le tube
nr_ailette = 8   # Divisions radiales dans l'ailette
nz_ailette = 3   # Divisions axiales dans l'épaisseur d'ailette
nz_espace = 10   # Divisions axiales entre ailettes
```

**Pour le rapport:** Vous pouvez faire une étude de convergence en augmentant ces valeurs et montrer que les résultats convergent.

---

## FORMULES CLÉS

### Géométrie:
- Rayon intérieur: R_int = R - t₁ où t₁ = R/5
- Épaisseur ailette: t_a = a/100
- Pas entre ailettes: p = L/N

### Conditions frontières:
- Flux intérieur: σᵢ = P / (2π × R_int × L)
- Convection: h, T_air sur surfaces extérieures

### Coût:
- Coût = 2×10⁴ × L × R² + 1000 × N × a × ((R+a)² - R²) + 3 × √N

---

## QUESTIONS FRÉQUENTES

**Q1: Pourquoi 3 solutions?**
R: Pour montrer différentes optimisations possibles. Le projet demande le coût minimal (Solution 2), mais les autres donnent des perspectives intéressantes.

**Q2: Combien de temps prend l'optimisation?**
R: Environ 2-5 minutes selon la puissance de calcul.

**Q3: Puis-je ajuster les plages de recherche?**
R: Oui, modifier les lignes 49-51 dans `run_optimisation_complete.py`

**Q4: Comment vérifier mes résultats?**
R: Exécuter `mec423_heating_baseboard.py` avec les paramètres trouvés et vérifier visuellement la distribution de température.

**Q5: Que faire si aucune solution ne respecte 248-250°C?**
R: Élargir les plages de recherche (R, a, N) dans le fichier d'optimisation.

---

## CHECKLIST POUR LE RAPPORT

- [ ] Données uniques vérifiées (L, P, h, T_air)
- [ ] Modèle Python expliqué (maillage, conditions frontières)
- [ ] Modèle Workbench créé et documenté
- [ ] Méthodologie d'optimisation décrite
- [ ] 3 solutions trouvées et présentées
- [ ] Solution 2 (coût minimal) justifiée comme choix final
- [ ] T_max vérifié: 248°C ≤ T_max ≤ 250°C
- [ ] Graphiques inclus (maillage + température)
- [ ] Coût calculé et présenté
- [ ] Discussion sur les résultats
- [ ] Conclusion claire

---

**Fin de la méthodologie**
