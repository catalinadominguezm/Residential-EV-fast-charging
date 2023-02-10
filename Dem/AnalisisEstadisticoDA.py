# -*- coding: utf-8 -*-
"""
  
La idea de este script es centralizar el estudio de planes de carga lenta y rápida en un solo programa.
Utiliza las funciones OptimizadoDA y OptimizaorDAfastChg, en donde se plantea el problema de optimización que es resuelto en Gurobi.
"""
# =============================================================================
# Configuracion Inicial
# =============================================================================
from datetime import datetime 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
#cambiar directorio de trabajo al actual
os.chdir('C:\\Users\\catal\\Desktop\\Paper\\Códigos-Paper\\Demanda Agregada')
from my_plot import set_size
import seaborn as sns

# # Guardamos el directorio actual:
# abspath = os.path.abspath("C:/Users/catal/OneDrive/Escritorio/OTOÑO 2021/Trabajo de investigación/Códigos-Paper/Demanda Agregada")
# dname = os.path.dirname(abspath)
# os.chdir(dname)

# Importamos funciones que resuelven el3/ P.O.
from OptimizadorDA import OptimizadorDA
from OptimizadorDAfastChg import OptimizadorDAfast

lanzamientos = 100 # Nº de simulaciones
adopcion = 100   # Nº de hogares (y de VEs puesto que la adopcion es 100%)
# demanda = "Sin"   # "Sin" no considera la demanda residencial, "Con" la considera
demanda = "Con"
Potencia = 5000000   # (infinito) Se libera la restricción de máx. potencia en el punto de conexión.
          # Se define Tmin de carga como 10 minutos (1 intervalo)

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

#Lectura archivos

# Cargamos los requerimientos de energía de cada vehículo eléctrico
Energia = pd.read_csv('../Datos Entrada/Energia.csv')
# Tiempos de desconexion
desconexiones_perfiles = pd.read_csv('../Datos UK/DesconexionAuto_indice.csv',index_col=0)
desconexiones_perfiles.columns = ['EV'+str(i) for i in range(2000)]
#Horas infactibles de carga por periodo de estacionamiento breve
infactibles_perfiles = pd.read_csv('../Datos UK/Horas_infactibles.csv',index_col=0)
infactibles_perfiles.columns =  ['EV'+str(i) for i in range(2000)]


#%%                                                                 
""" Optimizacion """

# Importar archivos con perfiles de carga no coordinada en resolucion 5 y 10 minutos
archivoDwellings = pd.read_csv('../Datos Entrada/PerfilCarga.csv',sep=';')
archivoDwellings5 = pd.read_csv('../Datos Entrada/PerfilCarga5.csv',sep=';')
archivoNoCoordLento = pd.read_csv('../Datos Entrada/InputNoCoordinado10.csv')
archivoNoCoordLento.columns= ['EV'+str(i) for i in range(2000)]
# archivoNoCoordLento5 = pd.read_csv('../Datos Entrada/InputNoCoordinado5.csv')
# archivoNoCoordLento5.columns= ['EV'+str(i) for i in range(2000)]


#se ingresa parametrizacion de carga rapida del usuario
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
#leemos perfiles de carga rapida no coordinada. Modelamos la carga rapida con resolucion 5 minutos
archivoNoCoordRapido = pd.read_csv('../Datos Entrada/InputNoCoordinadoRapido_param5_'+parametrizacion_joined_string+'.csv')
archivoNoCoordRapido.columns = ['EV'+str(i) for i in range(2000)]

#se crea carpeta para el nivel de adopcion 
if not os.path.exists(str(adopcion)):
    os.makedirs(str(adopcion))
    
#se crea sub carpeta al interior del nivel de adopcion por la parametrizacion del usuario
if not os.path.exists(str(adopcion)+'/'+parametrizacion_joined_string):
    os.makedirs(str(adopcion)+'/'+parametrizacion_joined_string)

# Tiempo de simulación
start = datetime.now()

