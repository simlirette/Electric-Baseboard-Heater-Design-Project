# Optimisation de la Plinthe Chauffante Électrique

## Projet MEC423 - Équipe 10

---

## 📋 Données du Projet

**Paramètres fixes:**
- Longueur du tube: **L = 3.0 m**
- Puissance à dissiper: **P = 3.6 kW**
- Coefficient de convection: **h = 30 W/(m²·°C)**
- Température de l'air: **T_air = 60 °C**
- Conductivité thermique: **k_c = 150 W/(m·°C)**

**Contrainte de conception:**
- Température maximale permise: **T_max ≤ 250°C**

**Fonction objectif (à minimiser):**
```
Coût = 2·10⁴·L·R² + 1000·N·a·((R+a)² - R²) + 3·√N  [$]
     = Coût tube + Coût ailettes + Coût assemblage
```

**Variables de conception:**
- **R**: Rayon extérieur du tube [m] (précision: 0.001 m)
- **a**: Longueur radiale des ailettes [m] (précision: 0.001 m)
- **N**: Nombre total d'ailettes (précision: 5 ailettes)

---

## 🎯 Solution Optimale Trouvée

### Variables de conception optimales:

| Variable | Valeur | Description |
|----------|--------|-------------|
| **R** | **12.000 mm** | Rayon extérieur du tube |
| **a** | **40.000 mm** | Longueur radiale des ailettes |
| **N** | **55** | Nombre total d'ailettes |

### Performances thermiques:

| Métrique | Valeur | Statut |
|----------|--------|--------|
| **T_max** | **249.62 °C** | ✅ Respecte la contrainte |
| **Marge de sécurité** | **0.38 °C** | Très proche de l'optimum |
| **T_min** | ~140 °C (approx.) | - |

### Coûts détaillés:

| Composant | Coût | Pourcentage |
|-----------|------|-------------|
| **Tube** | **8.64 $** | 23.7% |
| **Ailettes** | **5.63 $** | 15.4% |
| **Assemblage** | **22.25 $** | 60.9% |
| **TOTAL** | **36.52 $** | 100% |

> **Note importante:** Le coût d'assemblage (3·√N) représente plus de 60% du coût total, ce qui explique pourquoi la solution optimale tend vers un nombre d'ailettes relativement faible (N=55) tout en respectant la contrainte thermique.

---

## 📊 Analyse de Sensibilité

### Sensibilité par rapport à R (a=40mm, N=55):

| R [mm] | T_max [°C] | Coût [$] | Valide? |
|--------|------------|----------|---------|
| 10.8 | 265.67 | 34.67 | ❌ |
| 11.4 | 257.29 | 35.57 | ❌ |
| **12.0** | **249.62** | **36.52** | ✅ |
| 12.6 | 242.59 | 37.51 | ✅ |
| 13.2 | 236.10 | 38.55 | ✅ |

**Interprétation:**
- ⬇️ Diminuer R → Diminue le coût MAIS augmente T_max (risque de dépasser 250°C)
- ⬆️ Augmenter R → Diminue T_max MAIS augmente le coût
- **R=12mm** est le minimum qui respecte la contrainte thermique

### Sensibilité par rapport à a (R=12mm, N=55):

| a [mm] | T_max [°C] | Coût [$] | Valide? |
|--------|------------|----------|---------|
| 36.0 | 261.71 | 35.17 | ❌ |
| 38.0 | 255.43 | 35.81 | ❌ |
| **40.0** | **249.62** | **36.52** | ✅ |
| 42.0 | 244.24 | 37.29 | ✅ |
| 44.0 | 239.23 | 38.13 | ✅ |

**Interprétation:**
- ⬇️ Diminuer a → Diminue la surface d'échange → Augmente T_max
- ⬆️ Augmenter a → Améliore le refroidissement MAIS augmente le coût
- **a=40mm** est le minimum qui respecte la contrainte thermique

### Sensibilité par rapport à N (R=12mm, a=40mm):

