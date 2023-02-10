# -*- coding: utf-8 -*-
"""
La idea de este ejecutable es obtener la curva de After Diversity Maximum Demand promedio
tomando diferentes grupos de carga N veces cada uno, obteniendo su ADMD para finalmente promediar los resultados de esas N estimaciones
"""

# =============================================================================
# Configuracion inicial
# =============================================================================

from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import pickle

#guardar directorio actual
dname=os.getcwd()
#cambiar directorio de trabajo al actual
os.chdir('C:\\Users\\catal\\Desktop\\Paper\\Códigos-Paper\\ADMD')
#Habilitar uso de latex (requiere ProTexT)
from matplotlib import rc 
rc('text',usetex=True)
rc('font',**{'family':'DejaVu Sans','serif': 'Iwona'})
plt.rcParams.update(plt.rcParamsDefault)
lanzamientos=1000 #Fijo (Num simulaciones por grupo)
Adopcion_max=100 #maximo numero de EVs, igual a n° Viviendas (dwellings)
# NumMuestras=int(Adopcion_max/10)+1 #Num de agrupaciones de consumos (para iterar de 10 en 10)
NumMuestras=int(Adopcion_max)#Num de agrupaciones de consumos (para iterar de 1 en 1 en el zoom con 100 cargas)
#%%
# =============================================================================
# Datos de entrada
# =============================================================================

# Perfiles de carga  residencial (N=2000, CREST, W)
# Contiene 2000 perfiles de carga residencial lenta en 144 horas=6 dias
# Perfiles CREST
archivoDwellings=pd.read_csv('../Datos Entrada/PerfilCarga.csv',index_col=False,sep=';')
#Perfiles de carga no coordinada EV lenta (N=2000kW)
#Se genera de cruce de inf: perfil_carga_residencial + tiempos_desconexion)
archivoNoCoordLento=pd.read_csv('../Datos Entrada/InputNoCoordinado10.csv',index_col=False,sep=',')
#Perfil de carga EV NoCoord Rapida (N=2000,KW)

#pedir al usuario parametrizacion
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
#se crea a partir de perfil no coord segun entrada de usuario (parametrizacion inicio, medio o final)
archivoNoCoordRapido=pd.read_csv('../Datos Entrada/InputNoCoordinadoRapido_param_'+parametrizacion_joined_string+'.csv',index_col=False,sep=',')


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
#%%
# =============================================================================
# Procedimiento 
# =============================================================================



# Se marca tiempo inicio simulacion
start=datetime.now()

#Vars para guardar tiempo de simulaxion de conjunto de cargas
start_aux=0
finish_aux=0
i=0
#se itera para cada nivel de adopcion de 1,10,20,30..1000 range(0,Adopcion_max+1,10) o de 1 en 1 (range(1,Adopcion_max+1,1)
for adopcion in range(1,Adopcion_max+1,1):
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
        
        #Calculo preliminar ADMD
        ADMD_EVs_slow[j,i] = max(DemAgrNoCoordinadaLenta)
        ADMD_EVs_fast[j,i] = max(DemAgrNoCoordinadaRapida)
        
        #DemAgregada Residencial
        perfilDemResidencial = archivoDwellings.iloc[:,random_DWs[j]-1]
        DemAgrResidencial = perfilDemResidencial.sum(axis=1)/1000 #(W to Kw) (datos de EV ya estan en KW)
        
        #Calculo preliminar del ADMD
        ADMD_Loads[j,i] = max(DemAgrResidencial)
        
        #Se suman ambas curvas de demanda coincidente y se calcula ADMD conjnto
        DemAgrRes_NoCoordLenta = DemAgrNoCoordinadaLenta + DemAgrResidencial
        DemAgrRes_NoCoordRapida = DemAgrNoCoordinadaRapida + DemAgrResidencial
        
        ADMD_LoadsEVs_slow[j,i] = max(DemAgrRes_NoCoordLenta)
        ADMD_LoadsEVs_fast[j,i] = max(DemAgrRes_NoCoordRapida)
        
        
        # Se actualiza el t_final del grupo
        finish_aux = datetime.now()
        
    #actualiza i     
    i+=1
    
