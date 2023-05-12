import datetime
import json
from flask import Flask, render_template, request, Response
from flask_cors import CORS
import numpy as np
import os
import pandas as pd
from PIL import Image
import random
import shutil
import torch
from torch import nn
from tqdm import tqdm

from data import DEFAULT_VOCAB_PATHS, _random_indices
from demo.demo_model import Net_demo
from demo.demo_dataloader import _get_img_list, demoDataset, demo_dataloader_factory
from demo.demo_network import configs, net, image_transform, text_transform
from language import vocabulary_factory
from models import create_models
from options import get_experiment_config
from preference.svm.svm import make_classifier
from set_up import setup_demo
from transforms import image_transform_factory, text_transform_factory

_DEFAULT_FASHION_IQ_DATASET_ROOT = 'static/image'

app = Flask(__name__)

CORS(
    app,
    supports_credentials=True
)

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

print(demo_features[0][0].numpy().shape)
# svm用に選択を保存
selected = {}

# 直前の出力リスト
recent_output = []

# ドレス画像一覧
img_list = _get_img_list("dress")


@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        randaom_img_id = _get_random_ref_image()
        random_img_path = os.path.join(_DEFAULT_FASHION_IQ_DATASET_ROOT, '{}.png'.format(randaom_img_id))
        return render_template("home.html", init_img_path=random_img_path)
    if request.method == 'POST':
        json_data = request.json
        print(json_data)
        return 'Failed'


def _get_random_ref_image():
    # ランダムで画像を出す
    dataset_root = _DEFAULT_FASHION_IQ_DATASET_ROOT
    num_img = len(img_list)
    print("num_img:", num_img)
    random_idx = random.randint(0, num_img - 1)
    dt_now = datetime.datetime.now()
    random_idx = (dt_now.hour * dt_now.minute * dt_now.second * dt_now.microsecond) % num_img
    print("random_idx:", random_idx)
    randaom_img_id = img_list[random_idx]
    return randaom_img_id
    randaom_img_path = os.path.join(dataset_root, '{}.png'.format(randaom_img_id))
    print(randaom_img_path)
    return randaom_img_path
    #return copied_img_path


@app.route("/dress/start", methods=['GET'])
def get_random_dress():
    """
    開始画像をランダムで返す
    """
    if request.method == 'GET':
        print("start")
        # TODO 選択データの辞書を初期化
        return _get_random_ref_image()


@app.route("/dress", methods=['GET', 'POST'])
def get_dress():
    """
    元画像と修正指示文から新しい画像を返す
    clothing_type: dress
    """
    
    global recent_output

    if request.method == 'GET':
        return _get_random_ref_image("dress")
    if request.method == 'POST':
        json_data = request.json
        print(json_data)
        
        # 選択の更新
        if len(recent_output) > 1:
            if json_data['image_path'] not in set(recent_output):
                selected[json_data['image_path']] = 1
                for idx in recent_output:
                    selected[idx] = -1
            else:
                for idx in recent_output:
                    if idx == json_data['image_path']:
                        selected[idx] = 1
                    else:
                        selected[idx] = -1

        # 修正指示文をtensorに変換
        modifier = json_data['modifier']
        modifier = text_transform['val'](modifier)
        modifier = modifier.detach().numpy()
        len_modifier = torch.tensor([len(modifier)])
        modifier = torch.tensor([modifier])
        print("modifier:", modifier.shape)
        print("len_modifier:", len_modifier)

        # 画像をtensorに変換
        ref_image_path = os.path.join(_DEFAULT_FASHION_IQ_DATASET_ROOT, '{}.png'.format(json_data['image_path']))
        ref_img = Image.open(ref_image_path).convert('RGB')
        ref_img = image_transform['val'](ref_img)
        ref_img = ref_img.detach().numpy()
        ref_img = torch.tensor([ref_img])

        # 特徴量を計算
        composed_features = net.module._extract_composed_features(ref_img, modifier, len_modifier)
        print("composed_features:", composed_features.shape)

        # 出力枚数
        num_output = 5
        
        # 一致度を計算
        all_similarity_matrix = torch.Tensor().cuda()
        all_file_name_list = []
        with torch.no_grad():
            for i, (images, filename_list) in enumerate(demo_sample_dataloader):
                image_features = net.module._extract_image_features(images)
                similarity_matrix = composed_features.mm(image_features.t())
                all_similarity_matrix = torch.cat([all_similarity_matrix, similarity_matrix], dim=1)
                all_file_name_list += filename_list
                if i % 10 == 0:
                    print(i, "/", len(demo_sample_dataloader))
                continue
            best_similarity_matrix, best_similarity_idx = all_similarity_matrix.topk(num_output)
        print("best:", best_similarity_matrix, best_similarity_idx)
        best_similarity_id = [
            all_file_name_list[idx] for idx in best_similarity_idx[0]
        ]
        #best_similarity_id = demo_dataset.img_list[best_similarity_idx[0][0]]
        result = {
            "new_image": best_similarity_id,
            "new_turn": False
        }
        recent_output = best_similarity_id
        return json.dumps(result)


