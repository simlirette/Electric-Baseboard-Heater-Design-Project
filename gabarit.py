import numpy as py
from numpy.linalg import solve
import matplotlib.pyplot as plt
import matplotlib.tri as tri

Resoudre = True # Resoudre = False pour vérifier, Resoudre = True pour résoudre
pi = py.pi # Nombre 3.14159...

# gabarit pour solution avec éléments finis triangulaires axisymétriques
#  1) définir les paramètres du problème (géométrie, matériau, chargement)
#  2) définir les coordonnées des noeuds
#  3) définir les connectivités
#  4) définir les noeuds des facettes avec de la convection
#  5) définir les noeuds des facettes avec un flux de chaleur
#  6) vérifier le maillage (entrer ok=1 quand maillage satisfaisant)
# Si Resoudre = True
#  7) calcul des matrices de conduction et forces de volume pour chaque élément
#  8) assemblage chargement dû à la convection (ijhTf)
#  9) assemblage chargement dû au flux de chaleur (ijflux)
# 10) Solution et visualisation des résultats

## Paramètres facultatifs (géométrie, matériaux, conditions frontières)

## Coordonnées des noeuds
# xy=py.array([[xi, yi],[xj, yj],[ ...]]) 2 coordonnées x et y par noeud

## Connectivités des éléments
#cn=py.array([[i, j, k],[..., ..., ...]]) 3 no de noeuds par ligne de cn

## Propriétés matériaux
# kc = py.array([__, ...]) # une valeur par élément

## Chaleur volumique (W/m3) si la pièce conduit un courant électrique
Q = __

## Frontières de convection ijhTf=py.array([[i, j, h, Tf],[__, __, __, __]])

## Frontières de flux de chaleur ijflux=py.array([[i, j, flux],[__, __, __]])

# Fin des données
# --------------------------------------------------

nn = xy.shape[0] # nombre de noeuds (1 ddl / noeud)
ne= cn.shape[0] # nombre d'éléments
nh = ijhTf.shape[0]
nflux = ijflux.shape[0]

## Visualiser le maillage pour vérifier
plt.figure(1)# hold on, axis equal
for ie in range(0,ne):
    nijk = cn[ie,:]
    xe = xy[nijk-1,0]
    xc = py.mean(xe)
    ye = xy[nijk-1,1]
    yc = py.mean(ye)
    plt.fill(xe,ye,'g',edgecolor='k',linewidth = 0.5)
    plt.text(xc,yc,'%d' % (ie+1))
for i in range(0,nn):
    xi=xy[i,0]
    yi=xy[i,1]
    plt.text(xi,yi,'%d' % (i+1),color='b')

## Visualiser les frontières de convection pour vérifier
for i in range(0,nh):
    ni= int(ijhTf[i,0])-1
    nj =int(ijhTf[i,1])-1
    hc = plt.plot([xy[ni,0],xy[nj,0]],[xy[ni,1],xy[nj,1]],'b',linewidth = 2.5)
s='conv: h = %4.1f W/m²/°C' %ijhTf[i,2] + ', T$_f$ = %4.1f °C' %ijhTf[i,3]
hs = plt.plot([xy[ni,0],xy[nj,0]],[xy[ni,1],xy[nj,1]],'b',linewidth=2.5,label=s)
plt.xlabel('x')

## Visualiser les frontières de flux pour vérifier
for i in range(0,nflux):
    ni=int(ijflux[i,0]-1)
    nj=int(ijflux[i,1]-1)
    hs = plt.plot([xy[ni,0],xy[nj,0]],[xy[ni,1],xy[nj,1]],'r',linewidth=2.5)
s='flux: s = %4.1f W/m²' %ijflux[i,2]
hs = plt.plot([xy[ni,0],xy[nj,0]],[xy[ni,1],xy[nj,1]],'r',linewidth=2.5,label=s)
plt.xlabel('x')
plt.ylabel('y')
plt.axis('equal')
plt.title('maillage: noeuds, éléments et chargement')
plt.legend()
plt.show(block=False)
mngr=plt.get_current_fig_manager()
mngr.window.geometry()
plt.pause(0.5)

