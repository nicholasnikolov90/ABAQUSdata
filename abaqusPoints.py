import regex as re
import pandas as pd
import numpy as np

coordinates = pd.read_excel("coordinates.xlsx")
coordinates.columns.values[0] = 'x'
coordinates.columns.values[1] = 'y'
coordinates.columns.values[2] = 'z'
coordinates = coordinates.fillna(0).div(1000).sort_index()

points_wires = pd.Series() #initialize series object
#Initialize first two unique rows of points
points_wires.at[0] = f"mdb.models['Model-1'].parts['Part-1'].ReferencePoint(point=({coordinates.loc[0, 'x']},{coordinates.loc[0, 'y']},{coordinates.loc[0, 'z']}))"
points_wires.at[1] = f"mdb.models['Model-1'].parts['Part-1'].DatumPointByOffset(point=mdb.models['Model-1'].parts['Part-1'].referencePoints[1], vector=({coordinates.loc[1, 'x']},{coordinates.loc[1, 'y']},{coordinates.loc[1, 'z']}))"

#loop through entire coordinates, create all remaining points
for i in range(2, coordinates.index.max()+1):
    points_wires.at[i] = f"mdb.models['Model-1'].parts['Part-1'].DatumPointByOffset(point=mdb.models['Model-1'].parts['Part-1'].datums[{i}], vector=({coordinates.loc[i, 'x']},{coordinates.loc[i, 'y']},{coordinates.loc[i, 'z']}))"

#Initialize first unique row of wires
points_wires.at[coordinates.index.max()+2] = f"mdb.models['Model-1'].parts['Part-1'].WirePolyLine(mergeType=IMPRINT, meshable=ON, points=((mdb.models['Model-1'].parts['Part-1'].referencePoints[1],mdb.models['Model-1'].parts['Part-1'].datums[2]), ))"

for i in range(coordinates.index.max()+3, coordinates.index.max()*2+2):
    points_wires.at[i] = f"mdb.models['Model-1'].parts['Part-1'].WirePolyLine(mergeType=IMPRINT, meshable=ON, points=((mdb.models['Model-1'].parts['Part-1'].datums[{i-1-coordinates.index.max()}],mdb.models['Model-1'].parts['Part-1'].datums[{i-coordinates.index.max()}]), ))"

#save points to a .txt file
np.savetxt(r'np.txt', points_wires, fmt = '%s')

