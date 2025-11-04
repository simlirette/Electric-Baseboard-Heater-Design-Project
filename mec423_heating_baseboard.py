import numpy as py
from numpy.linalg import solve
import matplotlib.pyplot as plt
import matplotlib.tri as tri

# ============================================================================
# PROJET MEC423 - CONCEPTION D'UNE PLINTHE CHAUFFANTE ÉLECTRIQUE
# Modèle axisymétrique avec éléments finis triangulaires
# Basé sur le gabarit fourni - MEC423_T_axisymetrique
# ============================================================================

Resoudre = True  # False pour vérifier maillage, True pour résoudre
pi = py.pi


# ============================================================================
# FONCTION PRINCIPALE DE RÉSOLUTION (pour optimisation)
# ============================================================================

def solve_heating_baseboard(L, P, h_conv, T_air, k_c, R, a, N,
                            nr_tube=5, nr_ailette=8, nz_ailette=3, nz_espace=10,
                            verbose=False, plot_results=False):
    """
    Résout le problème thermique de la plinthe chauffante pour une configuration donnée.

    Paramètres:
        L: Longueur du tube [m]
        P: Puissance à dissiper [W]
        h_conv: Coefficient de convection [W/(m²·°C)]
        T_air: Température de l'air ambiant [°C]
        k_c: Conductivité thermique [W/(m·°C)]
        R: Rayon extérieur du tube [m]
        a: Longueur radiale des ailettes [m]
        N: Nombre total d'ailettes
        nr_tube: Nombre de divisions radiales dans le tube
        nr_ailette: Nombre de divisions radiales dans l'ailette
        nz_ailette: Nombre de divisions axiales dans l'épaisseur d'ailette
        nz_espace: Nombre de divisions axiales entre ailettes
        verbose: Afficher les détails
        plot_results: Afficher les graphiques

    Retourne:
        dict: {
            'Tmax': Température maximale [°C],
            'Tmin': Température minimale [°C],
            'cout_total': Coût total [$],
            'cout_tube': Coût du tube [$],
            'cout_ailettes': Coût des ailettes [$],
            'cout_assemblage': Coût d'assemblage [$],
            'success': True/False,
            'T': Vecteur des températures,
            'xy': Coordonnées des nœuds,
            'cn': Connectivités
        }
    """

    try:
        # --- Paramètres géométriques calculés ---
        t1 = R / 5              # Épaisseur de la paroi du tube [m]
        R_int = R - t1          # Rayon intérieur du tube [m]
        t_a = a / 100           # Épaisseur de l'ailette [m]
        pas_ailette = L / N     # Espacement entre ailettes [m]

        z_max = pas_ailette / 2  # Demi-distance entre ailettes

        # --- Génération du maillage ---
        # Coordonnées radiales (x = r)
        r_tube = py.linspace(R_int, R, nr_tube)
        r_ailette_sans_tube = py.linspace(R, R+a, nr_ailette+1)[1:]
        r_coords_tube = r_tube
        r_coords_ailette = py.linspace(R, R+a, nr_ailette+1)

        # Coordonnées axiales (y = z)
        z_ailette = py.linspace(0, t_a/2, nz_ailette)
        z_espace = py.linspace(t_a/2, z_max, nz_espace+1)[1:]
        z_coords_tube = py.concatenate([z_ailette, z_espace])
        z_coords_ailette = z_ailette

        nr_tube_count = len(r_coords_tube)
        nr_ailette_count = len(r_coords_ailette)
        nz_tube_count = len(z_coords_tube)
        nz_ailette_count = len(z_coords_ailette)

        # Créer la liste de nœuds et une map pour retrouver leur index
        xy_list = []
        node_map = {}
        node_id = 0

        # Zone 1: TUBE
        for iz in range(nz_tube_count):
            for ir in range(nr_tube_count):
                xy_list.append([r_coords_tube[ir], z_coords_tube[iz]])
                node_map[('tube', ir, iz)] = node_id
                node_id += 1

        # Zone 2: AILETTE
        for iz in range(nz_ailette_count):
            for ir in range(nr_ailette_count):
                if not (ir == 0 and iz < nz_ailette_count):
                    xy_list.append([r_coords_ailette[ir], z_ailette[iz]])
                    node_map[('ailette', ir, iz)] = node_id
                    node_id += 1

        xy = py.array(xy_list)
        nn_total = len(xy_list)

        # --- Fonctions pour obtenir les numéros de nœuds ---
        def get_node_tube(ir, iz):
            return node_map[('tube', ir, iz)] + 1

        def get_node_ailette(ir, iz):
            if ir == 0:
                iz_tube = iz
                return node_map[('tube', nr_tube_count-1, iz_tube)] + 1
            else:
                return node_map[('ailette', ir, iz)] + 1

        # --- Création des éléments triangulaires ---
        elements = []

        # Éléments dans le TUBE
        for iz in range(nz_tube_count - 1):
            for ir in range(nr_tube_count - 1):
                n1 = get_node_tube(ir, iz)
                n2 = get_node_tube(ir+1, iz)
                n3 = get_node_tube(ir+1, iz+1)
                n4 = get_node_tube(ir, iz+1)
                elements.append([n1, n2, n3])
                elements.append([n1, n3, n4])

        # Éléments dans l'AILETTE
        for iz in range(nz_ailette_count - 1):
            for ir in range(nr_ailette_count - 1):
                n1 = get_node_ailette(ir, iz)
                n2 = get_node_ailette(ir+1, iz)
                n3 = get_node_ailette(ir+1, iz+1)
                n4 = get_node_ailette(ir, iz+1)
                elements.append([n1, n2, n3])
                elements.append([n1, n3, n4])

        cn = py.array(elements)
        ne = cn.shape[0]

        # --- Propriétés matériaux ---
        kc = py.full(ne, k_c)
        Q = 0

        # --- Frontières de convection ---
        convection_faces = []

        idx_ta2_tube = py.where(py.isclose(z_coords_tube, t_a/2))[0][0]
        idx_zmax_tube = nz_tube_count - 1

        # 1. Surface extérieure du tube
        ir_R = nr_tube_count - 1
        for iz in range(idx_ta2_tube, idx_zmax_tube):
            ni = get_node_tube(ir_R, iz)
            nj = get_node_tube(ir_R, iz+1)
            convection_faces.append([ni, nj, h_conv, T_air])

        # 2. Surface supérieure de l'ailette
        iz_ta2_ailette = nz_ailette_count - 1
        for ir in range(nr_ailette_count - 1):
            ni = get_node_ailette(ir, iz_ta2_ailette)
            nj = get_node_ailette(ir+1, iz_ta2_ailette)
            convection_faces.append([ni, nj, h_conv, T_air])

        # 3. Extrémité de l'ailette
        ir_Ra = nr_ailette_count - 1
        for iz in range(nz_ailette_count - 1):
            ni = get_node_ailette(ir_Ra, iz)
            nj = get_node_ailette(ir_Ra, iz+1)
            convection_faces.append([ni, nj, h_conv, T_air])

        ijhTf = py.array(convection_faces)
        nh = ijhTf.shape[0]

        # --- Frontières de flux ---
        sigma_i = P / (2 * pi * R_int * L)
        flux_faces = []

        ir_Rint = 0
        for iz in range(nz_tube_count - 1):
            ni = get_node_tube(ir_Rint, iz)
            nj = get_node_tube(ir_Rint, iz+1)
            flux_faces.append([ni, nj, sigma_i])

        ijflux = py.array(flux_faces)
        nflux = ijflux.shape[0]

        # --- Résolution ---
        nn = xy.shape[0]
        kg = py.zeros((nn, nn))
        fg = py.zeros(nn)

        # Matrices de conduction
        for ie in range(0, ne):
            ni = cn[ie, 0]
            nj = cn[ie, 1]
            nk = cn[ie, 2]

            xi = xy[ni-1, 0]
            yi = xy[ni-1, 1]
            xj = xy[nj-1, 0]
            yj = xy[nj-1, 1]
            xk = xy[nk-1, 0]
            yk = xy[nk-1, 1]

            Vi = py.array([xk-xj, yk-yj])
            Vj = py.array([xi-xk, yi-yk])
            Vk = py.array([xj-xi, yj-yi])

            A = 0.5 * ((xj-xi)*(yk-yj) - (yj-yi)*(xk-xj))
            xm = (xi + xj + xk) / 3

            K = kc[ie] * xm / 4 / abs(A) * py.array([
                [py.dot(Vi, Vi), py.dot(Vi, Vj), py.dot(Vi, Vk)],
                [py.dot(Vj, Vi), py.dot(Vj, Vj), py.dot(Vj, Vk)],
                [py.dot(Vk, Vi), py.dot(Vk, Vj), py.dot(Vk, Vk)]
            ])

            fV = Q * abs(A) / 12 * py.array([
                2*xi + xj + xk,
                xi + 2*xj + xk,
                xi + xj + 2*xk
            ])

            ind = py.array([ni-1, nj-1, nk-1])
            ix, iy = py.meshgrid(ind, ind)
            kg[ix, iy] += K
            fg[ix] += fV

        # Convection
        for fi in range(0, nh):
            ni = int(ijhTf[fi, 0])
            nj = int(ijhTf[fi, 1])
            hij = ijhTf[fi, 2]
            Tfij = ijhTf[fi, 3]

            xi = xy[ni-1, 0]
            yi = xy[ni-1, 1]
            xj = xy[nj-1, 0]
            yj = xy[nj-1, 1]

            Lij = py.sqrt((xj-xi)**2 + (yj-yi)**2)

            H = Lij * hij / 12 * py.array([
                [3*xi + xj, xi + xj],
                [xi + xj, xi + 3*xj]
            ])

            fh = Lij * hij * Tfij / 6 * py.array([
                2*xi + xj,
                xi + 2*xj
            ])

            ind = py.array([ni-1, nj-1])
            ix, iy = py.meshgrid(ind, ind)
            kg[ix, iy] += H
            fg[ix] += fh

        # Flux
        for fi in range(0, nflux):
            ni = int(ijflux[fi, 0])
            nj = int(ijflux[fi, 1])
            sij = ijflux[fi, 2]

            xi = xy[ni-1, 0]
            yi = xy[ni-1, 1]
            xj = xy[nj-1, 0]
            yj = xy[nj-1, 1]

            Lij = py.sqrt((xj-xi)**2 + (yj-yi)**2)

            fs = Lij * sij / 6 * py.array([
                2*xi + xj,
                xi + 2*xj
            ])

            ind = py.array([ni-1, nj-1])
            fg[ind] += fs

        # Solution
        T = solve(kg, fg)

        # Analyse des résultats
        Tmax = max(T)
        Tmin = min(T)

        # Calcul du coût
        cout_tube = 2e4 * L * R**2
        cout_ailettes = 1000 * N * a * ((R+a)**2 - R**2)
        cout_assemblage = 3 * py.sqrt(N)
        cout_total = cout_tube + cout_ailettes + cout_assemblage

        if verbose:
            print(f"  R={R*1000:.1f}mm, a={a*1000:.1f}mm, N={N:3d} → Tmax={Tmax:.1f}°C, Coût={cout_total:.2f}$")

        # Graphiques si demandé
        if plot_results:
            plt.figure(figsize=(14, 6))

            # Maillage
            plt.subplot(1, 2, 1)
            for ie in range(0, ne):
                nijk = cn[ie, :]
                xe = xy[nijk-1, 0]
                ye = xy[nijk-1, 1]
                plt.fill(xe, ye, 'g', edgecolor='k', linewidth=0.5)
            plt.xlabel('x (rayon r) [m]')
            plt.ylabel('y (axial z) [m]')
            plt.axis('equal')
            plt.title('Maillage')

            # Distribution de température
            plt.subplot(1, 2, 2)
            noeud_x = xy[:, 0]
            noeud_y = xy[:, 1]
            triangulation = tri.Triangulation(noeud_x, noeud_y, cn-1)
            plt.tricontourf(triangulation, T, levels=20, cmap='jet')
            plt.colorbar(label='Température [°C]')
            plt.xlabel('x (rayon r) [m]')
            plt.ylabel('y (axial z) [m]')
            plt.title(f'T(r,z): Tmax={Tmax:.1f}°C')
            plt.axis('equal')
            plt.tight_layout()
            plt.show()

        return {
            'Tmax': Tmax,
            'Tmin': Tmin,
            'cout_total': cout_total,
            'cout_tube': cout_tube,
            'cout_ailettes': cout_ailettes,
            'cout_assemblage': cout_assemblage,
            'success': True,
            'T': T,
            'xy': xy,
            'cn': cn
        }

    except Exception as e:
        if verbose:
            print(f"  R={R*1000:.1f}mm, a={a*1000:.1f}mm, N={N:3d} → ERREUR: {str(e)}")

        return {
            'Tmax': 999,
            'Tmin': 0,
            'cout_total': 999999,
            'cout_tube': 0,
            'cout_ailettes': 0,
            'cout_assemblage': 0,
            'success': False,
            'T': None,
            'xy': None,
            'cn': None
        }

