# -*- coding: utf-8 -*-
"""
 
@author: catal

En este script se transforman los datos de perfiles de carga lenta no coordinados
a perfiles de carga rápida no coordinados
"""

#%%
import pandas as pd
import numpy as np 
from itertools import groupby
import itertools
import random
from copy import deepcopy
import matplotlib.pyplot as plt
from matplotlib import rc
# Habilitar el uso de LaTeX -> Para usar agregar r antes de str ' '
rc('text', usetex=True) # funciona
rc('font', **{'family': 'DejaVu Sans','serif': 'Iwona'}) # 'DejaVu Sans' es mejor que 'serif'


# Perfiles de carga EV lenta    (N=2000)
# perfil_lento=pd.read_csv('InputNoCoordinado10.csv')
res = 10
perfil_lento=pd.read_csv('InputNoCoordinado10.csv')
# My Electric Avenue
archivoDwellings = pd.read_csv('PerfilCarga.csv',index_col=False,sep=';')

changed_index = []
values = {0.0}
# #pedir al usuario parametrizacion
# print('Ingresar lista de parametrizaciones')
# print(5*'--------------')
# print('Opciones: inicio medio final ')
# input_string=input('Ingresar elementos de la lista separados por espacio: ')
# print("\n")
# user_list = input_string.split()
# # print list
# print('lista ingresada: ', user_list)
# lista_parametrizacion = user_list 
# parametrizacion_joined_string = ",".join(lista_parametrizacion)
parametrizacion_joined_string = 'medio'
lista_parametrizacion = ['medio']
#%%
#Cada perfil de carga se separa un sublistas que diferencian los periodos de cargas y los que no
#Ej: [0,0,3.6,3.6,3.6,0,0,0] -----> [[0,0],[3.6,3.6,3.6],[0,0,0]]
for column in perfil_lento:
    lista = perfil_lento[column].tolist()   
    #encontrar indices en donde comienza y termina la carga (cada dos indices hay un ciclo)
    indexes = np.where(np.diff(lista,prepend=np.nan))[0]
    split=[]
    for j in range(len(indexes)-1):
                L=lista[indexes[j]:indexes[j+1]]
                split.append(L)
                
    split.append(lista[indexes[-1]:])   
    changed_index.append(split)

#%%
perfil_fast=[]

#se recorre cada perfil de carga en changed_index
for column in changed_index:

    #column se copia a otra lista para no alterar la original
    perfil = deepcopy(column)  
    #se recorre cada sublista dentro del perfil en cuestion     
    for sublist in perfil:
        #sublista se copia a otra lista para no alterar la original
        carga = sublist
        
        if 3.6 in carga:
            #se escoge parametrizacion aleatoria para el periodo de carga
            parametrizacion = random.choice(lista_parametrizacion)
            if parametrizacion == 'inicio':
                #si la sublista es par, perfil rapido es la mitad exacta del lento
                if len(carga)%2 == 0:
                    mitad = int(len(carga)/2)
                    carga[:mitad] = [7.2 for j in range(len(carga[:mitad]))]
                    carga[mitad:] = [0.0 for j in range(len(carga[mitad:]))]
                #si el delta t de carga es impar, perfil rapido es random de mitad+1 o mitad-1 del lento
                else:           
                    mitad = random.choice([int(len(carga)/2),int(len(carga)/2)+1])
                    carga[:mitad] = [7.2 for j in range(len(carga[:mitad]))]
                    carga[mitad:] = [0.0 for j in range(len(carga[mitad:]))]
                    
            elif parametrizacion == 'medio':
                mitad = int(len(carga)/2)
                sub_mitad = int(mitad/2)
                carga[:]=[0.0 for j in carga]                   
                if len(carga)%2==0 and sub_mitad%2==0:  
                    carga[mitad-sub_mitad:mitad+sub_mitad]=[7.2 for 
                                                               j in range(len( carga[mitad-sub_mitad:mitad+sub_mitad]))]                  
                else: 
                     carga[mitad-sub_mitad:mitad+sub_mitad+1]=[7.2
                                                                  for j in range(len( carga[mitad-sub_mitad:mitad+sub_mitad+1]))]                                              
            elif parametrizacion == 'final':
                if len(carga)%2==0:
                    mitad = int(len(carga)/2)
                    carga[mitad:] = [7.2 for i in range(len(carga[mitad:]))]
                    carga[:mitad] = [0.0 for i in range(len(carga[:mitad]))]
                #si la carga es impar, perfil rapido es random de mitad+1 o mitad-1 del lento
                else:           
                    mitad = random.choice([int(len(carga)/2),int(len(carga)/2)+1])
                    carga[mitad:] = [7.2 for i in range(len(carga[mitad:]))]
                    carga[:mitad] = [0.0 for i in range(len(carga[:mitad]))]
                
    
    #sublistas a lista
    fast = [item for sublist in perfil for item in sublist]
    perfil_fast.append(fast)
    