| N | T_max [°C] | Coût [$] | Valide? |
|---|------------|----------|---------|
| 49 | 265.19 | 34.66 | ❌ |
| 51 | 259.72 | 35.29 | ❌ |
| 54 | 252.05 | 36.22 | ❌ |
| 57 | 244.95 | 37.13 | ✅ |
| 60 | 238.37 | 38.02 | ✅ |

**Interprétation:**
- ⬇️ Diminuer N → Réduit la surface totale d'échange → Augmente T_max
- ⬆️ Augmenter N → Améliore le refroidissement MAIS augmente le coût (surtout l'assemblage: 3·√N)
- **N=55** est dans la zone limite acceptable (proche de la contrainte)

---

## 🔧 Utilisation du Code

### Fichiers principaux:

1. **`mec423_heating_baseboard.py`**: Module de base contenant la fonction de résolution thermique par éléments finis
2. **`optimisation_plinthe.py`**: Code d'optimisation principal

### Exécution:

```bash
python optimisation_plinthe.py
```

### Options de configuration:

Dans le fichier `optimisation_plinthe.py`, vous pouvez modifier:

```python
# Ligne 401 - Méthode d'optimisation
methode = 'complete'  # ou 'rapide'
```

- **`'complete'`**: Recherche en 2 phases (grossière + fine) - Recommandé
- **`'rapide'`**: Recherche grossière uniquement (plus rapide mais moins précis)

### Plages de recherche:

```python
# Lignes 75-77
R_min, R_max = 0.008, 0.020    # Rayon tube: 8 à 20 mm
a_min, a_max = 0.020, 0.050    # Longueur ailettes: 20 à 50 mm
N_min, N_max = 20, 100         # Nombre d'ailettes: 20 à 100
```

---

## 📈 Méthodologie d'Optimisation

### Phase 1: Recherche Grossière
- Balayage systématique avec pas large (R: 2mm, a: 5mm, N: 10 ailettes)
- Identification rapide des régions prometteuses
- Filtrage des solutions qui respectent T_max ≤ 250°C

### Phase 2: Recherche Fine
- Raffinement autour des 3 meilleures solutions de la Phase 1
- Balayage avec précision demandée (R: 1mm, a: 1mm, N: 5 ailettes)
- Identification de la solution optimale globale

### Temps d'exécution:
- Phase 1: ~2-3 secondes (~441 tests)
- Phase 2: ~10-15 secondes (~2000 tests)
- **Total: ~15-20 secondes**

---

## 📝 Conclusions

### Points clés:

1. **Solution très contrainte thermiquement**: La T_max (249.62°C) est très proche de la limite (250°C), avec une marge de seulement 0.38°C. Cela indique que la solution est bien optimisée.

2. **Coût dominé par l'assemblage**: Le terme 3·√N représente 60.9% du coût total, ce qui limite le nombre optimal d'ailettes à N=55.

3. **Compromis coût-performance**: Toute réduction des paramètres (R, a, ou N) fait dépasser la contrainte thermique. La solution trouvée est donc le minimum viable.

4. **Robustesse limitée**: La faible marge de sécurité (0.38°C) suggère qu'en pratique, il pourrait être prudent d'augmenter légèrement un des paramètres (par exemple N=60 ou a=41mm) pour plus de robustesse.

### Recommandations:

Pour une conception plus robuste, considérer:
- **Option A**: N = 60 ailettes → T_max = 238.37°C, Coût = 38.02$ (+4.1%)
- **Option B**: a = 42 mm → T_max = 244.24°C, Coût = 37.29$ (+2.1%)
- **Option C**: R = 12.6 mm → T_max = 242.59°C, Coût = 37.51$ (+2.7%)

Ces options offrent une marge de sécurité de 6-12°C pour une augmentation de coût modérée.

---

## 📚 Références

- Projet 1 - MEC423-01-02-03, École de technologie supérieure
- Méthode des éléments finis axisymétriques
- Gabarit fourni: MEC423_T_axisymetrique

---

**Auteur:** Équipe 10 - MEC423-02
**Date:** Novembre 2025