# ============================================================================
# 1) PARAMÈTRES DU PROBLÈME
# ============================================================================

# --- Données du projet (MEC423-02, Équipe 10) ---
L = 3.0      # Longueur du tube [m]
P = 3600     # Puissance à dissiper [W] (3.6 kW)
h_conv = 30  # Coefficient de convection [W/(m²·°C)]
T_air = 60   # Température de l'air ambiant [°C]

# --- Propriétés matériaux ---
k_c = 150    # Conductivité thermique [W/(m·°C)] - tube et ailettes

# --- Variables de conception (à optimiser) ---
R = 0.010    # Rayon extérieur du tube [m] - Test: 10 mm
a = 0.036    # Longueur radiale des ailettes [m] - Test: 36 mm
N = 60       # Nombre total d'ailettes - Test: 60

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
# 2) COORDONNÉES DES NOEUDS - xy = py.array([[xi, yi], [xj, yj], ...])
# ============================================================================

# Domaine:
# - Tube: r ∈ [R_int, R], z ∈ [0, pas_ailette/2]
# - Ailette: r ∈ [R, R+a], z ∈ [0, t_a/2]
# Coordonnée x = r (rayon), y = z (axial)
# z=0: plan de symétrie au milieu de l'ailette
# z=pas_ailette/2: plan de symétrie entre deux ailettes

