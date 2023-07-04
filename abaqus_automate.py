import pandas as pd
import numpy as np

filename = 'abaqus_script.py'
pd.set_option('display.max_colwidth', None)

#uncomment if want to do it as a CLI
while(True):
    model_name = str(input("Enter the model name (e.g. Model-1): "))
    part_name = str(input("Enter the part name (e.g. Part-1): "))
    pipe_size = float(input("Enter the pipe outer diameter (in meters) used to calculate the bending radius (e.g. 1.2192): "))
    break

coordinates = pd.read_excel("coordinates.xlsx", names=['x', 'y', 'z']).fillna(0).div(1000).sort_index()
inputs = pd.read_excel("inputs.xlsx", names=['model_name', 'part_name', 'pipe_size'])

#Uncomment when taking input file
#model_name = inputs['model_name'].at[0]
#part_name = inputs['part_name'].at[0]
#pipe_size = inputs['pipe_size'].at[0]

points_wires = pd.Series(dtype='float64') #initialize series object
#Initialize first two unique rows of points
points_wires.at[0] = f"mdb.models['{model_name}'].parts['{part_name}'].ReferencePoint(point=({coordinates.loc[0, 'x']},{coordinates.loc[0, 'y']},{coordinates.loc[0, 'z']}))"
points_wires.at[1] = f"mdb.models['{model_name}'].parts['{part_name}'].DatumPointByOffset(point=mdb.models['{model_name}'].parts['{part_name}'].referencePoints[1], vector=({coordinates.loc[1, 'x']},{coordinates.loc[1, 'y']},{coordinates.loc[1, 'z']}))"

#loop through entire coordinates, create all remaining points
for i in range(2, coordinates.index.max()+1):
    points_wires.at[i] = f"mdb.models['{model_name}'].parts['{part_name}'].DatumPointByOffset(point=mdb.models['{model_name}'].parts['{part_name}'].datums[{i}], vector=({coordinates.loc[i, 'x']},{coordinates.loc[i, 'y']},{coordinates.loc[i, 'z']}))"

#Initialize first unique row of wires
points_wires.at[coordinates.index.max()+2] = f"mdb.models['{model_name}'].parts['{part_name}'].WirePolyLine(mergeType=IMPRINT, meshable=ON, points=((mdb.models['{model_name}'].parts['{part_name}'].referencePoints[1],mdb.models['{model_name}'].parts['{part_name}'].datums[2]), ))"

#loop through entire coordinates, create all remaining wires
for i in range(coordinates.index.max()+3, coordinates.index.max()*2+2):
    points_wires.at[i] = f"mdb.models['{model_name}'].parts['{part_name}'].WirePolyLine(mergeType=IMPRINT, meshable=ON, points=((mdb.models['{model_name}'].parts['{part_name}'].datums[{i-1-coordinates.index.max()}],mdb.models['{model_name}'].parts['{part_name}'].datums[{i-coordinates.index.max()}]), ))"

#Add generic header for all abaqus imports
import_header = pd.Series(['from part import *','from material import *','from section import *','from assembly import *','from step import *','from interaction import *','from load import *','from mesh import *','from optimization import *','from job import *','from sketch import *','from visualization import *','from connectorBehavior import *','',f"mdb.Model(modelType=STANDARD_EXPLICIT, name='{model_name}')",f"mdb.models['{model_name}'].Part(dimensionality=THREE_D, name='{part_name}',type=DEFORMABLE_BODY)", ''])

points_wires = pd.concat([import_header, points_wires], ignore_index=True)

#create Magnitude
bends = pd.DataFrame()
bends['Magnitude'] = np.sqrt(coordinates['x']**2 + coordinates['y']**2 + coordinates['z']**2)

#normalize all directions
bends[['xn', 'yn', 'zn']] = coordinates[['x', 'y', 'z']].div(bends['Magnitude'], axis=0)

#create dot product between points
#initialize columns
bends['dotProduct'] = 0
bends['angleDeg'] = 0
bends['bendRadius'] = 0

#calculate dot product, angles between wires and bending radius
for i in range(1, bends.index.max() + 1): 
    bends['dotProduct'].at[i] = round(bends['xn'].at[i-1]*bends['xn'].at[i] + bends['yn'].at[i-1]*bends['yn'].at[i] + bends['zn'].at[i-1]*bends['zn'].at[i], 8)
    bends['angleDeg'].at[i] = round(np.degrees(np.arccos(bends['dotProduct'].at[i])), 1)

    #create bending radius conditions
    if bends['angleDeg'].at[i] < 1:
        bends['bendRadius'].at[i] = 0
    elif bends['angleDeg'].at[i] <= 12:
        bends['bendRadius'].at[i] = round(57 * pipe_size, 4)
    elif bends['angleDeg'].at[i] <= 60:
        bends['bendRadius'].at[i] = round(5 * pipe_size, 4)
    else:
        bends['bendRadius'].at[i] = round(3 * pipe_size, 4)
    
#add rounding for the bends
bend_radius = pd.Series(dtype='float64')
skip_origin_bend = 0

for i in range(bends.index.max() + 1):
    if bends['bendRadius'].at[i] > 0:
        if (skip_origin_bend):
            bend_radius.at[i] = f"mdb.models['{model_name}'].parts['{part_name}'].Round(radius={bends['bendRadius'].at[i]}, vertexList=(mdb.models['{model_name}'].parts['{part_name}'].vertices.findAt(({coordinates['x'].cumsum().at[i-1]},{coordinates['y'].cumsum().at[i-1]},{coordinates['z'].cumsum().at[i-1]}), ), ))"
        skip_origin_bend = 1
total_abaqus_script = pd.concat([points_wires,bend_radius]).to_string(index=False)
points_wires = points_wires.to_string(index=False) #force all to string, so it can be written to python file
#save points and wires to a .py file

with open(filename, 'w') as f:
    for line in total_abaqus_script.split('\n'):
        f.write(line.strip() + '\n')

