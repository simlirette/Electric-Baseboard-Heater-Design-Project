import numpy as py
from numpy.linalg import solve
import matplotlib.pyplot as plt
import matplotlib.tri as tri

# ============================================================================
# PROJET MEC423 - CONCEPTION D'UNE PLINTHE CHAUFFANTE ÉLECTRIQUE
# Modèle axisymétrique avec éléments finis triangulaires
# ============================================================================

Resoudre = True  # False pour vérifier maillage, True pour résoudre
pi = py.pi

# ============================================================================
# 1) PARAMÈTRES DU PROBLÈME
# ============================================================================

# --- Données du projet (À MODIFIER selon votre équipe - Tableau 1) ---
L = 3      # Longueur du tube [m] - Exemple: MEC423-01, Équipe 1
P = 3600     # Puissance à dissiper [W] - Exemple: 3.0 kW
h_conv = 30  # Coefficient de convection [W/(m²·°C)]
T_air = 60   # Température de l'air ambiant [°C]

# --- Propriétés matériaux ---
k_c = 150    # Conductivité thermique [W/(m·°C)] - tube et ailettes

# --- Variables de conception (à optimiser) ---
R = 0.012    # Rayon extérieur du tube [m] - Exemple: 20 mm
a = 0.038    # Longueur radiale des ailettes [m] - Exemple: 25 mm
N = 65       # Nombre total d'ailettes - Exemple: 50

# --- Paramètres géométriques calculés ---
t1 = R / 5              # Épaisseur de la paroi du tube [m]
R_int = R - t1          # Rayon intérieur du tube [m]
t_a = a / 100           # Épaisseur de l'ailette [m]
pas_ailette = L / N     # Espacement entre ailettes [m]

# --- Paramètres de maillage ---
nr_tube = 5      # Nombre de divisions radiales dans le tube
nr_ailette = 8   # Nombre de divisions radiales dans l'ailette
nz_ailette = 3   # Nombre de divisions axiales dans l'épaisseur d'ailette
nz_espace = 10   # Nombre de divisions axiales entre ailettes

# --- Affichage des paramètres ---
print("="*70)
print(" PROJET MEC423 - PLINTHE CHAUFFANTE ÉLECTRIQUE")
print("="*70)
print(f"\nDonnées du projet:")
print(f"  Longueur tube L = {L} m")
print(f"  Puissance P = {P/1000} kW")
print(f"  Convection h = {h_conv} W/(m²·°C)")
print(f"  Température air T_air = {T_air} °C")
print(f"\nVariables de conception:")
print(f"  Rayon tube R = {R*1000:.1f} mm")
print(f"  Longueur ailettes a = {a*1000:.1f} mm")
print(f"  Nombre d'ailettes N = {N}")
print(f"\nGéométrie calculée:")
print(f"  Rayon intérieur R_int = {R_int*1000:.2f} mm")
print(f"  Épaisseur paroi t1 = {t1*1000:.2f} mm")
print(f"  Épaisseur ailette t_a = {t_a*1000:.3f} mm")
print(f"  Pas entre ailettes = {pas_ailette*1000:.2f} mm")
print("="*70)

# ============================================================================
# 2) GÉNÉRATION DU MAILLAGE - COORDONNÉES DES NOEUDS
# ============================================================================

# Domaine: z ∈ [0, pas_ailette/2], r ∈ [R_int, R+a]
# z=0: plan de symétrie au milieu de l'ailette
# z=pas_ailette/2: plan de symétrie entre deux ailettes

z_max = pas_ailette / 2  # Demi-distance entre ailettes

# Création des coordonnées r (radiales)
r_tube = py.linspace(R_int, R, nr_tube)
r_ailette_sans_tube = py.linspace(R, R+a, nr_ailette+1)[1:]  # Sans répéter R
r_coords = py.concatenate([r_tube, r_ailette_sans_tube])

