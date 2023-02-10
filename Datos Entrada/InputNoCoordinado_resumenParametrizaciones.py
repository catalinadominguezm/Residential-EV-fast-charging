# -*- coding: utf-8 -*-
 
#%%
import pandas as pd
import numpy as np 
from itertools import groupby
import itertools
import random
from copy import deepcopy
import matplotlib.pyplot as plt
# from matplotlib import rc
import os
os.chdir("C:\\Users\\catal\\Desktop\\Paper\\Códigos-Paper\\Datos Entrada")

# Habilitar el uso de LaTeX -> Para usar agregar r antes de str ' '
# rc('text', usetex=True) # funciona
# rc('font', **{'family': 'DejaVu Sans','serif': 'Iwona'}) # 'DejaVu Sans' es mejor que 'serif'


# Perfiles de carga EV lenta    (N=2000)
perfil_lento=pd.read_csv('InputNoCoordinado10.csv')

# My Electric Avenue
archivoDwellings = pd.read_csv('../Datos Entrada/PerfilCarga.csv',index_col=False,sep=';')

#lectura de archivos con parametrizacion inicial-medio-final

df= [pd.read_csv('InputNoCoordinadoRapido_param_inicio.csv'), 
     pd.read_csv('InputNoCoordinadoRapido_param_medio.csv'),
     pd.read_csv('InputNoCoordinadoRapido_param_final.csv')]

#vector con horas del dia de cada perfil con res cada 10min
horas = pd.date_range("00:10",periods=len(df[0]),freq='10min').strftime('%H:%M')


#se calcula demanda agregada viviendas /n° viviendas 
perfilDemResidencial = archivoDwellings
DemAgrResidencial = perfilDemResidencial.sum(axis=1)/1000 #se convierten en kw

#cálculo del area bajo la curva
import numpy as np
from scipy.integrate import trapz, simps
def integrate(x, y):
   sm = 0
   for i in range(1, len(x)):
       h = x[i] - x[i-1]
       sm += h * (y[i-1] + y[i]) / 2

   return sm


"""
SOLO EVs
"""

print(50*"=")
print('Caso EVs+Dwellings')    

ADMD_tiempo = perfil_lento.iloc[:,:2000].sum(axis=1)/2000 


texto=['beginning','middle','end']
fig = plt.figure(0)
plt.plot(horas, ADMD_tiempo.tolist(),  color='black', label='Slow charging',linewidth=2)
ADMDfast_evs=[]
percentage_evs=['--']
change_evs = [np.max(ADMD_tiempo)]
for i in range(3):   
    
    #calculamos el after diversity demand Evs carga lenta  y rapida en cada parametrizacion
    ADMDfast_tiempo = df[i].sum(axis=1)/len(df[i].columns) 
    ADMDfast_evs.append(np.max(ADMDfast_tiempo)) 
    percentage_evs.append(100*(ADMDfast_evs[i]-np.max(ADMD_tiempo))/np.max(ADMD_tiempo))
    change_evs.append(ADMDfast_evs[i])
    print('area bajo la curva '+ texto[i]+ ' '+str(round(integrate(np.arange(len(horas)),ADMDfast_tiempo.tolist()),3)))
    #ploteamos resultados de after diversity demand Evs carga lenta  y rapida 
    plt.plot(horas, ADMDfast_tiempo.tolist(), label='Fast charging, '+texto[i])
    plt.fill_between(horas, ADMDfast_tiempo.tolist(), ADMD_tiempo.tolist(),alpha=0.5)
    # plt.title('ADD de perfil de carga rápida por parametrización considerando solo EVs')
    plt.xlabel('Time interval')
    plt.ylabel('[kW]')
    plt.ylim((0,2.5))
    # plt.ylim([0,2600])
    # plt.axisbelow(True)
    plt.legend()
    plt.xticks(np.arange(144,step=10),rotation=60)
    plt.grid(which='major',linestyle='-',alpha=1)
    plt.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad
    plt.minorticks_on()


