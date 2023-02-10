# -*- coding: utf-8 -*-

""" Configuración inicial """
from datetime import datetime 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

#guardar directorio actual
dname=os.getcwd()
#cambiar directorio de trabajo al actual
os.chdir('C:\\Users\\catal\\Desktop\\Paper\\Códigos-Paper\\ADMD')
#Habilitar uso de latex (requiere ProTexT)
from matplotlib import rc 
rc('text',usetex=True)
rc('font',**{'family':'DejaVu Sans','serif': 'Iwona'})
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica"]})
# for Palatino and other serif fonts use:
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Palatino"],
})
plt.rcParams.update(plt.rcParamsDefault)
lanzamientos=1000 #Fijo (Num simulaciones por grupo)
Adopcion_max=100 #maximo numero de EVs, igual a n° Viviendas (dwellings)
NumMuestras=int(Adopcion_max/10)+1 #Num de agrupaciones de consumos (para iterar de 100 en 100)

#%%
# =============================================================================
# Datos de entrada
# =============================================================================

# Perfiles de carga  residencial (N=2000, CREST, W)
# Contiene 2000 perfiles de carga residencial lenta en 144 horas=6 dias
# My Electric Avenue
archivoDwellings=pd.read_csv('../Datos Entrada/PerfilCarga.csv',index_col=False,sep=';')
#Perfiles de carga no coordinada EV lenta (N=2000, se trabaja con los primeros 1700, kW)
#Se genera de cruce de inf: perfil_carga_residencial + tiempos_desconexion)
archivoNoCoordLento=pd.read_csv('../Datos Entrada/InputNoCoordinado10.csv',index_col=False,sep=',')
#Perfil de carga EV NoCoord Rapida (N=1700,KW)

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
parametrizacion_joined_string='medio'
#se crea a partir de perfil no coord lento
archivoNoCoordRapido=pd.read_csv('../Datos Entrada/InputNoCoordinadoRapido_param_'+parametrizacion_joined_string+'.csv',index_col=False,sep=',')

#%%
# =============================================================================
# Procedimiento
# =============================================================================

'''Creación de vectores de iniciacion de vars'''

#Consumos residenciales
ADMD_Loads=np.zeros([lanzamientos,NumMuestras]) #filas (lanzamientos)xcolumnas (N° cargas)
#VEs de carga lenta (3.6 KW)
ADMD_EVs_slow=np.zeros([lanzamientos,NumMuestras])
#Suma de consumos residenciales con VEs de carga lenta
ADMD_LoadsEVs_slow=np.zeros([lanzamientos,NumMuestras])
#VEs de carga rapida (7.2 kw)
ADMD_EVs_fast=np.zeros([lanzamientos,NumMuestras])
#Suma de consumos residenciales con VEs de carga rapida
ADMD_LoadsEVs_fast=np.zeros([lanzamientos,NumMuestras])

Fcoinc_slow = np.zeros([lanzamientos,NumMuestras])
Fcoinc_fast = np.zeros([lanzamientos,NumMuestras])
 

#%%
# Se marca tiempo inicio simulacion
start=datetime.now()

#Vars para guardar tiempo de simulaxion de conjunto de cargas
start_aux=0
finish_aux=0
i=0
#se itera para cada nivel de adopcion de 1,10,20,30..1000
for adopcion in range(0,Adopcion_max+1,10):
    if adopcion==0:
        adopcion = 1 #para que parta desde 1
    print(10*'----')
    print('Tiempo de ejecucion ',finish_aux-start_aux)
    
    #Se actualiza el t_inicial del grupo
    start_aux = datetime.now()
        
    #Etapas que restan del proceso
    print('Procesando etapa: ',i+1,'/'+str(NumMuestras))
    
    
    #Se seleccionan cargas aleatorias en forma matricial 
    #(low,max_number-1,(n_rows,n_cols))
    random_EVS = np.random.randint(1,2000+1,(lanzamientos,adopcion)) 
    random_DWs = np.random.randint(1,2000+1,(lanzamientos,adopcion)) #dwellings
    
    
    #se iteran n° de simulaciones
    for j in range(lanzamientos):
        
        #Por cada simulacion se escoge un perfil aleatorio indexando columnas 
        perfilNoCoorLento = archivoNoCoordLento.iloc[:,random_EVS[j]-1] #se seleccionan numero de perfiles segun nivel de adopcion en fila de simulacion j 
        perfilNoCoorRapido = archivoNoCoordRapido.iloc[:,random_EVS[j]-1]
        
        
        # Obtenemos la demanda coincidente como la suma de las cargas (sumamos cada fila -> intervalo horario)
        DemAgrNoCoordinadaLenta = perfilNoCoorLento.sum(axis=1)
        DemAgrNoCoordinadaRapida = perfilNoCoorRapido.sum(axis=1)
        
        # #Calculo preliminar ADMD
        # ADMD_EVs_slow[j,i] = max(DemAgrNoCoordinadaLenta)
        # ADMD_EVs_fast[j,i] = max(DemAgrNoCoordinadaRapida)
        
        #DemAgregada Residencial
        perfilDemResidencial = archivoDwellings.iloc[:,random_DWs[j]-1]
        DemAgrResidencial = perfilDemResidencial.sum(axis=1)/1000 #(W to Kw) (datos de EV ya estan en KW)
        
        #Calculo preliminar del ADMD
        #ADMD_Loads[j,i] = max(DemAgrResidencial)
        
        #Demandas maximas por usuario
        perfilDemResidencial.columns = perfilNoCoorLento.columns
        DemMax_UsrLenta = (perfilDemResidencial/1000 + perfilNoCoorLento).max()
        perfilDemResidencial.columns = perfilNoCoorRapido.columns
        DemMax_UsrRapida = (perfilDemResidencial/1000 + perfilNoCoorRapido).max()        
        
        
        #Se suman ambas curvas de demanda coincidente  
        DemAgrRes_NoCoordLenta = DemAgrNoCoordinadaLenta + DemAgrResidencial
        DemAgrRes_NoCoordRapida = DemAgrNoCoordinadaRapida + DemAgrResidencial
        
        #Calculo factor de coincidencia
        Fcoinc_slow[j,i] =  100*max(DemAgrRes_NoCoordLenta) / DemMax_UsrLenta.sum()
        Fcoinc_fast[j,i] = 100*max(DemAgrRes_NoCoordRapida) / DemMax_UsrRapida.sum()
        
        #Calculo ADMD
        ADMD_LoadsEVs_slow[j,i] = max(DemAgrRes_NoCoordLenta)
        ADMD_LoadsEVs_fast[j,i] = max(DemAgrRes_NoCoordRapida)
        
        
        # Se actualiza el t_final del grupo
        finish_aux = datetime.now()
        
        
    #actualiza i     
    i+=1
    
finis=datetime.now()