# Création des coordonnées z (axiales)
# Zone 1: épaisseur d'ailette [0, t_a/2]
z_ailette = py.linspace(0, t_a/2, nz_ailette)
# Zone 2: espace entre ailettes [t_a/2, z_max]
z_espace = py.linspace(t_a/2, z_max, nz_espace+1)[1:]  # Sans répéter t_a/2
z_coords = py.concatenate([z_ailette, z_espace])

# Génération de la grille de noeuds
nz_total = len(z_coords)
nr_total = len(r_coords)
nn_total = nz_total * nr_total

# Initialisation du tableau de coordonnées
xy = py.zeros((nn_total, 2))

# Remplissage (x=r, y=z en coordonnées axisymétriques)
node_id = 0
for iz in range(nz_total):
    for ir in range(nr_total):
        xy[node_id, 0] = r_coords[ir]  # coordonnée radiale (r)
        xy[node_id, 1] = z_coords[iz]  # coordonnée axiale (z)
        node_id += 1

print(f"\nMaillage généré:")
print(f"  Nombre de noeuds: {nn_total}")

# ============================================================================
# 3) CONNECTIVITÉS DES ÉLÉMENTS
# ============================================================================

# Fonction pour obtenir le numéro de noeud à partir des indices (ir, iz)
def get_node_number(ir, iz):
    return iz * nr_total + ir + 1  # +1 car numérotation commence à 1

# Création des éléments triangulaires
elements = []

for iz in range(nz_total - 1):
    for ir in range(nr_total - 1):
        # Noeuds du quadrilatère
        n1 = get_node_number(ir, iz)
        n2 = get_node_number(ir+1, iz)
        n3 = get_node_number(ir+1, iz+1)
        n4 = get_node_number(ir, iz+1)
        
        # Diviser le quadrilatère en 2 triangles
        elements.append([n1, n2, n3])
        elements.append([n1, n3, n4])

cn = py.array(elements)
ne = cn.shape[0]
print(f"  Nombre d'éléments: {ne}")

# ============================================================================
# 4) PROPRIÉTÉS MATÉRIAUX
# ============================================================================

kc = py.full(ne, k_c)  # Conductivité pour tous les éléments

# ============================================================================
# 5) CHALEUR VOLUMIQUE (si applicable)
# ============================================================================

Q = 0  # Pas de génération volumique dans ce cas

# ============================================================================
# 6) CONDITIONS FRONTIÈRES - CONVECTION
# ============================================================================

# Surfaces exposées à la convection:
# 1. Surface extérieure du tube: r=R, z ∈ [t_a/2, z_max]
# 2. Surface supérieure de l'ailette: z=t_a/2, r ∈ [R, R+a]
# 3. Extrémité de l'ailette: r=R+a, z ∈ [0, t_a/2]

convection_faces = []

# Trouver les indices correspondants
idx_R = py.where(py.isclose(r_coords, R))[0][0]
idx_Ra = py.where(py.isclose(r_coords, R+a))[0][0]
idx_ta2 = py.where(py.isclose(z_coords, t_a/2))[0][0]
idx_0 = 0
idx_zmax = nz_total - 1

# 1. Surface extérieure tube: r=R, z ∈ [t_a/2, z_max]
for iz in range(idx_ta2, idx_zmax):
    ni = get_node_number(idx_R, iz)
    nj = get_node_number(idx_R, iz+1)
    convection_faces.append([ni, nj, h_conv, T_air])

# 2. Surface supérieure ailette: z=t_a/2, r ∈ [R, R+a]
for ir in range(idx_R, idx_Ra):
    ni = get_node_number(ir, idx_ta2)
    nj = get_node_number(ir+1, idx_ta2)
    convection_faces.append([ni, nj, h_conv, T_air])

