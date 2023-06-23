import pandas as pd
import numpy as np

filename = 'points_wires.py'
pd.set_option('display.max_colwidth', None)

while(True):
    model_name = input("Enter the model name (e.g. Model-1): ")
    part_name = input("Enter the part name (e.g. Part-1): ")
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
points_wires = points_wires.to_string(index=False)

#save points and wires to a .py file
with open(filename, 'w') as f:
    for line in points_wires.split('\n'):
        f.write(line.strip() + '\n')

