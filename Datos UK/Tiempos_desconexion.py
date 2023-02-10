# -*- coding: utf-8 -*-
"""
@author: catalina
"""
##############################################################
#   Lectura y limpieza de datos
##############################################################

import pandas as pd
import numpy as np 
from datetime import timedelta 
from datetime import datetime
import datetime as dt
import os

# Guardamos el directorio actual:
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

#lectura de excel con datos de viajes y tiempos con criterio de distancia >1 milla
viajes = pd.read_excel('Datos_conexion.xlsx',sheet_name='Viajes_maindriver')
#seleccionamos filas con nan
df = viajes
df = df[df.isna().any(axis=1)]
#borramos datos de individuos con Nan en algun dato
viajes_clean = viajes[~viajes.IndividualID.isin(df.IndividualID.tolist())]

#se filtran las filas en que se sale o se llega a casa 
claves = viajes_clean[(viajes_clean.TripPurpFrom_B01ID==23) | (viajes_clean.TripPurpTo_B01ID==23)]
claves=claves.reset_index()
#borramos datos de individuos con tiempo que sale y llega a la casa menor o igual a 10 minutos
ind=[claves.IndividualID[i] for i in range(len(claves)) if ((dt.datetime.combine(dt.date(2021,6,1),claves.TimeEnd[i]) - timedelta(minutes=10)).time())<=claves.TimeStart[i] ]
claves=claves[~claves.IndividualID.isin(ind)]
#se aproximan tiempos de 5minutos a los 10minutos mas cercanos

def timeround10(dt):
    a, b = divmod(round(dt.minute, -1), 60)
    fixed_time='%i:%02i' % ((dt.hour + a) % 24, b)
    return datetime.strptime(fixed_time, '%H:%M').time()

claves.TimeStart=[timeround10(claves.TimeStart.tolist()[i]) for i in range(len(claves))]
claves.TimeEnd=[timeround10(claves.TimeEnd.tolist()[i]) for i in range(len(claves))]

#%%
##############################################################
#    Armar datos de desconexion por cliente
##############################################################

#lista de clientes
clientes=np.unique(claves['IndividualID'].tolist())
#lista de tiempos de desconexion por cliente
tiempos=[]
tiempos_pusuario=[]
individuo=claves.IndividualID
delta = timedelta(minutes=10)

for i in range(len(claves)):
    k=i+1
    #si es la ultima fila del dataframe:
    if i==len(claves)-1:
        k=0 #se guarda asi para evitar el error del siguiente if
    if individuo.tolist()[i]==individuo.tolist()[k]:
        #si en esa fila, el individuo sale de casa
        if claves.TripPurpFrom_B01ID.tolist()[i]==23:
            tiempos.append(claves.TimeStart.tolist()[i])
        #si en esa fila, el individuo regresa a casa
        elif claves.TripPurpTo_B01ID.tolist()[i]==23:
            tiempos.append(claves.TimeEnd.tolist()[i])
            
    #si a la siguiente fila se cambia de usuario (o es la ultima fila del dataframe)
    if individuo.tolist()[i]!=individuo.tolist()[k]:
        #si en esa fila, el individuo sale de casa
        if claves.TripPurpFrom_B01ID.tolist()[i]==23:
            tiempos.append(claves.TimeStart.tolist()[i])
        #si en esa fila, el individuo regresa a casa
        elif claves.TripPurpTo_B01ID.tolist()[i]==23:
            tiempos.append(claves.TimeEnd.tolist()[i])
        #se guarda el vector total de tiempos en que el usuario esta fuera de casa
        tiempos_pusuario.append(tiempos)
        #se reinicia el vector que guarda los tiempos en que el usuario esta fuera de casa
        tiempos=[]
 
tiempos_final=[]     
i=0  
clientes_final=[]
#No consideramos usuarios que solo salgan de casa y no lleguen
#o usuarios que solo lleguen a casa y no salgan 
#eliminamos usuarios con datos inconsistentes (horas de entrada/salida se repiten)
for usuario in tiempos_pusuario:
    if len(usuario)%2==0 and any(usuario.count(x) > 1 for x in usuario)==False:
        tiempos_final.append(usuario)
        clientes_final.append(clientes[i])
    i=1+i
#se arma dataframe con datos de tiempos fuera de casa por persona        
tiempos_desconexion=pd.DataFrame(tiempos_final,columns=None,index=None)


# #se guarda la traspuesta
tiempos_desconexion=tiempos_desconexion.transpose()
tiempos_desconexion.columns=clientes_final
#se añade fila con unos
lista=np.ones(len(clientes_final))
a_series = pd.Series(lista, index = tiempos_desconexion.columns)
tiempos_desconexion = tiempos_desconexion.append(a_series, ignore_index=True)

#escribir y guardar csv 
tiempos_desconexion.to_csv('DesconexionConHoraAjustada.csv',index=None)