z_max = pas_ailette / 2  # Demi-distance entre ailettes

# Coordonnées radiales (x = r)
r_tube = py.linspace(R_int, R, nr_tube)
r_ailette_sans_tube = py.linspace(R, R+a, nr_ailette+1)[1:]  # Sans répéter R
r_coords_tube = r_tube
r_coords_ailette = py.linspace(R, R+a, nr_ailette+1)

# Coordonnées axiales (y = z)
# Zone 1: épaisseur d'ailette [0, t_a/2]
z_ailette = py.linspace(0, t_a/2, nz_ailette)
# Zone 2: espace entre ailettes [t_a/2, z_max] (seulement pour le tube)
z_espace = py.linspace(t_a/2, z_max, nz_espace+1)[1:]  # Sans répéter t_a/2
z_coords_tube = py.concatenate([z_ailette, z_espace])
z_coords_ailette = z_ailette

# Génération des nœuds de manière structurée
# On va créer une grille en forme de L:
# - Zone du tube: tous les r_tube × tous les z_coords_tube
# - Zone de l'ailette: tous les r_ailette × tous les z_ailette (sauf r=R déjà dans tube)

nr_tube = len(r_coords_tube)
nr_ailette = len(r_coords_ailette)
nz_tube = len(z_coords_tube)
nz_ailette = len(z_coords_ailette)

