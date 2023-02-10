# -*- coding: utf-8 -*-
"""
""
Este modulo realiza la asociacion entre perfiles de auto disponibles y perfiles de viaje
de las personas
A cada auto se le asigna una persona  
"""
import pandas as pd
from datetime import datetime 
from datetime import timedelta
import datetime as hora
from gurobipy import Model, GRB, quicksum#, abs_, min_#, max_, and_, or_
import gurobipy as gp
import os
import numpy as np
from matplotlib import pyplot
import seaborn as sns

# Guardamos el directorio actual:
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

#Cargamos archivo con horas que las personas estan fuera de casa. Usamos  2000 perfiles random 
df = pd.read_csv('DesconexionConHoraAjustada.csv')
 
#seleccion de 2000 perfiles random
random_DWs=np.random.choice(range(len(df.columns)), 2000, False).tolist()

filtered=[df.columns.tolist()[i] for i in random_DWs]

#Cargamos perfil de carga no coordinada de cada vehiculo electrico de My Electric Avenue (1 si carga, 0 si no)
carga = pd.read_csv('../Datos Entrada/InputNoCoordinado10.csv')/3.6

#Cargamos datos de viaje de cada persona
viajes = pd.read_excel('Datos_conexion.xlsx',sheet_name='Viajes_maindriver')
 
#Cargamos archivo con horas que las personas estan fuera de casa. Usamos los 2000 perfiles random 
desconexion = pd.read_csv('DesconexionConHoraAjustada.csv',usecols=filtered)
 
#Cargamos archivo con datos de tiempos de viaje 
datos_desconexion=pd.read_excel('Datos_conexion.xlsx',sheet_name='Viajes_maindriver')


#%%
##############################################################################
#      Vectores a trabajar
##############################################################################


#vector con horas del dia de cada perfil con resolucion cada 10min
tiempo = pd.date_range("00:10",periods=144,freq='10min').strftime('%H:%M:%S')   
tiempo = [datetime.strptime(date, '%H:%M:%S').time() for date in tiempo]


def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end
   
# matriz que por cada persona marca 1 en las horas que esta fuera de casa
horas_desconexion=[]
k=0
for persona in desconexion:
    #se obtiene lista con horas de salida/llegada a casa de la persona
    rango = desconexion[persona].dropna().unique().tolist()[:-1]
    #se pasan a formato fecha
    rango = [datetime.strptime(date, '%H:%M:%S').time() for date in rango]
    #rangos se asocian de a 2 por cada viaje (primero sale luego llega a casa)
    sub_rangos = np.split(np.array(rango),int(len(rango)/2))
    #se crean intervalos en que está afuera la persona
    intervalos=[]
    """
    por cada intervalo se crea una lista que marca con 1 los minutos del dia
    que estan en ese rango (persona fuera de casa)
    """
    minute_in_intervalo=[]
    for intervalo in sub_rangos:
        #check si intervalo es mayor a 30 minutos
        #calcula diferencia en minutos en el intervalo recorrido
        diff = timedelta(hours=intervalo[1].hour-intervalo[0].hour, minutes=intervalo[1].minute-intervalo[0].minute).total_seconds()/60
        # if diff>30: 
        true_values=[]       
        true_values = [time_in_range(intervalo[0],intervalo[1],minute) for minute in tiempo]
        minute_in_intervalo.append(true_values)
        # else: #deja en falso intervalo menor o igual a 30 minutos
        #     print(k)
        #     k=k+1
        #     minute_in_intervalo.append([False]*144)
    """ las horas de desconexion de la persona sera la suma de las listas que contienen minutos fuera de casa
     Ej: si la persona salio dos veces en 90 minutos se obtendra algo como 
     [0,0,1,1,0,0,0,0,0]+[0,0,0,0,0,0,1,1,0]=[0,0,1,1,0,0,1,1,0]
    """
    horas_desconexion.append([sum(i) for i in zip(*minute_in_intervalo)])
    
