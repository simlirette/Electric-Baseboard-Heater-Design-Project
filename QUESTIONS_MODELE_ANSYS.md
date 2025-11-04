# Questions sur le modèle Ansys

## Situation
- **Paramètres testés**: R=10mm, a=36mm, N=60
- **Résultat Ansys**: T_max = 279°C
- **Résultat Python**: T_max = 187°C
- **Écart**: 92°C (33%)

Le flux de chaleur σ_i = 23,873 W/m² est identique dans les deux modèles (confirmé).

## Questions critiques

### 1. Géométrie dans Ansys

Dans votre modèle Ansys:

a) **Quelle est la longueur axiale TOTALE modélisée?**
   - [ ] 25 mm (= pas_ailette/2 = demi-période)
   - [ ] 50 mm (= pas_ailette = période complète)
   - [ ] Autre: _______ mm

b) **Où avez-vous placé les plans de symétrie?**
   - Plan 1: z = _______ mm
   - Plan 2: z = _______ mm

c) **Quelle est l'épaisseur d'ailette modélisée?**
   - [ ] 0.36 mm (= ta = épaisseur complète)
   - [ ] 0.18 mm (= ta/2 = demi-épaisseur)

### 2. Conditions aux limites dans Ansys

a) **Comment avez-vous défini le flux de chaleur?**
   - Type de chargement:
     - [ ] Heat Flux (W/m²)
     - [ ] Heat Flow (W)
     - [ ] Autre: _______

   - Valeur entrée: _______ (avec unités)

   - Sur quelle surface avez-vous appliqué ce flux?
     - [ ] Surface intérieure du tube (r = R_int = 8 mm)
     - [ ] Autre: _______

b) **Avez-vous appliqué des conditions sur les plans de symétrie?**
   - [ ] Oui: quel type? _______
   - [ ] Non (laissées libres)

c) **La convection est-elle appliquée sur les mêmes surfaces que le code Python?**
   - Surface extérieure du tube (r=R, z ∈ [ta/2, pas/2])
   - Surface supérieure de l'ailette (z=ta/2, r ∈ [R, R+a])
   - Extrémité de l'ailette (r=R+a, z ∈ [0, ta/2])

### 3. Type d'analyse

a) **Quel type d'analyse avez-vous utilisé?**
   - [ ] Steady-State Thermal (stationnaire)
   - [ ] Transient Thermal
   - [ ] Autre: _______

b) **Quel type d'élément?**
   - [ ] PLANE55 (2D axisymétrique)
   - [ ] SOLID70 (3D thermique)
   - [ ] Autre: _______

### 4. Vérification du modèle Python

Le modèle Python modélise:
- **Domaine**: r ∈ [8mm, 46mm], z ∈ [0mm, 25mm]
- **Demi-ailette**: z ∈ [0, 0.18mm]
- **Demi-espace**: z ∈ [0.18mm, 25mm]
- **Flux appliqué**: 23,873 W/m² sur r=8mm, pour tout z
- **Convection**: h=30 W/(m²·°C), T_air=60°C sur les surfaces exposées

Est-ce cohérent avec votre modèle Ansys?

## Hypothèses possibles

### Hypothèse 1: Flux défini comme "Heat Flow"
Si vous avez entré le flux comme "Heat Flow = 3600 W" au lieu de "Heat Flux = 23,873 W/m²", alors Ansys applique TOUTE la puissance sur votre portion modélisée, ce qui est incorrect.

Pour une portion représentant 1/(2N) = 1/120 du tube total, la puissance devrait être P/(2N) = 30 W, pas 3600 W.

### Hypothèse 2: Géométrie différente
Si Ansys modélise une période COMPLÈTE (50 mm) au lieu d'une demi-période (25 mm), les conditions aux limites et le flux seraient différents.

### Hypothèse 3: Convection appliquée différemment
Si la convection n'est pas appliquée exactement sur les mêmes surfaces, la dissipation thermique serait différente.

## Action recommandée

Vérifiez point par point votre modèle Ansys avec ces questions. L'écart de 33% suggère une différence de configuration plutôt qu'une erreur de formules mathématiques.

Le code Python est conforme au gabarit fourni et aux consignes PDF.