# 3. Extrémité ailette: r=R+a, z ∈ [0, t_a/2]
for iz in range(idx_0, idx_ta2):
    ni = get_node_number(idx_Ra, iz)
    nj = get_node_number(idx_Ra, iz+1)
    convection_faces.append([ni, nj, h_conv, T_air])

ijhTf = py.array(convection_faces)
nh = ijhTf.shape[0]
print(f"\nConditions frontières:")
print(f"  Facettes avec convection: {nh}")

# ============================================================================
# 7) CONDITIONS FRONTIÈRES - FLUX DE CHALEUR
# ============================================================================

# Flux imposé sur la surface intérieure du tube: r=R_int
# Formule: σ_i = P / [2π(R-t1)L]
sigma_i = P / (2 * pi * R_int * L)  # [W/m²]

print(f"  Flux de chaleur imposé: σ_i = {sigma_i:.2f} W/m²")

flux_faces = []

# Surface intérieure: r=R_int, toutes les valeurs de z
idx_Rint = 0  # Premier indice radial
for iz in range(nz_total - 1):
    ni = get_node_number(idx_Rint, iz)
    nj = get_node_number(idx_Rint, iz+1)
    flux_faces.append([ni, nj, sigma_i])

ijflux = py.array(flux_faces)
nflux = ijflux.shape[0]
print(f"  Facettes avec flux imposé: {nflux}")

# ============================================================================
# VISUALISATION DU MAILLAGE ET VÉRIFICATION
# ============================================================================

nn = xy.shape[0]
ne = cn.shape[0]

plt.figure(1, figsize=(10, 8))

# Tracer les éléments
for ie in range(ne):
    nijk = cn[ie, :]
    xe = xy[nijk-1, 0]
    xc = py.mean(xe)
    ye = xy[nijk-1, 1]
    yc = py.mean(ye)
    plt.fill(xe, ye, 'lightgreen', edgecolor='k', linewidth=0.3)

