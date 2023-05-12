import json
import os
import pandas as pd

from app import filename_2_demo_features_index, demo_features

print(os.getcwd())
dic_name_index = {}
df = pd.read_csv("preference/data/img_number.csv", header=0)
for index, row in df.iterrows():
    dic_name_index[row["画像No"]] = row["画像名"]


df_female = pd.read_csv("preference/data/preference_female.csv", header=0)

pref = {}

for index, row in df_female.iterrows():
    for i in range(1, 101):
        print(row["No.{}の画像があなたの好みであるかを0から10で評価してください．".format(i)])
        if row["No.{}の画像があなたの好みであるかを0から10で評価してください．".format(i)] >= 8:
            pref[dic_name_index[i]] = 1
        else:
            pref[dic_name_index[i]] = -1

print(pref)
