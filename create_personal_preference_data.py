import numpy as np
import pandas as pd
import json

from demo.demo_dataloader import demoDataset, demo_dataloader_factory
from demo.demo_network import configs, image_transform


_DEFAULT_FASHION_IQ_DATASET_ROOT = 'static/image'

# データローダーの準備
demo_dataset = demoDataset(_DEFAULT_FASHION_IQ_DATASET_ROOT, 'dress', image_transform['val'])
demo_sample_dataloader = demo_dataloader_factory(demo_dataset, configs)
print("len:", len(demo_sample_dataloader))

# ファイル名を指定して特徴量を取り出せるようにする
demo_features = []
filename_2_demo_features_index = {}
for i, (images, filename_list) in enumerate(demo_sample_dataloader):
    for j, filename in enumerate(filename_list):
        filename_2_demo_features_index[filename] = (i, j)
    if i == 0:
        print(images.shape)
    demo_features.append(images)


json_open = open('preference/data/0.json', 'r')
json_load = json.load(json_open)

features_for_preference = []
for file in json_load:
    id = file.split(".")[0]
    index = filename_2_demo_features_index[id]
    features_for_preference.append(np.ravel(demo_features[index[0]][index[1]].numpy()))

dic_name_index = {}
df_index = pd.read_csv("preference/data/img_number.csv", header=0)
for index, row in df_index.iterrows():
    dic_name_index[row["画像No"]] = row["画像名"].split(".")[0]

df_female = pd.read_csv("preference/data/preference_female.csv", header=0)
df_male = pd.read_csv("preference/data/preference_male.csv", header=0)

index = 0
gender = "male"
df = pd.read_csv(f"preference/data/preference_{gender}.csv", header=0)
sample_df = df.iloc(index+1)

list_for_df = []
for i in range(100):
    score = sample_df["No.{}の画像があなたの好みであるかを0から10で評価してください．".format(i+1)]
    row = np.concatenate([np.array(score), features_for_preference[i]])
    list_for_df.append(row)

df_preference_head = pd.DataFrame(list_for_df)
print(df_preference_head)
df_preference_head.to_csv(f"preference/data/personal/{gender}{index}.csv")
