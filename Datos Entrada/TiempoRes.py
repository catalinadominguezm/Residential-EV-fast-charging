# -*- coding: utf-8 -*-
"""
Created on Sat May  8 18:18:02 2021

@author: catal
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc
# Habilitar el uso de LaTeX -> Para usar agregar r antes de str ' '
rc('text', usetex=True) # funciona
rc('font', **{'family': 'DejaVu Sans','serif': 'Iwona'}) # 'DejaVu Sans' es mejor que 'serif'
import os
# Guardamos el directorio actual:
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


perfil_ev=pd.read_csv('Perfiles_EV.csv',header=None)
marks=[]
# for i in range(0,1440,10):
    # for j in range(2000):
        # if df.iloc[i-8][j]<df.iloc[i][j]<df.iloc[i+9][j]: marks.append(i)

#%%
#Cada perfil de carga se separa un sublistas que diferencian los periodos de cargas y los que no
#Ej: [0,0,3.6,3.6,3.6,0,0,0] -----> [[0,0],[3.6,3.6,3.6],[0,0,0]]
df=perfil_ev.iloc[:1439][:]
changed_index=[]
for column in df:
    lista = df[column].tolist()   
    #encontrar indices en donde comienza y termina la carga (cada dos indices hay un ciclo)
    indexes = np.where(np.diff(lista,prepend=np.nan))[0]
    split=[]
    for j in range(len(indexes)-1):
                L=lista[indexes[j]:indexes[j+1]]
                split.append(L)
                
    split.append(lista[indexes[-1]:])   
    changed_index.append(split)
        
#Calculamos el largo de cada sublista de todos los perfiles
len_changed=[[ len(sublista) for sublista in changed_index[i] if len(sublista)>=5 and 3.6 in sublista] for i in range(2000) ]
#Obtenemos el minimo tiempo de resolucion (switch) en c/u de los perfiles
resolucion=[np.min(len_changed[i]) for i in range(2000)]
#Tiempo de resolucion minimo, es el minimo de todos los perfiles
min_resolucion=np.min(resolucion)
min_resolucion=np.where(np.array(resolucion) == np.min(resolucion))[0]

#existen perfiles con tiempo de carga menor a 10 minutos, pero a priori se encuentran en los extremos,
#es decir, comienzo o final del dia. Eso significa que es el remanente de carga que ya se estaba realizando
#el dia anterior o que se sigue el dia posterior => Para la estabilizacion de tiempo resolutivo se contabilizara cada 10 minutos. Si considerará
#una carga efectiva si en un intervalo de 10 minutos se hizo una carga por mas de 5 minutos

#%%
# =============================================================================
# CAMBIO DE TIEMPO DE RESOLUCION DE CARGA A 1O MINUTOS
# =============================================================================
k=0
target=np.zeros((144,2000))

#vector con horas del dia de cada perfil con res cada 1min
horas = pd.date_range("00:10",periods=len(df),freq='1min').strftime('%H:%M')
df['DateTime']=horas

# DateTime type es datetime
df['DateTime'] = df['DateTime'].astype('datetime64')
# df['DateTime'] = df['DateTime']

# Set DateTime column as index
df.set_index('DateTime', inplace=True)
 
resample=[]
row=[]
data=[]
#se recorre cada fila
for i in range(0,len(df),10):
    print(i,' ',end='')
    #se recorre cada perfil 
    for j in  df.columns:
        k=i+10
        #si estamos en los ultimos 10 intervalos del df
        if i==1430:
            k=i+9
        #si se hace una carga en el perfil j por mas de 5 minutos en el intervalo:        
        if df.iloc[i:k][j].sum()>3.6*4:
            charging=3.6
        #si se cargó menos de 5 minutos en el intervalo de 10min del perfil j:
        elif df.iloc[i:k][j].sum()<3.6*5: 
            charging=0
        #se añade la carga del intervalo en 10 min al vector que guarda la carga de todos los perfiles
        row.append(charging)
    
    #despues de iterar todas las columnas se agrega el row al data
    data.append(row)
    # tambien se reinicia el row que guarda los charging
    row=[]
#se pasan datos a csv
resized10=pd.DataFrame(data)
resized10.columns=['EV{}'.format(i) for i in range(1,2001)]
#se guarda como csv
resized10.to_csv('InputNoCoordinado10.csv',index=None)
