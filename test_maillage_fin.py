#!/usr/bin/env python3
"""
Test avec un maillage plus raffiné
"""
import numpy as py
from numpy.linalg import solve
import matplotlib
matplotlib.use('Agg')

Resoudre = True
pi = py.pi

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
print(" TEST AVEC MAILLAGE RAFFINÉ")
print("="*70)

# Maillage plus fin
nr_tube = 10      # était 5
nr_ailette = 15   # était 8
nz_ailette = 6    # était 3
nz_espace = 20    # était 10

z_max = pas_ailette / 2

r_tube = py.linspace(R_int, R, nr_tube)
r_ailette_sans_tube = py.linspace(R, R+a, nr_ailette+1)[1:]
r_coords = py.concatenate([r_tube, r_ailette_sans_tube])

z_ailette = py.linspace(0, t_a/2, nz_ailette)
z_espace = py.linspace(t_a/2, z_max, nz_espace+1)[1:]
z_coords = py.concatenate([z_ailette, z_espace])

nz_total = len(z_coords)
nr_total = len(r_coords)
nn_total = nz_total * nr_total

xy = py.zeros((nn_total, 2))
node_id = 0
for iz in range(nz_total):
    for ir in range(nr_total):
        xy[node_id, 0] = r_coords[ir]
        xy[node_id, 1] = z_coords[iz]
        node_id += 1

def get_node_number(ir, iz):
    return iz * nr_total + ir + 1

elements = []
for iz in range(nz_total - 1):
    for ir in range(nr_total - 1):
        n1 = get_node_number(ir, iz)
        n2 = get_node_number(ir+1, iz)
        n3 = get_node_number(ir+1, iz+1)
        n4 = get_node_number(ir, iz+1)
        elements.append([n1, n2, n3])
        elements.append([n1, n3, n4])

cn = py.array(elements)
ne = cn.shape[0]
kc = py.full(ne, k_c)
Q = 0

convection_faces = []
idx_R = py.where(py.isclose(r_coords, R))[0][0]
idx_Ra = py.where(py.isclose(r_coords, R+a))[0][0]
idx_ta2 = py.where(py.isclose(z_coords, t_a/2))[0][0]
idx_0 = 0
idx_zmax = nz_total - 1

for iz in range(idx_ta2, idx_zmax):
    ni = get_node_number(idx_R, iz)
    nj = get_node_number(idx_R, iz+1)
    convection_faces.append([ni, nj, h_conv, T_air])

for ir in range(idx_R, idx_Ra):
    ni = get_node_number(ir, idx_ta2)
    nj = get_node_number(ir+1, idx_ta2)
    convection_faces.append([ni, nj, h_conv, T_air])

for iz in range(idx_0, idx_ta2):
    ni = get_node_number(idx_Ra, iz)
    nj = get_node_number(idx_Ra, iz+1)
    convection_faces.append([ni, nj, h_conv, T_air])

ijhTf = py.array(convection_faces)
nh = ijhTf.shape[0]

sigma_i = P / (2 * pi * R_int * L)

flux_faces = []
idx_Rint = 0
for iz in range(nz_total - 1):
    ni = get_node_number(idx_Rint, iz)
    nj = get_node_number(idx_Rint, iz+1)
    flux_faces.append([ni, nj, sigma_i])

ijflux = py.array(flux_faces)
nflux = ijflux.shape[0]

nn = xy.shape[0]
print(f"Nombre de noeuds: {nn} (vs 169 avant)")
print(f"Nombre d'éléments: {ne} (vs 288 avant)")
print("="*70)

if Resoudre:
    print("\nRésolution en cours...")

    kg = py.zeros((nn, nn))
    fg = py.zeros(nn)

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

        Vi = py.array([xk-xj, yk-yj])
        Vj = py.array([xi-xk, yi-yk])
        Vk = py.array([xj-xi, yj-yi])

        A = 0.5 * ((xj-xi)*(yk-yj) - (yj-yi)*(xk-xj))
        xm = (xi + xj + xk) / 3

        K = 2 * pi * kc[ie] * xm / (4 * abs(A)) * py.array([
            [py.dot(Vi, Vi), py.dot(Vi, Vj), py.dot(Vi, Vk)],
            [py.dot(Vj, Vi), py.dot(Vj, Vj), py.dot(Vj, Vk)],
            [py.dot(Vk, Vi), py.dot(Vk, Vj), py.dot(Vk, Vk)]
        ])

        fV = 2 * pi * Q * abs(A) / 12 * py.array([
            2*xi + xj + xk,
            xi + 2*xj + xk,
            xi + xj + 2*xk
        ])

        ind = py.array([ni-1, nj-1, nk-1])
        ix, iy = py.meshgrid(ind, ind)
        kg[ix, iy] += K
        fg[ix] += fV

    for fi in range(nh):
        ni = int(ijhTf[fi, 0])
        nj = int(ijhTf[fi, 1])
        hij = ijhTf[fi, 2]
        Tfij = ijhTf[fi, 3]

        xi = xy[ni-1, 0]
        yi = xy[ni-1, 1]
        xj = xy[nj-1, 0]
        yj = xy[nj-1, 1]

        Lij = py.sqrt((xj-xi)**2 + (yj-yi)**2)

        H = 2 * pi * Lij * hij / 12 * py.array([
            [3*xi + xj, xi + xj],
            [xi + xj, xi + 3*xj]
        ])

        fh = 2 * pi * Lij * hij * Tfij / 6 * py.array([
            2*xi + xj,
            xi + 2*xj
        ])

        ind = py.array([ni-1, nj-1])
        ix, iy = py.meshgrid(ind, ind)
        kg[ix, iy] += H
        fg[ix] += fh

    for fi in range(nflux):
        ni = int(ijflux[fi, 0])
        nj = int(ijflux[fi, 1])
        sij = ijflux[fi, 2]

        xi = xy[ni-1, 0]
        yi = xy[ni-1, 1]
        xj = xy[nj-1, 0]
        yj = xy[nj-1, 1]

        Lij = py.sqrt((xj-xi)**2 + (yj-yi)**2)

        fs = 2 * pi * Lij * sij / 6 * py.array([
            2*xi + xj,
            xi + 2*xj
        ])

        ind = py.array([ni-1, nj-1])
        fg[ind] += fs

    T = solve(kg, fg)

    Tmax = py.max(T)
    Tmin = py.min(T)

    print("\n" + "="*70)
    print(" RÉSULTATS AVEC MAILLAGE RAFFINÉ")
    print("="*70)
    print(f"  T_max = {Tmax:.2f} °C")
    print(f"  T_min = {Tmin:.2f} °C")
    print(f"\n  Comparaison:")
    print(f"    Ansys:  250.00°C")
    print(f"    Python: {Tmax:.2f}°C")
    print(f"    Écart:  {abs(Tmax-250):.2f}°C")
    print("="*70)
