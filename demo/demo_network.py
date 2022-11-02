import os
from PIL import Image
import torch

from bp import bp_img
from data import DEFAULT_VOCAB_PATHS
from demo.demo_model import Net_demo
from demo.demo_dataloader import demoDataset, demo_dataloader_factory
from language import vocabulary_factory
from models import create_models
from options import get_experiment_config
from set_up import setup_demo
from transforms import image_transform_factory, text_transform_factory


configs = get_experiment_config()
configs = setup_demo(configs)
vocabulary = vocabulary_factory(config={
    'vocab_path': configs['vocab_path'] if configs['vocab_path'] else DEFAULT_VOCAB_PATHS[configs['dataset']],
    'vocab_threshold': configs['vocab_threshold']
})
image_transform = image_transform_factory(config=configs)
text_transform = text_transform_factory(config={'vocabulary': vocabulary})

models = create_models(configs, vocabulary)
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
net = Net_demo(models).to(DEVICE)
if DEVICE == 'cuda':
    net = torch.nn.DataParallel(net) # make parallel
    torch.backends.cudnn.benchmark = True

# 推論モード
net.eval()

model_path = "experiments/test_cosmo_fashionIQDress_2022-05-29_6/best.pth"
model_params = torch.load(model_path)

model_param_key = model_params["model_state_dict"].keys()
model_params["model_state_dict"]["compositor"] = model_params["model_state_dict"]["layer4"]
del model_params["model_state_dict"]["layer4"]

new_model_params = {}
for key in model_params["model_state_dict"].keys():
    try:
        for key1 in model_params["model_state_dict"][key].keys():
            new_model_params["module." + key + ".module." + key1] = model_params["model_state_dict"][key][key1]
    except AttributeError:
        continue

net.load_state_dict(new_model_params)