plt.show()
aux_Name2 = 'ADD Evs con parametrización resumen '
Name = aux_Name2+'.pdf'
fig.savefig(Name, bbox_inches='tight') # Formato alta calidad # +'gap0'
    

"""
EVs+Dwellings
"""

print(50*"=")
print('Caso EVs+Dwellings')     
 
#calculamos el after diversity demand Evs+Dwellings carga lenta  y rapida 
ADMD_tiempo = perfil_lento.iloc[:,:2000].sum(axis=1)/2000 + DemAgrResidencial/2000
fig = plt.figure(2)
plt.plot(horas, ADMD_tiempo.tolist(), color='black',label='Slow charging',linewidth=2)



ADMDfast_evsDwe=[]
percentage_evsDwe=['--']
change_evsDwe = [np.max(ADMD_tiempo)]
for i in range(3):  
    
    #calculamos el after diversity demand Evs carga lenta  y rapida en cada parametrizacion
    ADMDfast_tiempo = df[i].sum(axis=1)/len(df[i].columns) + DemAgrResidencial/2000
    ADMDfast_evsDwe.append(np.max(ADMDfast_tiempo))
    percentage_evsDwe.append(100*(ADMDfast_evsDwe[i]-np.max(ADMD_tiempo))/np.max(ADMD_tiempo))
    change_evsDwe.append(ADMDfast_evsDwe[i])
    #calculamos area bajo la curva
    print('area bajo la curva '+ texto[i]+ ' '+str(round(integrate(np.arange(len(horas)),ADMDfast_tiempo.tolist()),3)))
    #ploteamos resultados de after diversity demand Evs+Dwellings carga lenta  y rapida 
    plt.plot(horas, ADMDfast_tiempo.tolist(), label='Fast charging '+texto[i])
    plt.fill_between(horas, ADMDfast_tiempo.tolist(),ADMD_tiempo.tolist(), alpha=0.5)
    # plt.title('ADD de perfil de carga rápida por parametrización considerando EVs+Dwellings')
    plt.xlabel('Time interval')
    plt.ylabel('[kW]')
    plt.ylim((0,2.5))
    # plt.ylim([0,2600])
    # plt.axisbelow(True)
    plt.legend()
    plt.xticks(np.arange(144,step=10),rotation=60)
    plt.grid(which='major',linestyle='-',alpha=1)
    plt.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad
    plt.minorticks_on()


plt.show()
aux_Name2 = 'ADD Evs+Dwellings con parametrización resumen '
Name = aux_Name2+'.pdf'
fig.savefig(Name, bbox_inches='tight') # Formato alta calidad # +'gap0'


#TABLA DE DIFERENCIAS ADMD POR PARAMATRIZACION VS ADMD CARGA LENTA SOLO EVS
#AUMENTO PORCENTUAL DEL ADMD AL PASAR DE CARGA LENTA A CARGA RAPIDA X PARAMETRIZACION

diff_table = pd.DataFrame({'Solo EVs': percentage_evs,'Cambio solo EVs': change_evs,'EVs + Dwe':percentage_evsDwe,'Cambio EVs + Dwe': change_evsDwe},index=['caso lento','inicio','medio','final'])
diff_table.to_csv('Tabla-ADMDxParametrizacion.csv')


#Demanda residencial
print('ADMD dwellings '+ str(round(np.max(DemAgrResidencial/2000),3)))
fig = plt.figure(2)
plt.plot(horas, DemAgrResidencial, color='darkblue',linewidth=2)
plt.xlabel('Time interval')
plt.ylabel('[kW]')
plt.title('Dwellings Aggregate Demand')
plt.xticks(np.arange(144,step=10),rotation=60)
plt.grid(which='major',linestyle='-',alpha=1)
plt.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad
plt.minorticks_on()
plt.show()
aux_Name2 = 'Demanda agregada residencial'
Name = aux_Name2+'.pdf'
fig.savefig(Name, bbox_inches='tight') # Formato alta calidad # +'gap0'
