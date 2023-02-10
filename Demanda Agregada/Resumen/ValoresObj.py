# -*- coding: utf-8 -*-
"""
Created on Sun Jul 11 19:34:25 2021

@author: catal
"""
# =============================================================================
# Configuracion inicial
# =============================================================================

from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os


#guardar directorio actual
dname=os.getcwd()
#cambiar directorio de trabajo al actual
#cambiar directorio de trabajo al actual
os.chdir('C:\\Users\\catal\\Desktop\\Paper\\Códigos-Paper\\Demanda Agregada\\Resumen')
#Habilitar uso de latex (requiere ProTexT)
from matplotlib import rc
# Habilitar el uso de LaTeX -> Para usar agregar r antes de str ' '
rc('text', usetex=True) # funciona
rc('font', **{'family': 'DejaVu Sans','serif': 'Iwona'}) # 'DejaVu Sans' es mejor que 'serif'


#Habilitar el uso de LaTeX en seaborn 
tex_fonts = {
    # Use LaTeX to write all text
    "text.usetex": True,
    "font.family": "serif",
    # Use 10pt font in plots, to match 10pt font in document
    "axes.labelsize": 10,
    "font.size": 10,
    # Make the legend/label fonts a little smaller
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    
    "ytick.labelsize": 8
}

plt.rcParams.update(tex_fonts)
plt.rcParams.update(plt.rcParamsDefault)
#%%
#se lee hoja con datos de valores objetivos guardados con parametrizacion al inicio

inicio=pd.read_csv('Inicio.csv')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10,5))

#carga no coordinada
no_coordinado=inicio[inicio.Coordinacion=='No coordinada']

X = np.unique(no_coordinado.Adopcion.tolist())

bar1 = ax1.barh(X - 25.00,no_coordinado[no_coordinado.Carga=='Lenta']['Demanda Agregada Promedio'].tolist() , 50, label='Carga Lenta')
bar2 = ax1.barh(X + 25.00,no_coordinado[no_coordinado.Carga=='Rápida']['Demanda Agregada Promedio'].tolist() ,50, label='Carga Rápida')

ax1.set_ylabel('Adopción')
ax1.set_xlabel('Demanda Agregada Promedio [kW]')

ax1.grid(which='major',linestyle='-',alpha=0.7) #alpha = opacidad
ax1.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad


#carga coordinada
coordinado=inicio[inicio.Coordinacion=='Coordinada']
X = np.unique(coordinado.Adopcion.tolist())

bar3 = ax2.barh(X - 25.00,coordinado[coordinado.Carga=='Lenta']['Demanda Agregada Promedio'].tolist() , 50, label='Carga Lenta')
bar4 = ax2.barh(X + 25.00,coordinado[coordinado.Carga=='Rápida']['Demanda Agregada Promedio'].tolist() , 50, label='Carga Rápida')

ax2.set_xlabel('Demanda Agregada Promedio [kW]')
ax2.grid(which='major',linestyle='-',alpha=0.7) #alpha = opacidad
ax2.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = 


fig.legend((bar1,bar2), ('Lenta','Rápida'), 'upper right')
fig.suptitle('Demanda Agregada Promedio por Adopción, Carga y Coordinación', fontsize=16)
fig.tight_layout()
fig.savefig('ValoresObjetivo_inicio.pdf',bbox_inches='tight')
plt.show()


#%%


#se lee hoja con datos de valores objetivos guardados con parametrizacion al medio

medio=pd.read_csv('medio.csv')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10,5))


#carga no coordinada
no_coordinado=inicio[inicio.Coordinacion=='No coordinada']

X = np.unique(no_coordinado.Adopcion.tolist())

bar1 = ax1.barh(X - 25.00,no_coordinado[no_coordinado.Carga=='Lenta']['Demanda Agregada Promedio'].tolist() , 50, label='Carga Lenta')
bar2 = ax1.barh(X + 25.00,no_coordinado[no_coordinado.Carga=='Rápida']['Demanda Agregada Promedio'].tolist() ,50, label='Carga Rápida')