#se transforman las horas de desconexion a un csv 
df_horas_desconexion=pd.DataFrame(np.transpose(horas_desconexion))
df_horas_desconexion.columns=desconexion.columns
df_horas_desconexion.index=np.arange(len(tiempo))
df_horas_desconexion.to_csv('DesconexionPorMinuto.csv')



"""obtener distancia de los viajes. El objetivo es tener la distancia de todos los viajes por persona
incluyendo todos los viajes de las personas que se seleccionaron, es decir no solo los viajes de ida 
y vuelta a casa 
"""
#se filtran viajes que pertenecen a las personas que estan en el archivo de horas_desconexion
viajes=datos_desconexion[datos_desconexion.IndividualID.isin(desconexion.columns.astype('int64'))]
# para obtener la suma de distancias por viaje, se agrupa por persona y se suma
distancias=viajes.groupby(by='IndividualID').sum()['TripDistance'].tolist()


#%%
# =============================================================================
#      Problema de optimizacion en gurobi 
# =============================================================================
"""
En este programa a cada vehiculo con su perfil de carga se le asocia una persona segun sus tiempos de desconexion
.Para ello se minimiza el error absoluto entre la energia diaria de la persona y la energia diaria del auto 
"""
#Tiempo
start = datetime.now()
m = Model() 
# m.params.LogToConsole = True # default
# m.Params.TimeLimit=3000
m.params.LogToConsole = True # default
m.params.Presolve = -1       # Default: -1 automatic, 0 off
n_personas=len(desconexion.columns)
n_cars=len(carga.columns)


#definicion de variables
A= m.addVars(n_personas, n_cars, vtype=GRB.BINARY,name="A") # o (range(n), range(T),...)


#energia diaria de cada persona
E_dia_persona=[]
# Nissan leaf: City - Mild Weather	163 Wh/km
# for p in range(n_personas):
grouped = viajes.groupby(by='IndividualID').sum()
for persona in desconexion:
    distancia = grouped.loc[int(persona),'TripDistance']
    E_dia_persona.append(np.round(distancia*0.163,3)) #Kwh/km)
   
#energia diaria de cada auto 
E_dia_car=[carga[ev].sum()*3.6 for ev in carga]

#Funcion objetivo
m.setObjective(quicksum(quicksum(A[p,c]*np.abs(E_dia_persona[p]-E_dia_car[c]) for c in range(n_cars)) for p in range(n_personas) ),GRB.MINIMIZE)    



#Cada auto tiene asociado una sola persona
m.addConstrs(quicksum(A[p,c] for p in range(n_personas))==1 for c in range(n_cars))

#%%            
#Respetar horas de desconexion. Cargar solo cuando la persona esta en casa
for p in range(n_personas):
    #obtener el indice de todas las horas en que esa persona está fuera de casa
    persona = desconexion.columns[p]
    print(p,end='')
    index_NoCarga = df_horas_desconexion[df_horas_desconexion[persona]==1][persona].index.tolist()
    #Se recorre cada auto y por cada auto 
    #Si la persona esta asignada al auto, no se puede cargar (con un margen de 0%)
    m.addConstrs(A[p,c]*carga.iloc[index_NoCarga,c].sum() <= 0 for c in range(n_cars))
#%%
#Se agrega restriccion para que todos los perfiles sean asociados al menos a un auto 

m.addConstrs(quicksum(A[p,c] for c in range(n_cars))>=1 for p in range(n_personas))
# m.addConstr(quicksum(quicksum(A[p,c] for p in range(n_personas)) for c in range(n_cars))==50)
#%%
m.Params.TimeLimit=3000
m.optimize()

#%%
# # =============================================================================
# # OPTIMIZACION DEL MODELO 
# # =============================================================================
# m.optimize()


# =============================================================================
#      Imprimir Resultados
# =============================================================================

#Comprobar que cada auto tenga asociada una sola persona
for c in range(n_cars):
    print(quicksum(A[p,c].X for p in range(n_personas)),"   ",end=" ")
    # print(50*"-")
    
print(80*"=")
#Comprobar que cada persona tiene asociado al menos un auto 
for p in range(n_personas):
    print(quicksum(A[p,c].X for c in range(n_cars)), "    ", end="  ")