# Créer la liste de nœuds et une map pour retrouver leur index
xy_list = []
node_map = {}  # (ir, iz, zone) -> node_id

node_id = 0

# Zone 1: TUBE (r ∈ [R_int, R], z ∈ [0, z_max])
for iz in range(nz_tube):
    for ir in range(nr_tube):
        xy_list.append([r_coords_tube[ir], z_coords_tube[iz]])
        node_map[('tube', ir, iz)] = node_id
        node_id += 1

# Zone 2: AILETTE (r ∈ [R, R+a], z ∈ [0, t_a/2])
for iz in range(nz_ailette):
    for ir in range(nr_ailette):
        # Ne pas dupliquer les nœuds à r=R qui sont déjà dans le tube
        if not (ir == 0 and iz < nz_ailette):  # ir=0 correspond à r=R
            xy_list.append([r_coords_ailette[ir], z_ailette[iz]])
            node_map[('ailette', ir, iz)] = node_id
            node_id += 1

xy = py.array(xy_list)
nn_total = len(xy_list)

print(f"\nGénération du maillage:")
print(f"  Nombre de noeuds: {nn_total}")
print(f"    - Zone tube: {nr_tube} × {nz_tube} = {nr_tube * nz_tube}")
print(f"    - Zone ailette: {nr_ailette} × {nz_ailette} - {nz_ailette} (partage avec tube) = {nr_ailette * nz_ailette - nz_ailette}")