# Inicializacion
ValorObjetivoLento = []
ValorObjetivoRapido = []
DemAgrNoCoordinadaLenta =[]
DemAgrNoCoordinadaRapida = []
DemAgrResidencial = []
DemAgrResidencial5 = []

random_EVs = np.random.randint(0,2000,(lanzamientos,adopcion))
random_DWs = np.random.randint(0,2000,(lanzamientos,adopcion))# dwellings
#%%
for i in range(lanzamientos):

    """ Seleccion aleatoria """
    
    # filas-> lanzamientos; columnas-> vehiculos seleccionados
    # En el caso de VEs podemos seleccionar hasta el VE Nº 2000 
    # tiempos de desconexión. Para los hogares podemos seeccionar cualquiera (del 1 al 2000)

    
    # Importamos las cargas definiendo las columnas (VEs) a partir de vectores aleatorios
    # perfilNoCoorLento = archivoNoCoordLento.iloc[:,random_EVs[i]]
    perfilNoCoorLento = archivoNoCoordLento.iloc[:,random_EVs[i]]
    perfilNoCoorRapido = archivoNoCoordRapido.iloc[:,random_EVs[i]]
    
    # Obtenemos la demanda coincidente como la suma de las cargas (sumamos cada fila -> intervalo horario)
    DemAgrNoCoordinadaLenta.append(perfilNoCoorLento.sum(axis=1))
    DemAgrNoCoordinadaRapida.append(perfilNoCoorRapido.sum(axis=1))
    
    # Analogo para demanda residencial a usar en carga lenta res10 y carga rapida res 5
    perfilDemResidencial = archivoDwellings.iloc[:,random_DWs[i]]
    DemAgrResidencial.append(perfilDemResidencial.sum(axis=1)/1000)
    perfilDemResidencial5 = archivoDwellings5.iloc[:,random_DWs[i]]
    DemAgrResidencial5.append(perfilDemResidencial5.sum(axis=1)/1000)
    
    #calculamos numero de cargas por usuario
    df_ch= perfilNoCoorLento.copy()
    n_sw=np.zeros(len(df_ch.columns))
    k=0
    for j in range(len(df_ch.columns)):
        if df_ch.iloc[0,j]>0: n=1
        else: n=0
        n_sw[k]=int(sum(df_ch.iloc[:,j].diff().eq(3.6))+n)
        k=k+1
    # Se guardan resultados de optimizacion para carga lenta
    Tmin = 1
    auxiliar1,dataExcel = OptimizadorDA(adopcion, demanda, Potencia, Tmin, random_EVs[i], DemAgrResidencial[i],Energia,desconexiones_perfiles,n_sw,infactibles_perfiles) 
    # auxiliar1= OptimizadorDA(adopcion, demanda, Potencia, Tmin, random_EVs[i], DemAgrResidencial[i],Energia,desconexiones_perfiles,n_sw,infactibles_perfiles) 
                        
    print('\n')
    print('         PROCESO SLOW',2*i-1 + 1,'DE',2*lanzamientos)
    print('\n')  

        
    # Se guardan resultados de optimizacion para carga rápida
    Tmin = 2
    auxiliar2,dataExcelFast= OptimizadorDAfast(adopcion, demanda, Potencia, Tmin, random_EVs[i], DemAgrResidencial5[i],Energia,desconexiones_perfiles,n_sw,infactibles_perfiles)
    # auxiliar2 = OptimizadorDAfast(adopcion, demanda, Potencia, Tmin, random_EVs[i], DemAgrResidencial5[i],Energia,desconexiones_perfiles,n_sw,infactibles_perfiles)
    
    print('\n')
    print('         PROCESO FAST',2*i + 1,'DE',2*lanzamientos)
    print('\n')




    """Guardar datos de lanzamiento"""
    dataExcel.to_csv(str(adopcion)+'/'+parametrizacion_joined_string+'/lanz'+str(i+1)+'.csv')
    dataExcelFast.to_csv(str(adopcion)+'/'+parametrizacion_joined_string+'/lanzFast'+str(i+1)+'.csv')
    
    
    """Guardamos maxima demanda agregada"""
    ValorObjetivoLento.append(auxiliar1)
    ValorObjetivoRapido.append(auxiliar2)