if Resoudre:

    # Initialisation
    kg = py.zeros((nn,nn))
    fg = py.zeros(nn)

    # Calcul des matrices de conduction et des charges volumiques
    for ie in range(0,ne):
        ni=cn[ie,0] ; nj=cn[ie,1] ; nk=cn[ie,2]
        xi=xy[ni-1,0]; yi=xy[ni-1,1]
        xj=xy[nj-1,0]; yj=xy[nj-1,1]
        xk=xy[nk-1,0]; yk=xy[nk-1,1]
        Vi=py.array([xk-xj, yk-yj])
        Vj=py.array([xi-xk, yi-yk])
        Vk=py.array([xj-xi, yj-yi])
        A=0.5*((xj-xi)*(yk-yj)-(yj-yi)*(xk-xj))
        xm=(xi+xj+xk)/3
        #K = kc[ie]*xm/4/abs(A)*py.array([[Vi.T@Vi,Vi.T@Vj,Vi.T@Vk],[Vj.T@Vi,Vj.T@Vj,Vj.T@Vk],[Vk.T@Vi,Vk.T@Vj,Vk.T@Vk]])
        K = kc[ie]*xm/4/abs(A)*py.array([[py.dot(Vi,Vi),py.dot(Vi,Vj),py.dot(Vi,Vk)],
                                         [py.dot(Vj,Vi),py.dot(Vj,Vj),py.dot(Vj,Vk)],
                                         [py.dot(Vk,Vi),py.dot(Vk,Vj),py.dot(Vk,Vk)]])
        fV=Q*abs(A)/12*py.array([2*xi +   xj +   xk,
                                 xi + 2*xj +   xk,
                                 xi +   xj + 2*xk])
        # assemblage
        ind=py.array([ni-1, nj-1, nk-1])
        ix,iy = py.meshgrid(ind,ind)
        kg[ix,iy] += K
        fg[ix] += fV

    # Calcul des matrices de convection
    for fi in range(0,nh):
        ni = int(ijhTf[fi,0]); nj = int(ijhTf[fi,1]); hij = ijhTf[fi,2]; Tfij = ijhTf[fi,3]
        xi = xy[ni-1,0]; yi = xy[ni-1,1]
        xj = xy[nj-1,0]; yj = xy[nj-1,1]
        Lij = py.sqrt((xj-xi)**2+(yj-yi)**2)
        H = Lij*hij/12*py.array([[3*xi+xj,xi+  xj],
                                 [  xi+xj,xi+3*xj]])
        fh = Lij*hij*Tfij/6*py.array([2*xi+  xj,
                                        xi+2*xj])
        # assemblage
        ind = py.array([ni-1,nj-1])
        ix,iy = py.meshgrid(ind,ind)
        kg[ix,iy] += H
        fg[ix] += fh

    # Calcul des matrices de flux de chaleur
    for fi in range(0,nflux):
        ni = int(ijflux[fi,0]); nj = int(ijflux[fi,1]); sij = ijflux[fi,2];
        xi = xy[ni-1,0]; yi = xy[ni-1,1]
        xj = xy[nj-1,0]; yj = xy[nj-1,1]
        Lij = py.sqrt((xj-xi)**2+(yj-yi)**2)
        fs=Lij*sij/6*py.array([2*xi+  xj,
                                 xi+2*xj])

        # assemblage
        ind=py.array([ni-1,nj-1])
        ix,iy = py.meshgrid(ind,ind)
        fg[ix] += fs

    T = solve(kg,fg)
    plt.figure(2);
    # hold on, axis equal, set(2,'Position',[680+300   558-200   560   420])
    #colormap jet
    noeud_x = xy[:,0]
    noeud_y = xy[:,1]
    triangulation = tri.Triangulation(noeud_x,noeud_y,cn-1)
    plt.tricontourf(triangulation, T, cmap = 'jet')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('distribution de température: T(x,y)')
    Tmax = max(T)
    j = py.where(T == Tmax)
    s='$T_{max}$ = %5.2f °C' %Tmax
    plt.text(xy[j,0],xy[j,1],s)
    Tmin = min(T)
    j = py.where(T == Tmin)
    s='$T_{min}$ = %5.2f °C' %Tmin
    plt.text(xy[j,0],xy[j,1],s)
    for ie in range(0,ne):
        nijk=cn[ie,:]
        xe=xy[nijk-1,0]
        xc = py.mean(xe)
        ye = xy[nijk-1,1]
        plt.fill(xe,ye,color=(1,1,1,0.0),edgecolor='k',linewidth = 0.5)

    plt.colorbar()
    plt.axis('equal')
    mngr=plt.get_current_fig_manager()
    mngr.window.geometry("+750+200")
    plt.show()