# ============================================================================
# 3) CONNECTIVITÉS DES ÉLÉMENTS - cn = py.array([[i, j, k], [...]])
# ============================================================================

# Fonction pour obtenir le numéro de noeud (base 1) à partir des indices
# Pour la zone du tube
def get_node_tube(ir, iz):
    return node_map[('tube', ir, iz)] + 1  # +1 car numérotation commence à 1

# Pour la zone de l'ailette (en gérant le partage avec le tube à r=R)
def get_node_ailette(ir, iz):
    if ir == 0:  # r=R, nœud partagé avec le tube
        # Trouver l'index correspondant dans z_coords_tube
        iz_tube = iz  # Même index car z_ailette est un sous-ensemble de z_coords_tube
        return node_map[('tube', nr_tube-1, iz_tube)] + 1  # nr_tube-1 = dernier index radial du tube (r=R)
    else:
        return node_map[('ailette', ir, iz)] + 1

# Création des éléments triangulaires
elements = []

# Éléments dans le TUBE: r ∈ [R_int, R], z ∈ [0, z_max]
for iz in range(nz_tube - 1):
    for ir in range(nr_tube - 1):
        # Noeuds du quadrilatère
        n1 = get_node_tube(ir, iz)
        n2 = get_node_tube(ir+1, iz)
        n3 = get_node_tube(ir+1, iz+1)
        n4 = get_node_tube(ir, iz+1)

        # Diviser le quadrilatère en 2 triangles
        elements.append([n1, n2, n3])
        elements.append([n1, n3, n4])

# Éléments dans l'AILETTE: r ∈ [R, R+a], z ∈ [0, t_a/2]
for iz in range(nz_ailette - 1):
    for ir in range(nr_ailette - 1):
        # Noeuds du quadrilatère
        n1 = get_node_ailette(ir, iz)
        n2 = get_node_ailette(ir+1, iz)
        n3 = get_node_ailette(ir+1, iz+1)
        n4 = get_node_ailette(ir, iz+1)

        # Diviser le quadrilatère en 2 triangles
        elements.append([n1, n2, n3])
        elements.append([n1, n3, n4])

cn = py.array(elements)
ne = cn.shape[0]
print(f"  Nombre d'éléments: {ne}")
print(f"    - Zone tube: {2 * (nr_tube-1) * (nz_tube-1)}")
print(f"    - Zone ailette: {2 * (nr_ailette-1) * (nz_ailette-1)}")

# ============================================================================
# 4) PROPRIÉTÉS MATÉRIAUX - kc = py.array([k1, k2, ...])
# ============================================================================

kc = py.full(ne, k_c)  # Conductivité pour tous les éléments

