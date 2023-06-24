import pandas as pd
import numpy as np

filename = 'points_wires.py'
pd.set_option('display.max_colwidth', None)

while(True):
    model_name = str(input("Enter the model name (e.g. Model-1): "))
    part_name = str(input("Enter the part name (e.g. Part-1): "))
    pipe_size = float(input("Enter the pipe outer diameter (in meters) used to calculate the bending radius (e.g. 1.2192): "))
    break

coordinates = pd.read_excel("coordinates.xlsx")
coordinates.columns.values[0] = 'x'
coordinates.columns.values[1] = 'y'
coordinates.columns.values[2] = 'z'
coordinates = coordinates.fillna(0).div(1000).sort_index()

points_wires = pd.Series() #initialize series object
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
bends['xn'] = coordinates['x'] / bends['Magnitude']
bends['yn'] = coordinates['y'] / bends['Magnitude']
bends['zn'] = coordinates['z'] / bends['Magnitude']

#create dot product between points
#initialize columns
bends['dotProduct'] = 0
bends['angleDeg'] = 0
bends['bendRadius'] = 0

#calculate dot product, angles between wires and bending radius
for i in range(1, bends.index.max() + 1): 
    bends['dotProduct'].at[i] = round(bends['xn'].at[i-1]*bends['xn'].at[i] + bends['yn'].at[i-1]*bends['yn'].at[i] + bends['zn'].at[i-1]*bends['zn'].at[i], 8)
    bends['angleDeg'].at[i] = round(np.degrees(np.arccos(bends['dotProduct'].at[i])), 1)
    if bends['angleDeg'].at[i] < 1:
        bends['angleDeg'].at[i] = 0
        
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
bend_radius = pd.Series()
current_x = 0
current_y = 0
current_z = 0

for i in range(bends.index.max() + 1):
    current_x += coordinates['x'].at[i]
    current_y += coordinates['y'].at[i]
    current_z += coordinates['z'].at[i]
    
    if bends['bendRadius'].at[i] > 0:
        bend_radius.at[i] = f"mdb.models['{model_name}'].parts['{part_name}'].Round(radius={bends['bendRadius'].at[i]}, vertexList=(mdb.models['{model_name}'].parts['{part_name}'].vertices.findAt(({current_x},{current_y},{current_z}), ), ))"

total_abaqus_script = pd.concat([points_wires,bend_radius]).to_string(index=False)
points_wires = points_wires.to_string(index=False) #force all to string, so it can be written to python file
#save points and wires to a .py file
with open(filename, 'w') as f:
    for line in total_abaqus_script.split('\n'):
        f.write(line.strip() + '\n')