#%%    
#armar y exportar csv con datos de carga rapida con los 2000 perfiles
df = pd.DataFrame({'EV{}'.format(k+1):perfil_fast[k] for k in range(2000)})
 
df.to_csv('InputNoCoordinadoRapido_param_'+parametrizacion_joined_string +'.csv',index=False) 
#%%
#leer datos para graficar

df=pd.read_csv('InputNoCoordinadoRapido_param_'+parametrizacion_joined_string +'.csv')


#vector con horas del dia de cada perfil con res cada 10min
horas = pd.date_range("00:10",periods=len(df),freq='10min').strftime('%H:%M')

#ploteamos resultados de demanda agregada
fig = plt.figure(0)
plt.plot(horas,df.sum(axis=1), color = 'b')#, label='\% Carga rápida')
plt.plot(horas,perfil_lento.iloc[:,:2000].sum(axis=1), color = 'g')#, label='\% Carga lenta')
plt.title('Demanda agregada de perfil de carga rápida con parametrización uniforme '+parametrizacion_joined_string)
plt.xlabel('Intervalo horario')
plt.ylabel('[kW]')
plt.ylim((0,3500))
# plt.ylim([0,2600])
# plt.axisbelow(True)
plt.legend(labels=[' Carga rápida', ' Carga lenta'])
plt.xticks(np.arange(144,step=10),rotation=60)
plt.grid(which='major',linestyle='-',alpha=1)
plt.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad
plt.minorticks_on()
plt.show()
aux_Name2 = 'Demanda agregada con parametrización uniforme de '+ parametrizacion_joined_string 
Name = aux_Name2+'.pdf'
fig.savefig(Name, bbox_inches='tight') # Formato alta calidad # +'gap0'

#%%


perfilDemResidencial = archivoDwellings
DemAgrResidencial = perfilDemResidencial.sum(axis=1)/1000 #se convierten en kw

#calculamos el after diversity demand Evs carga lenta  y rapida 
ADMD_tiempo = perfil_lento.iloc[:,:2000].sum(axis=1)/2000 
ADMDfast_tiempo = df.sum(axis=1)/len(df.columns) 


#ploteamos resultados de after diversity demand Evs carga lenta  y rapida 
fig = plt.figure(1)
plt.plot(horas, ADMD_tiempo.tolist(), color = 'b')#, label='\% Carga rápida')
plt.plot(horas, ADMDfast_tiempo.tolist(), color = 'g')#, label='\% Carga lenta')
plt.title('ADD de perfil de carga rápida con parametrización uniforme '+parametrizacion_joined_string)
plt.xlabel('Intervalo horario')
plt.ylabel('[kW]')
plt.ylim((0,2.5))
# plt.ylim([0,2600])
# plt.axisbelow(True)
plt.legend(labels=[' Carga rápida', ' Carga lenta'])
plt.xticks(np.arange(144,step=10),rotation=60)
plt.grid(which='major',linestyle='-',alpha=1)
plt.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad
plt.minorticks_on()
plt.show()
aux_Name2 = 'ADD Evs con parametrización uniforme de '+ parametrizacion_joined_string 
Name = aux_Name2+'.pdf'
fig.savefig(Name, bbox_inches='tight') # Formato alta calidad # +'gap0'



#calculamos el after diversity demand Evs+Dwellings carga lenta  y rapida 
ADMD_tiempo = perfil_lento.iloc[:,:2000].sum(axis=1)/2000 +DemAgrResidencial/2000
ADMDfast_tiempo = df.sum(axis=1)/len(df.columns) + DemAgrResidencial/2000


#ploteamos resultados de after diversity demand Evs+Dwellings carga lenta  y rapida 
fig = plt.figure(2)
plt.plot(horas, ADMD_tiempo.tolist(), color = 'b')#, label='\% Carga rápida')
plt.plot(horas, ADMDfast_tiempo.tolist(), color = 'g')#, label='\% Carga lenta')
plt.title('ADD de perfil de carga rápida con parametrización uniforme '+parametrizacion_joined_string)
plt.xlabel('Intervalo horario')
plt.ylabel('[kW]')
plt.ylim((0,2.5))
# plt.ylim([0,2600])
# plt.axisbelow(True)
plt.legend(labels=[' Carga rápida', ' Carga lenta'])
plt.xticks(np.arange(144,step=10),rotation=60)
plt.grid(which='major',linestyle='-',alpha=1)
plt.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad
plt.minorticks_on()
plt.show()
aux_Name2 = 'ADD Evs+Dwe con parametrización uniforme de '+ parametrizacion_joined_string 
Name = aux_Name2+'.pdf'
fig.savefig(Name, bbox_inches='tight') # Formato alta calidad # +'gap0'