# ============================================================================
# 5) CHALEUR VOLUMIQUE (W/m³)
# ============================================================================

Q = 0  # Pas de génération volumique dans ce problème

# ============================================================================
# 6) FRONTIÈRES DE CONVECTION - ijhTf = py.array([[i, j, h, Tf], [...]])
# ============================================================================

# Surfaces exposées à la convection:
# 1. Surface extérieure du tube: r=R, z ∈ [t_a/2, z_max]
# 2. Surface supérieure de l'ailette: z=t_a/2, r ∈ [R, R+a]
# 3. Extrémité de l'ailette: r=R+a, z ∈ [0, t_a/2]

convection_faces = []

# Trouver les indices dans z_coords_tube pour t_a/2 et z_max
idx_ta2_tube = py.where(py.isclose(z_coords_tube, t_a/2))[0][0]
idx_zmax_tube = nz_tube - 1

# 1. Surface extérieure du tube: r=R (dernier r du tube), z ∈ [t_a/2, z_max]
ir_R = nr_tube - 1  # Dernier indice radial du tube (r=R)
for iz in range(idx_ta2_tube, idx_zmax_tube):
    ni = get_node_tube(ir_R, iz)
    nj = get_node_tube(ir_R, iz+1)
    convection_faces.append([ni, nj, h_conv, T_air])

# 2. Surface supérieure de l'ailette: z=t_a/2, r ∈ [R, R+a]
iz_ta2_ailette = nz_ailette - 1  # Dernier indice axial de l'ailette (z=t_a/2)
for ir in range(nr_ailette - 1):
    ni = get_node_ailette(ir, iz_ta2_ailette)
    nj = get_node_ailette(ir+1, iz_ta2_ailette)
    convection_faces.append([ni, nj, h_conv, T_air])

# 3. Extrémité de l'ailette: r=R+a, z ∈ [0, t_a/2]
ir_Ra = nr_ailette - 1  # Dernier indice radial de l'ailette (r=R+a)
for iz in range(nz_ailette - 1):
    ni = get_node_ailette(ir_Ra, iz)
    nj = get_node_ailette(ir_Ra, iz+1)
    convection_faces.append([ni, nj, h_conv, T_air])

ijhTf = py.array(convection_faces)
nh = ijhTf.shape[0]

# ============================================================================
# 7) FRONTIÈRES DE FLUX - ijflux = py.array([[i, j, flux], [...]])
# ============================================================================

# Flux imposé sur la surface intérieure du tube: r=R_int
# Formule du PDF: σ_i = P / [2π(R-t1)L]
sigma_i = P / (2 * pi * R_int * L)  # [W/m²]

flux_faces = []

# Surface intérieure: r=R_int (premier indice radial du tube), toutes les valeurs de z
ir_Rint = 0  # Premier indice radial du tube
for iz in range(nz_tube - 1):
    ni = get_node_tube(ir_Rint, iz)
    nj = get_node_tube(ir_Rint, iz+1)
    flux_faces.append([ni, nj, sigma_i])

ijflux = py.array(flux_faces)
nflux = ijflux.shape[0]

print(f"\nConditions frontières:")
print(f"  Facettes avec convection: {nh}")
print(f"  Facettes avec flux imposé: {nflux}")
print(f"  Flux de chaleur: σ_i = {sigma_i:.2f} W/m²")
print("="*70)

# ============================================================================
# FIN DES DONNÉES
# ============================================================================

nn = xy.shape[0]  # nombre de noeuds (1 ddl / noeud)
ne = cn.shape[0]  # nombre d'éléments
nh = ijhTf.shape[0]
nflux = ijflux.shape[0]

# ============================================================================
# VISUALISATION DU MAILLAGE POUR VÉRIFICATION
# ============================================================================

plt.figure(1)
for ie in range(0, ne):
    nijk = cn[ie, :]
    xe = xy[nijk-1, 0]
    xc = py.mean(xe)
    ye = xy[nijk-1, 1]
    yc = py.mean(ye)
    plt.fill(xe, ye, 'g', edgecolor='k', linewidth=0.5)
    if ne < 100:  # Numéroter les éléments si pas trop nombreux
        plt.text(xc, yc, '%d' % (ie+1), fontsize=6)

