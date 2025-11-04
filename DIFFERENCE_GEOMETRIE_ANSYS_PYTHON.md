# Différence de géométrie entre Ansys et Python

## CONFIRMATION DE L'UTILISATEUR

L'utilisateur a confirmé que dans Ansys:
1. ✓ Le type de chargement heat flux est le même
2. ✓ Le flux est appliqué sur toute la surface intérieure
3. ✓ Le type d'élément est axisymétrique
4. ✓ **Une ailette COMPLÈTE est modélisée** (pas une demi-ailette)

## DIFFÉRENCE IDENTIFIÉE

### Modèle Python actuel
```
Domaine: z ∈ [0, pas_ailette/2] = [0, 25 mm] pour N=60
Ailette: z ∈ [0, t_a/2] = [0, 0.18 mm]
Espace: z ∈ [t_a/2, pas_ailette/2] = [0.18 mm, 25 mm]

Géométrie: DEMI-AILETTE
```

### Modèle Ansys (selon confirmation utilisateur)
```
Domaine: z ∈ [0, pas_ailette] = [0, 50 mm] pour N=60 ???
Ailette: z ∈ [?, ? + t_a] avec t_a = épaisseur COMPLÈTE

Géométrie: AILETTE COMPLÈTE
```

## QUESTION CRITIQUE POUR L'UTILISATEUR

Dans votre modèle Ansys, quelle est la **longueur axiale totale** modélisée?

### Option A: Demi-période (comme Python actuel)
```
Domaine axial: z ∈ [0, 25 mm] (pas_ailette/2)
Épaisseur ailette modélisée: t_a = 0.36 mm (épaisseur complète)
Espace modélisé: 25 - 0.36 = 24.64 mm

Symétrie à: z = 0 mm (base de l'ailette)
            z = 25 mm (milieu entre deux ailettes)
```

### Option B: Période complète
```
Domaine axial: z ∈ [0, 50 mm] (pas_ailette)
Épaisseur ailette: t_a = 0.36 mm
Espace total: 50 - 0.36 = 49.64 mm

Symétrie à: z = 0 mm et z = 50 mm
```

## IMPACT SUR LES RÉSULTATS

### Si Ansys utilise Option A (demi-période + ailette complète)
Alors le modèle Python doit être modifié pour modéliser:
- Une ailette d'épaisseur **t_a** (au lieu de t_a/2)
- Sur un domaine [0, pas_ailette/2]

Cette différence d'épaisseur d'ailette change:
- La résistance thermique de l'ailette
- La distribution de température
- La température maximale

### Si Ansys utilise Option B (période complète)
Alors le modèle Python doit être modifié pour modéliser:
- Une période complète [0, pas_ailette]
- Une ailette complète d'épaisseur t_a

## FLUX DE CHALEUR - VÉRIFICATION

### Dans le modèle Python actuel
```python
sigma_i = P / (2 * pi * R_int * L)  # W/m²
        = 3600 / (2 * π * 0.008 * 3.0)
        = 23,873 W/m²
```
Ce flux est appliqué sur **toute** la longueur L = 3 m.

### Répartition sur le domaine modélisé
Le modèle Python modélise une portion représentant:
- Longueur axiale: pas_ailette/2 = L/(2N) = 3/(2×60) = 0.025 m
- Fraction de la longueur totale: 1/(2N) = 1/120

**Important**: Le flux σ_i est le même partout (c'est correct), mais la géométrie qui dissipe ce flux est différente selon si on modélise:
- Une demi-ailette (t_a/2) → moins de surface → moins de dissipation → température plus basse
- Une ailette complète (t_a) → plus de surface → plus de dissipation → température différente

## HYPOTHÈSE SUR LA CAUSE DE LA DIFFÉRENCE

Si Ansys modélise une ailette d'épaisseur t_a = 0.36 mm et que Python modélise une demi-ailette d'épaisseur t_a/2 = 0.18 mm, alors:

1. **Surface de convection différente**: L'ailette complète a ~2× plus de surface exposée
2. **Conduction différente**: Le chemin thermique est différent
3. **Résistance thermique différente**: Une ailette plus épaisse conduit différemment

Cela expliquerait parfaitement l'écart observé:
- Ansys (ailette complète): T_max = 250°C
- Python (demi-ailette): T_max = 196°C
- Écart: 54°C (21%)

## ACTIONS RECOMMANDÉES

1. **VÉRIFIER dans Ansys**: Quelle est l'épaisseur d'ailette réellement modélisée?
   - Si t_a = 0.36 mm → ailette complète
   - Si t_a = 0.18 mm → demi-ailette

2. **VÉRIFIER dans Ansys**: Quelle est la longueur axiale totale du domaine?
   - Si 25 mm → demi-période (comme Python)
   - Si 50 mm → période complète (différent de Python)

3. **ADAPTER le code Python** selon la configuration Ansys confirmée

## MODIFICATION PROPOSÉE DU CODE PYTHON

Si Ansys modélise effectivement une ailette complète sur une demi-période, il faut modifier:

```python
# ACTUEL (demi-ailette)
z_ailette = py.linspace(0, t_a/2, nz_ailette)
z_espace = py.linspace(t_a/2, z_max, nz_espace+1)[1:]

# PROPOSÉ (ailette complète)
z_ailette = py.linspace(0, t_a, nz_ailette)
z_espace = py.linspace(t_a, z_max, nz_espace+1)[1:]
```

Et modifier les conditions aux limites en conséquence.

## QUESTION POUR L'UTILISATEUR

**Pouvez-vous confirmer dans votre modèle Ansys:**
1. La longueur axiale totale du domaine modélisé (en mm)?
2. L'épaisseur de l'ailette modélisée (en mm)?
3. Les coordonnées z des plans de symétrie (s'ils existent)?

Ces informations permettront d'adapter exactement le code Python pour correspondre au modèle Ansys.