finish = datetime.now()

#%%
""" Analisis """

# print(finish-start) 

maxDAlenta = []
maxDArapida = []
porcentajeLenta = []
porcentajeRapida = []
for i in range(lanzamientos):
    # Porcentaje de reducción (gráficos de barras)
    if demanda == "Con":
        maxDAlenta.append(max(DemAgrResidencial[i]+DemAgrNoCoordinadaLenta[i]))
        maxDArapida.append(max(DemAgrResidencial5[i]+DemAgrNoCoordinadaRapida[i]))
    elif demanda == "Sin":
        maxDAlenta.append(max(DemAgrNoCoordinadaLenta[i]))
        maxDArapida.append(max(DemAgrNoCoordinadaRapida[i]))
    else:
        print("Por favor introduzca un valor  valido para la demanda ('Con' o 'Sin')")
for i in range(lanzamientos):    
    # Para cada simulacion comparamos la máxima demanda coincidente con el valor objetivo de la función (que es a su vez la máxima demanda coincidente óptima)
    aux1 = (1-ValorObjetivoLento[i]/maxDAlenta[i])*100
    aux2 = (1-ValorObjetivoRapido[i]/maxDArapida[i])*100
    porcentajeLenta.append(aux1) # Porcentaje de reducción (carga lenta)
    porcentajeRapida.append(aux2)# Porcentaje de reducción (carga rápida)

#%%
""" Guardar resultados """
import pickle
aux_Name = 'PorcentajeReduccion'+str(adopcion)+'VEs'+'Pot'+str(Potencia)+'Lanz'+str(lanzamientos)+demanda
df=pd.DataFrame({'valorObjetivoLento':ValorObjetivoLento,'valorObjetivoRapido':ValorObjetivoRapido,'porcentajeLenta':porcentajeLenta,'porcentajeRapida':porcentajeRapida})
df.to_csv(str(adopcion)+'/'+parametrizacion_joined_string+'/'+aux_Name+'df'+'.csv')

#%%
""" Cargar resultados """
# Si se desean cargar resultados previos de % de reducción
CargarResultados = 1 # Definir como 1 para cargar
aux_Name = 'PorcentajeReduccion'+str(adopcion)+'VEs'+'Pot'+str(Potencia)+'Lanz'+str(lanzamientos)+demanda
if CargarResultados:
    # Load 
    # [porcentajeLenta, porcentajeRapida] = pickle.load(open(aux_Name+'.dat',"rb"))
    df=pd.read_csv(str(adopcion)+'/'+parametrizacion_joined_string+'/'+aux_Name+'df'+'.csv')
    
porcentajeLenta = df['porcentajeLenta'].tolist()
porcentajeRapida = df['porcentajeRapida'].tolist()


# #filter values
# porcentajeRapida = list(map(lambda porcentaje: np.mean(porcentajeRapida) if porcentaje>=70 else porcentaje, porcentajeRapida))
# porcentajeLenta= list(map(lambda porcentaje: np.mean(porcentajeLenta) if porcentaje>=70 else porcentaje, porcentajeLenta))


#%% 
plt.rcParams.update(plt.rcParamsDefault)
porcentaje_red=pd.DataFrame({'Lenta':porcentajeLenta,'Rapida':porcentajeRapida})
aux_Name = 'porcentaje-red-'+str(adopcion)+'VEs'+'Pot'+str(Potencia)+'Lanz'+str(lanzamientos)+demanda+'MaximaDemandaAgregada'

