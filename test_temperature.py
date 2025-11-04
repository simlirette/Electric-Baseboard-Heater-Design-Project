import sys
import numpy as py

# Rediriger vers le code principal avec les paramètres de test
# a=34mm, N=60, R=10mm

# Charger et modifier les paramètres
with open('mec423_heating_baseboard.py', 'r') as f:
    code = f.read()

# Remplacer les paramètres
code = code.replace('R = 0.012', 'R = 0.010')
code = code.replace('a = 0.038', 'a = 0.034')
code = code.replace('N = 65', 'N = 60')

# Exécuter
exec(code)
