# Analyse de la différence de température entre Ansys et Python

## Paramètres testés
- R = 10 mm
- a = 34 mm
- N = 60 ailettes
- Autres paramètres: L=3m, P=3600W, h=30 W/(m²·°C), T_air=60°C

## Résultats
- **Ansys**: T_max = 250°C
- **Python**: T_max = 196°C
- **Écart**: 54°C (21.3%)

## Tests effectués

### 1. Ajout du facteur 2π dans toutes les formules
**Résultat**: Aucun changement (196°C)
**Raison**: Le facteur 2π s'annule des deux côtés de l'équation K×T = f

### 2. Raffinement du maillage
- Augmentation du nombre de noeuds de 169 à 650
**Résultat**: Aucun changement significatif (196.83°C)
**Conclusion**: Ce n'est pas un problème de résolution numérique

### 3. Modification de la formule du flux
- Sans 2π: σ_i = P/(R_int×L) → T_max = 920°C (trop élevé)
- Avec 2π: σ_i = P/(2π×R_int×L) → T_max = 196°C (trop bas)

## Hypothèses pour expliquer la différence

### Hypothèse 1: Différence de géométrie modélisée
- **Modèle Ansys**: Probablement une ailette COMPLÈTE (épaisseur ta) + demi-espaces de chaque côté
  - Longueur totale: pas_ailette = L/N
- **Modèle Python**: Demi-ailette (épaisseur ta/2) + demi-espace
  - Longueur totale: pas_ailette/2 = L/(2N)

⚠️ **IMPORTANT**: Les deux modèles ont des géométries DIFFÉRENTES selon le PDF!

### Hypothèse 2: Définition du flux dans Ansys
Le flux dans Ansys pourrait être défini différemment:
- **Heat Flux** (W/m²): Flux par unité de surface → σ = P/(2π×R_int×L)
- **Heat Flow** (W): Puissance totale → Ansys calcule automatiquement le flux

### Hypothèse 3: Conditions aux limites différentes
Les conditions de symétrie ou de convection pourraient être définies différemment.

## Questions à vérifier dans votre modèle Ansys

1. **Géométrie exacte modélisée**:
   - Quelle est la longueur axiale totale de votre modèle?
   - Modélisez-vous une ailette complète ou une demi-ailette?
   - Où sont placés les plans de symétrie?

2. **Définition du flux**:
   - Avez-vous utilisé "Heat Flux" ou "Heat Flow"?
   - Quelle valeur avez-vous entrée exactement?
   - Sur quelle surface le flux est-il appliqué?

3. **Conditions aux limites**:
   - Quelles conditions avez-vous appliquées sur les plans de symétrie?
   - La convection est-elle appliquée sur les mêmes surfaces que le code Python?

4. **Paramètres matériaux**:
   - Conductivité thermique: k = 150 W/(m·°C)?
   - Coefficient de convection: h = 30 W/(m²·°C)?

## Code Python - État actuel

Le code Python utilise la formulation du PDF:
```python
sigma_i = P / (2 * pi * R_int * L)  # W/m²
```

Cette formule est mathématiquement correcte pour un flux uniforme sur toute la longueur L.

## Recommandations

1. **Vérifier le modèle Ansys** avec les questions ci-dessus
2. **Comparer les géométries** exactes des deux modèles
3. **Vérifier que le flux est bien défini comme un Heat Flux** (W/m²) dans Ansys, pas un Heat Flow (W)
4. **S'assurer que les conditions aux limites sont identiques**

## Conclusion provisoire

Je n'ai PAS trouvé d'erreur dans le code Python. Les formules correspondent au PDF et aux équations d'éléments finis axisymétriques. La différence de 54°C (21%) suggère une différence de configuration entre les deux modèles plutôt qu'une erreur de code.

Le problème le plus probable est une différence dans la **définition du flux** ou dans la **géométrie modélisée** entre Ansys et Python.