if nn < 200:  # Numéroter les noeuds si pas trop nombreux
    for i in range(0, nn):
        xi = xy[i, 0]
        yi = xy[i, 1]
        plt.text(xi, yi, '%d' % (i+1), color='b', fontsize=6)

# Visualiser les frontières de convection
for i in range(0, nh):
    ni = int(ijhTf[i, 0]) - 1
    nj = int(ijhTf[i, 1]) - 1
    plt.plot([xy[ni, 0], xy[nj, 0]], [xy[ni, 1], xy[nj, 1]],
             'b', linewidth=2.5)
s = 'conv: h = %4.1f W/m²/°C' % ijhTf[0, 2] + ', T$_f$ = %4.1f °C' % ijhTf[0, 3]
plt.plot([xy[ni, 0], xy[nj, 0]], [xy[ni, 1], xy[nj, 1]],
         'b', linewidth=2.5, label=s)

# Visualiser les frontières de flux
for i in range(0, nflux):
    ni = int(ijflux[i, 0] - 1)
    nj = int(ijflux[i, 1] - 1)
    plt.plot([xy[ni, 0], xy[nj, 0]], [xy[ni, 1], xy[nj, 1]],
             'r', linewidth=2.5)
s = 'flux: s = %4.1f W/m²' % ijflux[0, 2]
plt.plot([xy[ni, 0], xy[nj, 0]], [xy[ni, 1], xy[nj, 1]],
         'r', linewidth=2.5, label=s)

plt.xlabel('x (rayon r) [m]')
plt.ylabel('y (axial z) [m]')
plt.axis('equal')
plt.title('maillage: noeuds, éléments et chargement')
plt.legend()
plt.show(block=False)
plt.pause(0.5)

# ============================================================================
# RÉSOLUTION DU PROBLÈME (SI Resoudre = True)
# ============================================================================