#saber qué persona se le asignó a cada auto y contar numero de personas asignadas
n=[]
asignacion=[]
for c in range(n_cars):
    for p in range(n_personas):
        if A[p,c].x==1:
            print("Auto ", carga.columns[c], " Se le asigna la persona ", desconexion.columns[p])
            n.append(desconexion.columns[p])
            asignacion.append({'auto':carga.columns[c],'persona':desconexion.columns[p]})
    
print(20*"=")           
print("Se asignaron ",len(np.unique(n)), " personas")


#%%

"""Se guarda csv de HoraAjustada con datos de desconexion optimizados para cada vehiculo
    Cada vehiculo tiene un horario de desconexion segun la persona que se le asigno  """
desconexion_auto=[]
for c in range(n_cars):
    #persona que se asigno al auto c 
    persona=asignacion[c]['persona']
    #se busca persona en df con horas de desconexion por persona
    horas_persona=desconexion[persona].tolist()
    #se agregan horas de desconexion a lista
    desconexion_auto.append(horas_persona)
    
#se pasan datos de desconexion_auto a dataframe
DFdesconexion_auto=pd.DataFrame(np.transpose(desconexion_auto))
#se renombran columnas de acuerdo al numero de vehiculo eb lectrico 
DFdesconexion_auto.columns=['EV{}'.format(i) for i in range(len(DFdesconexion_auto.columns))]
  
#se guarda dataframe como csv 
DFdesconexion_auto.to_csv('DesconexionAuto.csv',index=None)  

#%%

"""
Desconexion por auto se guardan horas segun indice de vector tiempo de res 10min 
Este es el csv final que se usa en optimizacion de gurobi 

"""
from datetime import datetime, timedelta
import os
# Guardamos el directorio actual:
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
         
por_hora=pd.read_csv('DesconexionAuto.csv')
tiempo = np.arange(datetime(2020,7,1,0,10,0), datetime(2020,7,2,0,10,0), timedelta(minutes=10)).astype(datetime)
tiempo2=[x.time() for x in tiempo]

columnas=por_hora.columns
for k in  range(len(columnas)): # num cols
    for j in range(len(por_hora)): # num rows
        if por_hora[columnas[k]][j]=='1.0' or por_hora[columnas[k]][j] != por_hora[columnas[k]][j]:
            break
        else: 
            date1=datetime.strptime(por_hora[columnas[k]][j], '%H:%M:%S').time()
            por_hora[columnas[k]][j]=tiempo2.index(date1)
    
por_hora.to_csv('DesconexionAuto_indice.csv')


"""
Intervalos de infactibilidad de carga para viajes consecutivos con delta inferior a 30 minutos
Se guarda csv como input para intervalos de carga factible de la optimizacion
"""

from datetime import timedelta
por_hora = por_hora.iloc[:-1,:]
por_hora = pd.DataFrame(np.sort(por_hora.values, axis=0), index=por_hora.index, columns=por_hora.columns)

infactibles =  pd.DataFrame(np.nan, index=np.arange(int(len(por_hora)/2)), columns=por_hora.columns)
#se recorre cada EV
for k in range(len(columnas)):
    #se verifica que haya realizado mas de un viaje (cada viaje se cuenta como el intervalo entre la hora de salida y de llegada)
    trips = int(por_hora[columnas[k]].count()/2)
    if trips>1:
        #recorremos hasta el trip n-1 (de a dos filas)
        i=0
        for j in range(2,2*trips,2):
            enter_1 = por_hora.iloc[j-1,k] #datos viaje 1
            exit_2 = por_hora.iloc[j,k]  #datos viaje 2
            # diff = delta_2 -delta_1
            diff = exit_2 - enter_1 
             
            #si la diferencia es menor o igual a 30 minutos, se agrega como periodo de carga infactible
            if diff<=3:
                infactibles.iloc[i,k]=enter_1
                infactibles.iloc[i+1,k]=exit_2
                i=i+2
infactibles.to_csv('Horas_infactibles.csv')