# Grafico de % de reduccion 
plt.rc('axes',edgecolor='gray')
sns.kdeplot(porcentajeLenta,shade=True)
sns.kdeplot(porcentajeRapida,shade=True)  
plt.xlabel('ADMD reduction percentage')
plt.ylabel('Frequency')
plt.grid(which='major',linestyle='-',alpha=0.5) #alpha = opacidad
plt.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad
plt.minorticks_on()
plt.legend(labels=['Slow charging \% reduction', 'Fast charging \% reduction'])
plt.savefig(str(adopcion)+'/'+parametrizacion_joined_string+'/'+aux_Name+'.pdf')
plt.show()

#%% 
"""Plot de maxima demanda agregada por grupo de adopcion"""


porcentaje_red=pd.DataFrame({'Lenta':porcentajeLenta,'Rapida':porcentajeRapida})
aux_Name = 'MaxDemnAggr'+str(adopcion)+'VEs'+'Pot'+str(Potencia)+'Lanz'+str(lanzamientos)+demanda+'MaximaDemandaAgregada'


valorObjetivoLento_auto = df.valorObjetivoLento
# #filter
# valorObjetivoLento_auto = list(map(lambda x: np.mean(valorObjetivoLento_auto) if (x<550 or x!=x) else x, valorObjetivoLento_auto))
maxDAlenta = df.valorObjetivoLento/(1 - df.porcentajeLenta/100)
# #filter
# maxDAlenta = list(map(lambda x: np.mean(maxDAlenta) if (x<=50 or x!=x) else x, maxDAlenta))


valorObjetivoRapido_auto = df.valorObjetivoRapido
# #filter
# valorObjetivoRapido_auto = list(map(lambda x: np.median(valorObjetivoRapido_auto) if (x<550  or x!=x) else x, valorObjetivoRapido_auto))

maxDArapida = df.valorObjetivoRapido/(1 - df.porcentajeRapida/100)
# #filter
# maxDArapida = list(map(lambda x: np.mean(maxDArapida) if (x<=550 or x!=x) else x, maxDArapida))


# Grafico de demanda agregada no coordinada
print('la dstancia no coordinada entre las media es ', np.mean(maxDArapida)-np.mean(maxDAlenta))
sns.kdeplot(maxDAlenta,shade=True)
sns.kdeplot(maxDArapida,shade=True)     
plt.xlabel('Maximum aggregate demand [kW] ')
plt.ylabel('Frequency')
#plt.title('Máxima demanda agregada no coordinada adopcion='+str(adopcion)+'EVs')
plt.grid(which='major',linestyle='-',alpha=0.7) #alpha = opacidad
plt.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad
plt.minorticks_on()
plt.legend(labels=['Slow charging', 'Fast charging'])
plt.savefig(str(adopcion)+'/'+parametrizacion_joined_string+'/'+'gaussNoCoord_'+aux_Name+'.pdf',bbox_inches='tight')
plt.show()


# Grafico carga coordinada
print('la distancia coordinada entre las media es ', np.mean(valorObjetivoRapido_auto)-np.mean(valorObjetivoLento_auto))
sns.kdeplot(valorObjetivoLento_auto,shade=True)
sns.kdeplot(valorObjetivoRapido_auto,shade=True)     
plt.xlabel('Maximum aggregate demand [kW]  ')
#plt.title('Máxima demanda agregada coordinada adopcion='+str(adopcion)+'EVs')
plt.ylabel('Frequency')
plt.grid(which='major',linestyle='-',alpha=0.7) #alpha = opacidad
plt.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad
plt.minorticks_on()
plt.legend(labels=['Slow charging', 'Fast charging'])
plt.savefig(str(adopcion)+'/'+parametrizacion_joined_string+'/'+'gaussCoord_'+aux_Name+'.pdf',bbox_inches='tight')
plt.show()


#%% 
  
# Definimos intervalos para el eje X   
defInicio = int(min(min(porcentajeLenta),min(porcentajeRapida))/10)*10
defFinal  = int(max(max(porcentajeLenta),max(porcentajeRapida))/10+1)*10
    