if Resoudre:

    print("\nRésolution du problème thermique...")

    # Initialisation
    kg = py.zeros((nn, nn))
    fg = py.zeros(nn)

    # ========================================================================
    # Calcul des matrices de conduction et des charges volumiques
    # ========================================================================

    for ie in range(0, ne):
        ni = cn[ie, 0]
        nj = cn[ie, 1]
        nk = cn[ie, 2]

        xi = xy[ni-1, 0]
        yi = xy[ni-1, 1]
        xj = xy[nj-1, 0]
        yj = xy[nj-1, 1]
        xk = xy[nk-1, 0]
        yk = xy[nk-1, 1]

        Vi = py.array([xk-xj, yk-yj])
        Vj = py.array([xi-xk, yi-yk])
        Vk = py.array([xj-xi, yj-yi])

        A = 0.5 * ((xj-xi)*(yk-yj) - (yj-yi)*(xk-xj))
        xm = (xi + xj + xk) / 3

        # Matrice de conduction élémentaire (axisymétrique)
        # Formule du gabarit: K = kc[ie]*xm/4/abs(A)*...
        K = kc[ie] * xm / 4 / abs(A) * py.array([
            [py.dot(Vi, Vi), py.dot(Vi, Vj), py.dot(Vi, Vk)],
            [py.dot(Vj, Vi), py.dot(Vj, Vj), py.dot(Vj, Vk)],
            [py.dot(Vk, Vi), py.dot(Vk, Vj), py.dot(Vk, Vk)]
        ])

        # Force volumique (si Q ≠ 0)
        # Formule du gabarit: fV = Q*abs(A)/12*py.array([2*xi+xj+xk, ...])
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
    # Calcul des matrices de convection
    # ========================================================================

    for fi in range(0, nh):
        ni = int(ijhTf[fi, 0])
        nj = int(ijhTf[fi, 1])
        hij = ijhTf[fi, 2]
        Tfij = ijhTf[fi, 3]

        xi = xy[ni-1, 0]
        yi = xy[ni-1, 1]
        xj = xy[nj-1, 0]
        yj = xy[nj-1, 1]

        Lij = py.sqrt((xj-xi)**2 + (yj-yi)**2)

        # Matrice de convection (axisymétrique)
        # Formule du gabarit: H = Lij*hij/12*py.array([[3*xi+xj, xi+xj], ...])
        H = Lij * hij / 12 * py.array([
            [3*xi + xj, xi + xj],
            [xi + xj, xi + 3*xj]
        ])

        # Vecteur force de convection
        # Formule du gabarit: fh = Lij*hij*Tfij/6*py.array([2*xi+xj, xi+2*xj])
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
    # Calcul des matrices de flux de chaleur
    # ========================================================================

    for fi in range(0, nflux):
        ni = int(ijflux[fi, 0])
        nj = int(ijflux[fi, 1])
        sij = ijflux[fi, 2]

        xi = xy[ni-1, 0]
        yi = xy[ni-1, 1]
        xj = xy[nj-1, 0]
        yj = xy[nj-1, 1]

        Lij = py.sqrt((xj-xi)**2 + (yj-yi)**2)

        # Vecteur force de flux (axisymétrique)
        # Formule du gabarit: fs = Lij*sij/6*py.array([2*xi+xj, xi+2*xj])
        fs = Lij * sij / 6 * py.array([
            2*xi + xj,
            xi + 2*xj
        ])

        # Assemblage
        ind = py.array([ni-1, nj-1])
        fg[ind] += fs

    # ========================================================================
    # Solution du système d'équations
    # ========================================================================

    T = solve(kg, fg)

    print("Résolution terminée!")

    # ========================================================================
    # Analyse des résultats
    # ========================================================================

    Tmax = max(T)
    Tmin = min(T)
    idx_max = py.where(T == Tmax)[0][0]
    idx_min = py.where(T == Tmin)[0][0]

    print("\n" + "="*70)
    print(" RÉSULTATS DE L'ANALYSE THERMIQUE")
    print("="*70)
    print(f"  Température maximale: T_max = {Tmax:.2f} °C")
    print(f"    Position: r = {xy[idx_max, 0]*1000:.2f} mm, z = {xy[idx_max, 1]*1000:.3f} mm")
    print(f"  Température minimale: T_min = {Tmin:.2f} °C")
    print(f"    Position: r = {xy[idx_min, 0]*1000:.2f} mm, z = {xy[idx_min, 1]*1000:.3f} mm")
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
    # Visualisation des résultats
    # ========================================================================

    plt.figure(2)

    noeud_x = xy[:, 0]
    noeud_y = xy[:, 1]
    triangulation = tri.Triangulation(noeud_x, noeud_y, cn-1)

    plt.tricontourf(triangulation, T, levels=20, cmap='jet')
    plt.xlabel('x (rayon r) [m]')
    plt.ylabel('y (axial z) [m]')
    plt.title('distribution de température: T(r,z)')

    # Marquer Tmax
    j = py.where(T == Tmax)
    s = '$T_{max}$ = %5.2f °C' % Tmax
    plt.text(xy[j, 0], xy[j, 1], s, color='white', fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='red', alpha=0.7))

    # Marquer Tmin
    j = py.where(T == Tmin)
    s = '$T_{min}$ = %5.2f °C' % Tmin
    plt.text(xy[j, 0], xy[j, 1], s, color='black', fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='cyan', alpha=0.7))

    # Tracer les contours des éléments
    for ie in range(0, ne):
        nijk = cn[ie, :]
        xe = xy[nijk-1, 0]
        ye = xy[nijk-1, 1]
        plt.fill(xe, ye, color=(1, 1, 1, 0.0), edgecolor='k', linewidth=0.5)

    plt.colorbar(label='Température [°C]')
    plt.axis('equal')
    plt.tight_layout()
    plt.show()

    print("\nAnalyse terminée. Fermez les fenêtres graphiques pour continuer.")