ax1.set_ylabel('EV adoption level',fontsize=14)
ax1.set_xlabel('Average Maximum Aggregate Demand [kW]',fontsize=14)

ax1.grid(which='major',linestyle='-',alpha=1) #alpha = opacidad
ax1.grid(which='minor',linestyle='dashed',alpha=0.5) #alpha = opacidad

# ax1.set_xticklabels([0,200,400,600,800,1000], Fontsize= 12)
ax1.set_yticklabels([0,100,200,300,400,500], fontsize= 12)
ax1.set_xlim([0,1200])
#carga coordinada
coordinado=inicio[inicio.Coordinacion=='Coordinada']
X = np.unique(coordinado.Adopcion.tolist())

bar3 = ax2.barh(X - 25.00,coordinado[coordinado.Carga=='Lenta']['Demanda Agregada Promedio'].tolist() , 50, label='Carga Lenta')
bar4 = ax2.barh(X + 25.00,coordinado[coordinado.Carga=='Rápida']['Demanda Agregada Promedio'].tolist() , 50, label='Carga Rápida')

ax2.set_xlabel('Average Maximum Aggregate Demand [kW]',fontsize=14)
ax2.grid(which='major',linestyle='-',alpha=1) #alpha = opacidad
ax2.grid(which='minor',linestyle='dashed',alpha=0.5) #alpha = 
# ax2.set_xticklabels([0,200,400,600,800,1000], Fontsize= 12)
ax2.set_yticklabels([0,100,200,300,400,500], fontsize= 12)
ax2.set_xlim([0,1200])
fig.legend((bar1,bar2), ('Slow charging','Fast charging'), 'upper right',fontsize=14)
#fig.suptitle('Demanda Agregada Promedio por Adopción, Carga y Coordinación', fontsize=16)
fig.tight_layout()
plt.rc('axes',edgecolor='gray')
fig.savefig('ValoresObjetivo_medio.pdf',bbox_inches='tight')

plt.show()


    #%%


#se lee hoja con datos de valores objetivos guardados con parametrizacion al final

inicio=pd.read_csv('final.csv')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10,5))


#carga no coordinada
no_coordinado=inicio[inicio.Coordinacion=='No coordinada']

X = np.unique(no_coordinado.Adopcion.tolist())

bar1 = ax1.barh(X - 25.00,no_coordinado[no_coordinado.Carga=='Lenta']['Demanda Agregada Promedio'].tolist() , 50, label='Carga Lenta')
bar2 = ax1.barh(X + 25.00,no_coordinado[no_coordinado.Carga=='Rápida']['Demanda Agregada Promedio'].tolist() ,50, label='Carga Rápida')

ax1.set_ylabel('Adopción')
ax1.set_xlabel('Demanda Agregada Promedio [kW]')

ax1.grid(which='major',linestyle='-',alpha=0.7) #alpha = opacidad
ax1.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad


#carga coordinada
coordinado=inicio[inicio.Coordinacion=='Coordinada']
X = np.unique(coordinado.Adopcion.tolist())

bar3 = ax2.barh(X - 25.00,coordinado[coordinado.Carga=='Lenta']['Demanda Agregada Promedio'].tolist() , 50, label='Carga Lenta')
bar4 = ax2.barh(X + 25.00,coordinado[coordinado.Carga=='Rápida']['Demanda Agregada Promedio'].tolist() , 50, label='Carga Rápida')

ax2.set_xlabel('Demanda Agregada Promedio [kW]')
ax2.grid(which='major',linestyle='-',alpha=0.7) #alpha = opacidad
ax2.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = 


fig.legend((bar1,bar2), ('Lenta','Rápida'), 'upper right')
fig.suptitle('Demanda Agregada Promedio por Adopción, Carga y Coordinación', fontsize=16)
fig.tight_layout()
fig.savefig('ValoresObjetivo_final.pdf',bbox_inches='tight')
plt.show()