# Si se desean comparar diferentes escenarios habría que definir previamente estos limites (estandarizarlos para todos los escenarios)

ejeX = np.arange(defInicio,defFinal)
vectorLenta = []
vectorRapida = []

# Generamos histograma:
for i in range(defInicio,defFinal):
    contadorLen = 0
    contadorRap = 0
    for j in range(len(porcentajeLenta)):
        if i <= porcentajeLenta[j] < i+1:
            contadorLen = contadorLen + 1
        if i <= porcentajeRapida[j] < i+1:
            contadorRap = contadorRap + 1
    vectorLenta.append(contadorLen)
    vectorRapida.append(contadorRap)

print('Numero de escenarios carga lenta muestreados:',sum(vectorLenta))
print('Numero de escenarios carga rápida muestreados:',sum(vectorRapida))

# print('Demanda agregada NO COORDINADA promedio, carga lenta: ',sum(maxDAlenta)/len(maxDAlenta))
# print('Demanda agregada NO COORDINADA promedio, carga rápida: ',sum(maxDArapida)/len(maxDArapida))
# print('Demanda agregada COORDINADA promedio, carga lenta: ',sum(ValorObjetivoLento)/len(ValorObjetivoLento))
# print('Demanda agregada COORDINADA promedio, carga rápida: ',sum(ValorObjetivoRapido)/len(ValorObjetivoRapido))

# Graficamos histogramas
fig = plt.figure()
ax = fig.add_axes([0,0,1,1])
ax.bar(ejeX + 0.00, vectorLenta, color = 'b', width = 0.3, edgecolor = 'b')#, label='\% Reduccion carga lenta')
ax.bar(ejeX + 0.3, vectorRapida, color = 'g', width = 0.3, edgecolor = 'g')#, label='\% Reduccion carga rápida')
# ax.set_title('Adopción de '+str(adopcion)+' VEs. '+demanda+' dem. residencial '+str(lanzamientos)+' simulaciones')
ax.set_xlabel('Porcentaje de reducción respectivo')
ax.set_ylabel('Frecuencia')
ax.set_xlim([25,75])
if lanzamientos == 100:
    ax.set_ylim([0,23])
elif lanzamientos == 1000:
    ax.set_ylim([0,200])
ax.set_axisbelow(True)
ax.legend(labels=['\% Reduccion carga lenta', '\% Reduccion carga rápida'])
ax.grid(which='major',linestyle='-',alpha=0.7)
ax.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad
ax.minorticks_on()
aux_Name = 'PorcentajeReduccion'+str(adopcion)+'VEs'+'Pot'+str(Potencia)+'Lanz'+str(lanzamientos)+demanda+'MaximaDemandaAgregada'
Name = str(adopcion)+'/'+parametrizacion_joined_string+'/'+aux_Name+'.pdf'
fig.savefig(Name, bbox_inches='tight') # Formato alta calidad # +'gap0'

#%%
# Escribir informacion relevante
informacionTxt  = open(str(adopcion)+'/'+parametrizacion_joined_string+'/'+aux_Name+'.txt', "w") 
informacionTxt.write('Tiempo de simulación ' + str(finish-start) +'\n')
informacionTxt.write('Demanda agregada NO COORDINADA promedio, carga lenta: ' + str(sum(maxDAlenta)/len(maxDAlenta)) +'\n')
informacionTxt.write('Demanda agregada NO COORDINADA promedio, carga rápida: ' + str(sum(maxDArapida)/len(maxDArapida)) +'\n')
informacionTxt.write('Demanda agregada COORDINADA promedio, carga lenta: ' + str(sum(ValorObjetivoLento)/len(ValorObjetivoLento)) +'\n')
informacionTxt.write('Demanda agregada COORDINADA promedio, carga rápida: ' + str(sum(ValorObjetivoRapido)/len(ValorObjetivoRapido)))
informacionTxt.close()

