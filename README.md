# Paper - data and codes

This repository provides input data and PYTHON codes of the paper : *"Is single-phase residential EV fast-charging a good idea? Evidence from optimal charging plans based on realistic data"*  

 
## Main Folders:

* Datos Entrada : 
     + main data to use as input for each problem
     + 2000 dwellings profiles built from CREST tool https://repository.lboro.ac.uk/articles/dataset/CREST_Demand_Model_v2_0/2001129
     + 2000 ev charging profiles with 1 minute resolution
     + fast charging profiles parametrizations 
     
* Datos UK : 
     + contains statistics data of UK drivers, cleaned from National Travel Survey’, https://www.gov.uk/government/collections/national-travel-survey-statistics,
     + solves match between EV energy requirements and travel patterns 
     + gets unfeasible charging time windows for each vehicle
    
* ADMD : after diversity demand analyisis

* Demanda Agregada :
      + class with EV charging optimization
      + Statistical analysis

## Software Requirements 

 * Python: this codes have been tested with Python 3.9.12. The additional required libraries in python are:
              + Pandas
              + datetime  
              + gurobipy
              + numpy 
              + seaborn 
              + matplotlib 
              
 * Gurobi : optimizer tool used to solve the MILP problem that is solved in the codes provided. 
 
 
              
              