finis=datetime.now()


#%%
# =============================================================================
# Calculo de ADMD final 
# =============================================================================

#Se define el numero de cargas para cada simulacion
NumCargasXcolumna=np.arange(Adopcion_max ) #para que llegue Adopcion maxima de 10 en 10 (np.arange(0,2001,10 )), para que vaya de 1 en 1 np.arange(Adopcion_max )
NumCargasXcolumna[0]=1


#Se divide cada columna del ADMD (preliminar) por el n° de cargas correspondiente

ADMDf_Loads         = ADMD_Loads/NumCargasXcolumna
ADMDf_EVs_slow      = ADMD_EVs_slow/NumCargasXcolumna
ADMDf_LoadsEVs_slow = ADMD_LoadsEVs_slow/NumCargasXcolumna
ADMDf_EVs_fast      = ADMD_EVs_fast/NumCargasXcolumna
ADMDf_LoadsEVs_fast = ADMD_LoadsEVs_fast/NumCargasXcolumna


#%%
# =============================================================================
#  ADMD promedio (ADMDf_prom)
# =============================================================================

# Finalmente, para obtener la curva ADMD promedio, se calcula promedio de cada columna como la suma de cada columna dividido en el Nº de columnas (lanzamientos)
ADMDf_prom_Loads         = (ADMDf_Loads.sum(axis=0)/lanzamientos)
ADMDf_prom_EVs_slow      = (ADMDf_EVs_slow.sum(axis=0)/lanzamientos)
ADMDf_prom_LoadsEVs_slow = (ADMDf_LoadsEVs_slow.sum(axis=0)/lanzamientos)
ADMDf_prom_EVs_fast      = (ADMDf_EVs_fast.sum(axis=0)/lanzamientos)
ADMDf_prom_LoadsEVs_fast = (ADMDf_LoadsEVs_fast.sum(axis=0)/lanzamientos)

ejeX = NumCargasXcolumna

ejeYlenta = [ADMDf_prom_Loads, ADMDf_prom_EVs_slow, ADMDf_prom_LoadsEVs_slow]
ejeYrapida = [ADMDf_prom_Loads, ADMDf_prom_EVs_fast, ADMDf_prom_LoadsEVs_fast]

#%%
""" Cargar archivos """
cargarArchivo=1
if cargarArchivo==1:
    [aux1, aux2] = pickle.load(open(parametrizacion_joined_string+'/Datos ADMD.dat',"rb"))
    ejeYlenta = aux1
    ejeYrapida = aux2

NumCargasXcolumna=np.arange(Adopcion_max ) #para que llegue Adopcion maxima de 10 en 10 (np.arange(0,2001,10 )), para que vaya de 1 en 1 np.arange(Adopcion_max )
NumCargasXcolumna[0]=1
#%%
# =============================================================================
# Analisis
# =============================================================================


texto=["Loads","EVs","Loads+EVs"]

ADMDf_prom_Loads = ejeYlenta[0]
ADMDf_prom_EVs_slow = ejeYlenta[1]
ADMDf_prom_LoadsEVs_slow = ejeYlenta[2]
ADMDf_prom_EVs_fast = ejeYrapida[1]
ADMDf_prom_LoadsEVs_fast = ejeYrapida[2]


ejeX = NumCargasXcolumna

maximoLenta = max(max(ADMDf_prom_Loads),max(ADMDf_prom_EVs_slow),max(ADMDf_prom_LoadsEVs_slow))
maximoRapida = max(max(ADMDf_prom_Loads),max(ADMDf_prom_EVs_fast),max(ADMDf_prom_LoadsEVs_fast))
 
#%%
""" Guardar archivos """

# Save
pickle.dump([ejeYlenta, ejeYrapida], open(parametrizacion_joined_string+'/Datos ADMD.dat',"wb"))