#%%
""" Guardar resultados """
# Se guardan resultados de % de reducción
import pickle

# Save
pickle.dump([porcentajeLenta, porcentajeRapida], open(str(adopcion)+'/'+parametrizacion_joined_string+'/'+aux_Name+'.dat',"wb"))


#%%
""" Cargar resultados """
aux_Name2 = 'PorcentajeReduccion'+str(adopcion)+'VEs'+'Pot'+str(Potencia)+'Lanz'+str(lanzamientos)+demanda+'MaximaDemandaAgregada'
# Si se desean cargar resultados previos de valores de Max. demanda coincidente óptima (valores objetivos del PO)
CargarResultados = 1

if CargarResultados:
    [ValorObjetivoLento, ValorObjetivoRapido] = pickle.load(open(str(adopcion)+'/'+parametrizacion_joined_string+'/'+aux_Name2+'.dat',"rb"))

#%%
""" Graficos con valores optimos """

vectorDemNoCoorPromedioLenta = [sum(maxDAlenta)/len(maxDAlenta)]*len(ejeX)
vectorDemNoCoorPromedioRapida = [sum(maxDArapida)/len(maxDArapida)]*len(ejeX)

#%%

Inicio = int(min(min(ValorObjetivoLento),min(ValorObjetivoRapido)))
Final = int(max(max(ValorObjetivoLento),max(ValorObjetivoRapido))+1)

NumTicks = 50
Paso = (Final-Inicio)/NumTicks
ejeX2 = np.arange(Inicio,Final,Paso)

# Inicializamos variables para generar histograma
vectorLenta2 = []
vectorRapida2 = []

for i in range(NumTicks):
    contadorLen = 0
    contadorRap = 0
    Izq = Inicio + Paso*i
    Der = Izq + Paso
    for j in range(len(ValorObjetivoLento)):
        if Izq <= ValorObjetivoLento[j] < Der:
            contadorLen = contadorLen + 1
        if Izq <= ValorObjetivoRapido[j] < Der:
            contadorRap = contadorRap + 1
    vectorLenta2.append(contadorLen)
    vectorRapida2.append(contadorRap)
   
# Graficamos 
fig = plt.figure()
ax = fig.add_axes([0,0,1,1])
ax.bar(ejeX2 + 0.00, vectorLenta2, color = 'b', width = 0.3, edgecolor = 'b')#, label='\% Reduccion carga lenta')
ax.bar(ejeX2 + 0.3, vectorRapida2, color = 'g', width = 0.3, edgecolor = 'g')#, label='\% Reduccion carga rápida')
ax.plot
# ax.set_title('Adopción de '+str(adopcion)+' VEs. '+demanda+' dem. residencial '+str(lanzamientos)+' simulaciones')
ax.set_xlabel('Máxima demanda agregada (kW)')
ax.set_ylabel('Frecuencia')
# ax.set_ylim([0,66])
ax.set_axisbelow(True)
ax.legend(labels=['\% Reduccion carga lenta', '\% Reduccion carga rápida'])
ax.grid(which='major',linestyle='-',alpha=0.7)
ax.grid(which='minor',linestyle='dashed',alpha=0.2) #alpha = opacidad
ax.minorticks_on()
aux_Name2 = 'PorcentajeReduccion'+str(adopcion)+'VEs'+'Pot'+str(Potencia)+'Lanz'+str(lanzamientos)+demanda+'MaximaDemandaAgregada'
Name =str(adopcion)+'/'+parametrizacion_joined_string+'/'+aux_Name2+'.pdf'
fig.savefig(Name, bbox_inches='tight') # Formato alta calidad # +'gap0'

#%%
""" Guardar resultados """
# Si se desean guardan resultados de valores objetivos
pickle.dump([ValorObjetivoLento, ValorObjetivoRapido], open(str(adopcion)+'/'+parametrizacion_joined_string+'/'+aux_Name2+'.dat',"wb"))