# Numéroter quelques éléments (pas tous pour éviter surcharge)
if ne < 100:
    for ie in range(0, ne, max(1, ne//50)):
        nijk = cn[ie, :]
        xe = xy[nijk-1, 0]
        xc = py.mean(xe)
        ye = xy[nijk-1, 1]
        yc = py.mean(ye)
        plt.text(xc, yc, '%d' % (ie+1), fontsize=6, ha='center')

# Numéroter quelques noeuds
if nn < 200:
    for i in range(0, nn, max(1, nn//50)):
        xi = xy[i, 0]
        yi = xy[i, 1]
        plt.text(xi, yi, '%d' % (i+1), color='b', fontsize=6)

# Visualiser les frontières de convection
for i in range(nh):
    ni = int(ijhTf[i, 0]) - 1
    nj = int(ijhTf[i, 1]) - 1
    plt.plot([xy[ni, 0], xy[nj, 0]], [xy[ni, 1], xy[nj, 1]], 
             'b', linewidth=2.5, alpha=0.7)

s = f'Convection: h={h_conv} W/m²/°C, T_air={T_air}°C'
plt.plot([], [], 'b', linewidth=2.5, label=s)

# Visualiser les frontières de flux
for i in range(nflux):
    ni = int(ijflux[i, 0]) - 1
    nj = int(ijflux[i, 1]) - 1
    plt.plot([xy[ni, 0], xy[nj, 0]], [xy[ni, 1], xy[nj, 1]], 
             'r', linewidth=2.5, alpha=0.7)

s = f'Flux: σ={sigma_i:.1f} W/m²'
plt.plot([], [], 'r', linewidth=2.5, label=s)

plt.xlabel('r (rayon) [m]')
plt.ylabel('z (axial) [m]')
plt.axis('equal')
plt.title('Maillage: noeuds, éléments et conditions frontières')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show(block=False)
plt.pause(1)

print("\nVérifiez le maillage dans la Figure 1.")
print("Appuyez sur Entrée pour continuer vers la résolution...")
input()

# ============================================================================
# RÉSOLUTION DU PROBLÈME THERMIQUE
# ============================================================================

if Resoudre:
    
    print("\nRésolution en cours...")
    
    # Initialisation des matrices globales
    kg = py.zeros((nn, nn))
    fg = py.zeros(nn)
    
    # ========================================================================
    # 8) CALCUL DES MATRICES DE CONDUCTION
    # ========================================================================
    
    for ie in range(ne):
        ni = cn[ie, 0]
        nj = cn[ie, 1]
        nk = cn[ie, 2]
        
        xi = xy[ni-1, 0]
        yi = xy[ni-1, 1]
        xj = xy[nj-1, 0]
        yj = xy[nj-1, 1]
        xk = xy[nk-1, 0]
        yk = xy[nk-1, 1]
        
        # Vecteurs pour le calcul de la matrice de rigidité
        Vi = py.array([xk-xj, yk-yj])
        Vj = py.array([xi-xk, yi-yk])
        Vk = py.array([xj-xi, yj-yi])
        
        # Aire de l'élément
        A = 0.5 * ((xj-xi)*(yk-yj) - (yj-yi)*(xk-xj))
        
        # Rayon moyen (pour axisymétrique)
        xm = (xi + xj + xk) / 3
        
        # Matrice de conduction élémentaire (axisymétrique)
        K = kc[ie] * xm / (4 * abs(A)) * py.array([
            [py.dot(Vi, Vi), py.dot(Vi, Vj), py.dot(Vi, Vk)],
            [py.dot(Vj, Vi), py.dot(Vj, Vj), py.dot(Vj, Vk)],
            [py.dot(Vk, Vi), py.dot(Vk, Vj), py.dot(Vk, Vk)]
        ])
        
        # Force volumique (si Q ≠ 0)
        fV = Q * abs(A) / 12 * py.array([
            2*xi + xj + xk,
            xi + 2*xj + xk,
            xi + xj + 2*xk
        ])
        
        # Assemblage
        ind = py.array([ni-1, nj-1, nk-1])
        ix, iy = py.meshgrid(ind, ind)
        kg[ix, iy] += K
        fg[ix] += fV
    
    # ========================================================================
    # 9) ASSEMBLAGE CHARGEMENT DÛ À LA CONVECTION
    # ========================================================================
    
    for fi in range(nh):
        ni = int(ijhTf[fi, 0])
        nj = int(ijhTf[fi, 1])
        hij = ijhTf[fi, 2]
        Tfij = ijhTf[fi, 3]
        
        xi = xy[ni-1, 0]
        yi = xy[ni-1, 1]
        xj = xy[nj-1, 0]
        yj = xy[nj-1, 1]
        
        # Longueur de la facette
        Lij = py.sqrt((xj-xi)**2 + (yj-yi)**2)
        
        # Matrice de convection (axisymétrique)
        H = Lij * hij / 12 * py.array([
            [3*xi + xj, xi + xj],
            [xi + xj, xi + 3*xj]
        ])
        
        # Vecteur force de convection
        fh = Lij * hij * Tfij / 6 * py.array([
            2*xi + xj,
            xi + 2*xj
        ])
        
        # Assemblage
        ind = py.array([ni-1, nj-1])
        ix, iy = py.meshgrid(ind, ind)
        kg[ix, iy] += H
        fg[ix] += fh
    
    # ========================================================================
    # 10) ASSEMBLAGE CHARGEMENT DÛ AU FLUX DE CHALEUR
    # ========================================================================
    
    for fi in range(nflux):
        ni = int(ijflux[fi, 0])
        nj = int(ijflux[fi, 1])
        sij = ijflux[fi, 2]
        
        xi = xy[ni-1, 0]
        yi = xy[ni-1, 1]
        xj = xy[nj-1, 0]
        yj = xy[nj-1, 1]
        
        # Longueur de la facette
        Lij = py.sqrt((xj-xi)**2 + (yj-yi)**2)
        
        # Vecteur force de flux (axisymétrique)
        fs = Lij * sij / 6 * py.array([
            2*xi + xj,
            xi + 2*xj
        ])
        
        # Assemblage
        ind = py.array([ni-1, nj-1])
        fg[ind] += fs
    
    # ========================================================================
    # 11) RÉSOLUTION DU SYSTÈME D'ÉQUATIONS
    # ========================================================================
    
    T = solve(kg, fg)
    
    print("Résolution terminée!")
    
    # ========================================================================
    # 12) ANALYSE DES RÉSULTATS
    # ========================================================================
    
    Tmax = py.max(T)
    Tmin = py.min(T)
    idx_max = py.argmax(T)
    idx_min = py.argmin(T)
    
    print("\n" + "="*70)
    print(" RÉSULTATS DE L'ANALYSE THERMIQUE")
    print("="*70)
    print(f"  Température maximale: T_max = {Tmax:.2f} °C")
    print(f"    Position: r = {xy[idx_max, 0]*1000:.2f} mm, z = {xy[idx_max, 1]*1000:.2f} mm")
    print(f"  Température minimale: T_min = {Tmin:.2f} °C")
    print(f"    Position: r = {xy[idx_min, 0]*1000:.2f} mm, z = {xy[idx_min, 1]*1000:.2f} mm")
    print(f"\n  Critère de conception: T_max ≤ 250°C")
    
    if Tmax <= 250:
        print(f"  ✓ RESPECTÉ (marge: {250-Tmax:.2f} °C)")
    else:
        print(f"  ✗ NON RESPECTÉ (dépassement: {Tmax-250:.2f} °C)")
    
    # Calcul du coût
    cout_tube = 2e4 * L * R**2
    cout_ailettes = 1000 * N * a * ((R+a)**2 - R**2)
    cout_assemblage = 3 * py.sqrt(N)
    cout_total = cout_tube + cout_ailettes + cout_assemblage
    
    print(f"\n  COÛT DE LA CONCEPTION:")
    print(f"    Coût tube:       {cout_tube:.2f} $")
    print(f"    Coût ailettes:   {cout_ailettes:.2f} $")
    print(f"    Coût assemblage: {cout_assemblage:.2f} $")
    print(f"    COÛT TOTAL:      {cout_total:.2f} $")
    print("="*70)
    
    # ========================================================================
    # 13) VISUALISATION DES RÉSULTATS
    # ========================================================================
    
    plt.figure(2, figsize=(12, 8))
    
    noeud_x = xy[:, 0]
    noeud_y = xy[:, 1]
    triangulation = tri.Triangulation(noeud_x, noeud_y, cn-1)
    
    # Contours de température
    contour = plt.tricontourf(triangulation, T, levels=20, cmap='jet')
    
    # Tracer les éléments (contours)
    for ie in range(ne):
        nijk = cn[ie, :]
        xe = xy[nijk-1, 0]
        ye = xy[nijk-1, 1]
        plt.fill(xe, ye, color=(1, 1, 1, 0.0), edgecolor='k', linewidth=0.3)
    
    # Annotations
    plt.plot(xy[idx_max, 0], xy[idx_max, 1], 'r*', markersize=15, 
             label=f'T_max = {Tmax:.2f}°C')
    plt.plot(xy[idx_min, 0], xy[idx_min, 1], 'b*', markersize=15, 
             label=f'T_min = {Tmin:.2f}°C')
    
    plt.xlabel('r (rayon) [m]')
    plt.ylabel('z (axial) [m]')
    plt.title(f'Distribution de température: T(r,z)\nR={R*1000:.1f}mm, a={a*1000:.1f}mm, N={N}')
    plt.colorbar(contour, label='Température [°C]')
    plt.axis('equal')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.show()
    
    print("\nAnalyse terminée. Fermez les fenêtres graphiques pour continuer.")