@app.route("/dress/new_turn", methods=['POST'])
def get_new_dress():
    """
    好み推定の結果を用いて新たな開始画像を返す
    完成するまではランダムで出力
    """
    global recent_output
    if request.method == 'POST':
        json_data = request.json
        # 選択の更新
        if len(recent_output) > 1:
            if json_data['image_path'] not in set(recent_output):
                selected[json_data['image_path']] = 1
                for idx in recent_output:
                    selected[idx] = -1
            else:
                for idx in recent_output:
                    if idx == json_data['image_path']:
                        selected[idx] = 1
                    else:
                        selected[idx] = -1
        # TODO: 好み推定モデルの導入
        print("start new turn.")
        result = {
            "new_image": _get_random_ref_image(),
            "new_turn": True
        }
        return json.dumps(result)


@app.route("/favorite", methods=['GET', 'POST'])
def get_favorite_estimation():
    """
    好み推定を用いて5枚出力する
    完成するまではランダムで出力
    """
    # TODO: 好み推定モデルの導入
    print(selected)
    classifier = make_classifier(selected, filename_2_demo_features_index, demo_features)
    print("start classify.")
    for_estimation = []
    for_estimaiton_id = []
    better_score_id = []
    for i, id in enumerate(img_list):
        for_estimaiton_id.append(id)
        image_index_4_features = filename_2_demo_features_index[id]
        for_estimation.append(np.ravel(demo_features[image_index_4_features[0]][image_index_4_features[1]].numpy()))
        if i % 1000 == 0:
            estimation = classifier.predict(for_estimation)
            for id, score in zip(for_estimation, estimation):
                if score > 0:
                    better_score_id.append(id)
            for_estimation = []
            for_estimaiton_id = []
            print(better_score_id)
    estimation = classifier.predict(for_estimation)
    for id, score in zip(for_estimation, estimation):
        if score > 0:
            better_score_id.append(id)
    for_estimation = []
    for_estimaiton_id = []
    print(better_score_id)
    res = {}
    if len(better_score_id) > 0:
        if len(better_score_id) <= 5:
            res["estimation"] = better_score_id
        else:
            res["estimation"] = random.sample(better_score_id, 5)
    else:
        random_images = []
        for _ in range(5):
            random_image_id = _get_random_ref_image()
            random_images.append(random_image_id)
        res["estimation"] = random_images
    return json.dumps(res)

    for _ in range(5):
        random_image_id = _get_random_ref_image("dress")
        estimation.append(random_image_id)
    res = {
        "estimation": estimation
    }
    print(res)
    return json.dumps(res)


if __name__ == '__main__':    
    app.run(host="0.0.0.0", port=49876, use_reloader=True, debug=False)
    
    # svm用に選択を保存
    selected = {}
    
    # 直前の出力リスト
    recent_output = []
    #main()

"""
print(os.getcwd())
dic_name_index = {}
df = pd.read_csv("preference/data/img_number.csv", header=0)
for index, row in df.iterrows():
    dic_name_index[row["画像No"]] = row["画像名"].split(".")[0]
    
df_female = pd.read_csv("preference/data/preference_female.csv", header=0)

pref = {}

for index, row in df_female.iterrows():
    for i in range(1, 101):
        if row["No.{}の画像があなたの好みであるかを0から10で評価してください．".format(i)] >= 6:
            pref[dic_name_index[i]] = 1
        else:
            pref[dic_name_index[i]] = -1

classifier = make_classifier(pref, filename_2_demo_features_index, demo_features)
for_estimation = []
for_estimaiton_id = []
better_score_id = []

for i, id in enumerate(img_list):
    for_estimaiton_id.append(id)
    image_index_4_features = filename_2_demo_features_index[id]
    for_estimation.append(np.ravel(demo_features[image_index_4_features[0]][image_index_4_features[1]].numpy()))
    if i % 1000 == 0:
        estimation = classifier.predict(for_estimation)
        for id, score in zip(for_estimation, estimation):
            if score > 0:
                better_score_id.append(id)
        for_estimation = []
        for_estimaiton_id = []
        print(better_score_id)
estimation = classifier.predict(for_estimation)
for id, score in zip(for_estimation, estimation):
    if score > 0:
        better_score_id.append(id)
for_estimation = []
for_estimaiton_id = []
print(better_score_id)
res = {}
if len(better_score_id) > 0:
    if len(better_score_id) <= 5:
        res["estimation"] = better_score_id
    else:
        res["estimation"] = random.sample(better_score_id, 5)
else:
    random_images = []
    for _ in range(5):
        random_image_id = _get_random_ref_image()
        random_images.append(random_image_id)
    res["estimation"] = random_images

"""