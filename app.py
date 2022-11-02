import datetime
import json
from flask import Flask, render_template, request, Response
from flask_cors import CORS
import os
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
from set_up import setup_demo
from transforms import image_transform_factory, text_transform_factory

_DEFAULT_FASHION_IQ_DATASET_ROOT = 'static/image'

app = Flask(__name__)

CORS(
    app,
    supports_credentials=True
)

@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        randaom_img_id = _get_random_ref_image("dress")
        random_img_path = os.path.join(_DEFAULT_FASHION_IQ_DATASET_ROOT, '{}.png'.format(randaom_img_id))
        return render_template("home.html", init_img_path=random_img_path)
    if request.method == 'POST':
        json_data = request.json
        print(json_data)
        return 'Failed'


def _get_random_ref_image(clothing_type):
    # ランダムで画像を出す
    img_list = _get_img_list(clothing_type)
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

@app.route("/dress", methods=['GET', 'POST'])
def get_dress():
    """
    元画像と修正指示文から新しい画像を返す
    clothing_type: dress
    """
    if request.method == 'GET':
        return _get_random_ref_image("dress")
    if request.method == 'POST':
        json_data = request.json
        print(json_data)

        # 修正指示文をtensorに変換
        modifier = json_data['modifier']
        # ターンの終わり
        next_turn_modifiers = {"This is good.", "I like this one.", "I like this dress."}
        if modifier in next_turn_modifiers:
            # TODO: 好みモデルの導入
            print("start new turn.")
            result = {
                "new_image": _get_random_ref_image("dress"),
                "new_turn": True
            }
            return json.dumps(result)
        #modifier = "is more colorful and shorter sleeves and Is more floral and shorter sleeves"
        modifier = text_transform['val'](modifier)
        modifier = modifier.detach().numpy()
        len_modifier = torch.tensor([len(modifier)])
        modifier = torch.tensor([modifier])
        print("modifier:", modifier.shape)
        print("len_modifier:", len_modifier)

        # 画像をtensorに変換
        clothing_type = "dress"
        ref_image_path = os.path.join(_DEFAULT_FASHION_IQ_DATASET_ROOT, '{}.png'.format(json_data['image_path']))
        ref_img = Image.open(ref_image_path).convert('RGB')
        ref_img = image_transform['val'](ref_img)
        ref_img = ref_img.detach().numpy()
        ref_img = torch.tensor([ref_img])

        # 特徴量を計算
        composed_features = net.module._extract_composed_features(ref_img, modifier, len_modifier)
        print("composed_features:", composed_features.shape)

        # データローダー
        demo_dataset = demoDataset(_DEFAULT_FASHION_IQ_DATASET_ROOT, 'dress', image_transform['val'])
        demo_sample_dataloader = demo_dataloader_factory(demo_dataset, configs)
        print("len:", len(demo_sample_dataloader))

        best_similarity_matrix = torch.Tensor().cuda()
        best_similarity_idx = torch.Tensor().cuda()
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
                similarity_matrix = torch.cat([best_similarity_matrix, similarity_matrix], dim=1)
                best_similarity_matrix, similarity_idx = similarity_matrix.topk(5)
                if i == 0:
                    for idx in similarity_idx[0]:
                        best_similarity_id.append(filename_list[idx])
                    best_similarity_idx = similarity_idx
                else:
                    similarity_id = []
                    for j in range(5):
                        if similarity_idx[0][j] < 5:
                            similarity_id.append(best_similarity_id[similarity_idx[0][j]])
                            similarity_idx[0][j] = best_similarity_idx[0][similarity_idx[0][j]]
                        else:
                            similarity_id.append(filename_list[similarity_idx[0][j] - 5])
                            similarity_idx[0][j] += i * 512 - 5
                    best_similarity_idx = similarity_idx
                    best_similarity_id = similarity_id
                if i % 10 == 0:
                    print(i, similarity_idx, best_similarity_matrix)
                    print(best_similarity_idx, best_similarity_id)
                del images, image_features, similarity_matrix, similarity_idx
                torch.cuda.empty_cache()
                if i % 10 == 0:
                    print(i)
                continue
                if i == 0:
                    best_similarity_matrix, best_similarity_idx = similarity_matrix.topk(1)
                else:
                    top_similarity_matrix, top_similarity_idx = similarity_matrix.topk(1)
                    if top_similarity_matrix > best_similarity_matrix:
                        best_similarity_matrix = top_similarity_matrix
                        best_similarity_idx = i * 64 + top_similarity_idx
                        best_similarity_id = filename_list[top_similarity_idx]
            best_similarity_matrix, best_similarity_idx = all_similarity_matrix.topk(5)
        print("best:", best_similarity_matrix, best_similarity_idx)
        best_similarity_id = all_file_name_list[best_similarity_idx[0][0]]
        #best_similarity_id = demo_dataset.img_list[best_similarity_idx[0][0]]
        result = {
            "new_image": best_similarity_id,
            "new_turn": False
        }
        return json.dumps(result)
        best_similarity_img_path = os.path.join(_DEFAULT_FASHION_IQ_DATASET_ROOT, '{}.png'.format(best_similarity_id))
        print(best_similarity_img_path)
        return best_similarity_img_path


@app.route("/favorite", methods=['GET', 'POST'])
def get_favorite_estimation():
    estimation = []
    for _ in range(5):
        random_image_id = _get_random_ref_image("dress")
        estimation.append(random_image_id)
    res = {
        "estimation": estimation
    }
    print(res)
    return json.dumps(res)

if __name__ == '__main__':    
    app.run(host="0.0.0.0", port=49876, use_reloader=True)
    #main()