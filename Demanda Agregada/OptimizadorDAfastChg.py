# -*- coding: utf-8 -*-
"""
 
Esta función define el modelo de optimización en Gurobi (minimización de la máx. demanda coincidente)
para la opción de carga EV rapida y lo resuelve- entrega finalmente el valor resultante de la función objetivo tras la optimización
"""
#librerias
import itertools
import pandas as pd
from datetime import datetime 
from gurobipy import Model, GRB, quicksum#, abs_, min_#, max_, and_, or_
# from gurobipy import * # (todo)
import os
import numpy as np
# Cargamos los requerimientos de energía de cada vehículo eléctrico
Energia=pd.read_csv('../Datos Entrada/Energia.csv')
# Tiempos de desconexion
# Tiempos de desconexion
desconexiones_perfiles = pd.read_csv('../Datos UK/DesconexionAuto_indice.csv')
def OptimizadorDAfast(adopcion, demanda, Potencia, Tmin_config, SeleccionEVs, PerfilResidencial,Energia,desconexiones_perfiles,n_sw,infactibles):

    ListaSeleccion = list(SeleccionEVs)
    # ListaSeleccion.append(0) # Esto es para que lea el indice
    data = Energia.iloc[ListaSeleccion,:]
    
    print("Versión "+str(adopcion)+" EVs")
    
    # Transformamos el pandas CSV a lista     
    flat_data = data['Demanda'].tolist()
    
    # Definimos el perfil residencial
    if demanda == "Con":
        dataCarga = PerfilResidencial
    elif demanda == "Sin":
        dataCarga = PerfilResidencial*0
    else:
        dataCarga = False
        print("Introduzca por favor un valor valido para la demanda residencial ('Con' o 'Sin')")
    
    #Tiempo
    start = datetime.now()
        
    # =============================================================================
    #                                    GUROBI 
    # =============================================================================
    m = Model() 
    
    m.params.LogToConsole = True # default
    # m.params.TimeLimit = 300    # 1200 # second
    m.params.MIPGap = 0.03
    # m.params.DegenMoves=1
    # m.params.method = 2
    # m.params.Crossover=0
    # m.params.Presolve = 0      # Default: -1 automatic, 0 off
    # m.Params.MIPGap = 5e-4  # Default: 1e-4 (tolerancia de valor objetivo)
    
    EVs_data = flat_data
    print("Version con datos reales")
    
    n = len(EVs_data) # Nº VEs
    N = range(n)      # 
    T = 288           # Nº intervalos temporales (resolucion de 5 mins)
    eta = 1           # Eficiencia (es 1 dado que los datos de energía objetivo por vehículo corresponden a energía retirada de la red)
    pLoad = 7.2    # En esta version del modelo la potencia es fija e idéntica para cada vehículo
    
    #Definicion de variables 
    
    p = m.addVars(n, T, vtype=GRB.BINARY) 
    # p = m.addVars(n, T, lb=0, ub=1, vtype=GRB.CONTINUOUS)  #relajacion LP
    b = m.addVars(n, T, vtype=GRB.BINARY) 
    x = m.addVars(n, vtype=GRB.BINARY)
    w = m.addVars(n, T, vtype=GRB.BINARY)
    dx = m.addVars(n, T, vtype=GRB.BINARY) 
    dy = m.addVars(n, T, vtype=GRB.BINARY)
    d = m.addVars(n, T, vtype=GRB.BINARY)    
    Ene_falla = m.addVars(n, vtype=GRB.CONTINUOUS) # potencia critica
    max_power = m.addVar(lb=0.0, vtype=GRB.CONTINUOUS) # Demanda maxima
    m.update()
    #perfiles de desconexiones a leer 
    desconexiones=desconexiones_perfiles.iloc[:,SeleccionEVs].fillna(-1)

    columnas = desconexiones.columns.tolist()
    NumCols = len(columnas)

    #Lista de tiempo factibles de carga por EV
    T_factible = []
    for k in range(len(infactibles.columns)):
        lista = list(np.arange(T))
        #contamos periodos de infactibilidad (se divide en 2 ya que es un rango)
        n_infact =  int(infactibles.iloc[:,k].count()/2)
        for j in range(n_infact):
            ini = infactibles.iloc[j,k]*2 #se multiplica por dos porque es resolucion de 5 min
            fin = infactibles.iloc[j+1,k]*2 #se multiplica por dos porque es resolucion de 5 min
            intervalo_infactible = list(np.arange(ini,fin+1))
            #quitamos intervalo infactible de la lista de tiempo
            lista = [i for i in lista if i not in intervalo_infactible]
            
        T_factible.append(lista)
        
        
    # Restriccion para satisfacer demanda energetica de cada vehiculo
    for i in N:
        m.addConstr(eta * pLoad * quicksum(p[i,t] for t in T_factible[i])  == EVs_data[i]*12,  'demanda_%d' % (i))

    #restriccion de potencia 0 en periodo de desconexión del vehículo
    for k in range(NumCols): # numero de vehiculos
        for j in range(len(desconexiones)-1):  # filas del archivo desconexión
            if desconexiones.iloc[j,k] == -1.0:
                # Se acabaron los datos de desconexion
                break
            elif (j % 2) - 1  == 0: # Vamos viendo de a 2 en 2:
                # Restricción: la potencia debe ser 0 para el período de desconexión del vehículo
                m.addConstrs(p[k,t] <= 0.001 for t in range(T) if t in range( int(desconexiones.iloc[j-1,k]),1+int(desconexiones.iloc[j,k])) )
           
    # # Restricciones del tipo tiempo minimo de carga
    # # Esto es por si se define por ejemplo Tmin=3 (30 mins) pero el vehículo requiere solo 5 mins de carga      
    Tmin = [min(Tmin_config, int(EVs_data[i]/(7.2/12))) for i in N]  #12 porque la resolucion es de 5 minutos
        
 
    # Condicion inicial
    for i in N:
        for j in range(0, Tmin[i]):
            if j in T_factible[i]:
                m.addConstr(p[i,0+j]>=(p[i,0]-0))
            # Si el vehículo está cargando en el instante inicial, debe cargar hasta completar Tmin intervalos de carga
    
    # Caso general
    for i in N:
        for t in T_factible[i][1:-1]:
            if t < T-Tmin[i]: # Esto es, evaluamos si no nos encontramos justo en los intervalos finales del día (condición de borde)
                # En este caso estamos durante el día
                for j in range(0, Tmin[i]): # O bien 'j in range(t+1,t+Tmin)' y 'p[i,j]>=...'
                    m.addConstr(p[i,t+j]>=(p[i,t]-p[i,t-1]))                    
                    # Otra forma de escribirlo
                    # m.addConstrs(p[i,t+j]>=p[i,t]-p[i,t-1] for i in N for t in range(1,T-Tmin) for j in range(0,Tmin))                    
                    # El lado derecho de la desigualdad pertenece a {-1,0,1}. Dado que 'p' es variable
                    # binaria, el lado izquierdo pertenece a {0,1} y por tanto la restriccion se activa
                    # cuando el lado derecho es igual 1. Esto es, cuando inicia un proceso de carga.
                    # Se fuerza entonces a que en los instantes t+j el auto este cargando
    
            else:
                # Condición de borde:
                m.addConstr(p[i,t+1] <= p[i,t]) #De modo que si p[i,t] = 1, en t+1 se puede detener o continuar la carga
                # Si p[i,t] = 0, en t+1 obligatoriamente no se puede comenzar otro proceso de carga (no hay tiempo suficiente
                # para carga el tiempo minimo). Si inicialmente p[i,t]=1 y luego en t+1 se corta la carga, se mantendra apagada en la siguiente
                # vuelta del ciclo for por la condicion anterior.
 
    # IMPORTANTE:
    # La solucion optima cambia al agregar las restricciones para 'y'
    # aun sin siquiera modificar la funcion objetivo, el orden de las restricciones modifica la performance de Gurobi!
    for t in range(T):
        # Restriccion para maxima potencia coincidente, tambien es posible utilizar funcion max_
        m.addConstr(pLoad * quicksum(p[i,t] for i in N) + dataCarga[t] <= max_power)

 

    # Restriccion Potencia del pto. de conexion
    m.addConstrs(eta* pLoad* quicksum(p[i,t] for i in N) + dataCarga[t] <= Potencia for t in range(T))
    
    # Definimos función objetivo:
    # m.setObjective(max_power+costoFalla*quicksum(Ene_falla[i] for i in N), GRB.MINIMIZE)     
    m.setObjective(max_power, GRB.MINIMIZE)   
    
    
    #restriccion del limite de procesos de carga al dia    
    eps = 0.0001
    M = len(range(T)) + eps
    for i in N:
        # m.addConstr((p[i,0]==1) >> (b[i,0]==1))
        m.addConstrs(p[i,t]>= p[i,t-1] + eps - M*(1-b[i,t]) for t in T_factible[i][1:])
        m.addConstrs(p[i,t]<= p[i,t-1] + M*b[i,t] for t in T_factible[i][1:])
        m.addConstr((p[i,0]==1) >> (x[i]==1))
        for t in T_factible[i][1:]:
            m.addConstr((b[i,t]==1) >> (w[i,t]==1))
            # m.addConstr((b[i,t]==0) >> (w[i,t]==0))
            
    # m.addConstrs(quicksum(w[i,t] for t in range(T))+x[i] <= 5 for i in N) #limite de procesos de carga
    m.addConstrs(quicksum(w[i,t] for t in T_factible[i])+x[i] <= 3 for i in N)
    
 

    
    
    # # Resolvemos el modelo:
    m.presolve()
    m.optimize()
    
    
 
    finish = datetime.now()
    
    """Print Result"""
    # for i in N:
    #     for t in range(T):
    #         print(str(p[i,t].X*3.6),';',end='')
    #     print(' ')
        
    # for i in N:
    #     for t in Off:
    #         print(str(p[i,t].X*3.6),';',end='')
    #     print('\n')
    """Create Data Frame"""
    
    dataExcel = pd.DataFrame({'EV'+str(i):[7.2*p[i,t].X for t in range(T)] for i in N})
    
    """Energia de falla"""
    
    # sumaP = sum(p[i,t].X for i in N for t in range(T))
    # sumaEf = sum(Ene_falla[i].X for i in N)
    # maxPot = max_power.X
    # maxPot = presolve_model.objVal
    maxPot = m.objVal
    # print('Energía: '+str(sumaP*7.2/12))
    # print('Energía no servida '+str(sumaEf))
    print('Demanda Agregada maxima '+str(maxPot))
    
    # """Writing to CSV"""
    # dataExcel.to_csv(str(adopcion)+'/InputCoordinado'+str(adopcion)+demanda+'Potencia'+str(Potencia)+'.csv', index = False)

    return maxPot,dataExcel
    # return maxPot
  