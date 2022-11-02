import json
import os
from torch.utils.data import DataLoader, Dataset

from data.utils import _get_img_from_path

_DEFAULT_FASHION_IQ_DATASET_ROOT = 'static/image'
_DEFAULT_FASHION_IQ_VOCAB_PATH = '../FashionIQ_dataset/fashion_iq_vocab.pkl'


def _get_img_list(clothing_type):
    img_list = []
    dataset_root = _DEFAULT_FASHION_IQ_DATASET_ROOT
    with open(os.path.join('../FashionIQ_dataset', 'image_splits', 'split.{}.test.json'.format(clothing_type))) as json_file:
        img_list += json.load(json_file)
    with open(os.path.join('../FashionIQ_dataset', 'image_splits', 'split.{}.train.json'.format(clothing_type))) as json_file:
        img_list += json.load(json_file)
    return img_list


def _get_random_img_list(i):
    with open(os.path.join('demo', 'random', '{}.json'.format(str(i)))) as json_file:
        img_list = json.load(json_file)
    for i in range(len(img_list)):
        img_list[i] = img_list[i].split(".")[0]
    return img_list
    

def _create_img_path_from_id(root, id):
    return os.path.join(root, '{}.png'.format(id))


def _get_img_path_using_idx(img_caption_data, img_root, idx, is_ref=True):
    img_caption_pair = img_caption_data[idx]
    key = 'candidate' if is_ref else 'target'

    img = _create_img_path_from_id(img_root, img_caption_pair[key])
    id = img_caption_pair[key]
    return img, id


def demo_dataloader_factory(dataset, config, collate_fn=None):
    batch_size = 512
    num_workers = config.get('num_workers', 16)
    shuffle = config.get('shuffle', True)

    return DataLoader(dataset, batch_size, shuffle=shuffle, num_workers=num_workers, pin_memory=True,
                      collate_fn=collate_fn, drop_last=False)


class demoDataset(Dataset):
    def __init__(self, root_path=_DEFAULT_FASHION_IQ_DATASET_ROOT, clothing_type='dress',
                 img_transform=None):
        super().__init__()
        self.root_path = root_path
        self.img_root_path = os.path.join(self.root_path)
        self.clothing_type = clothing_type
        self.img_transform = img_transform

        self.img_list = _get_img_list(clothing_type)

    def __getitem__(self, idx, use_transform=True):
        img_transform = self.img_transform if use_transform else None
        img_id = self.img_list[idx]
        img_path = _create_img_path_from_id(self.img_root_path, img_id)

        target_img = _get_img_from_path(img_path, img_transform)

        return target_img, img_id

    def sample_img_for_visualizing(self, gt):
        img_path = _create_img_path_from_id(self.img_root_path, gt)
        img = _get_img_from_path(img_path, None)
        return img

    def __len__(self):
        return len(self.img_list)


class favarDataset(Dataset):
    def __init__(self, root_path=_DEFAULT_FASHION_IQ_DATASET_ROOT, index=0,
                 img_transform=None):
        super().__init__()
        self.root_path = root_path
        self.img_root_path = os.path.join(self.root_path)
        self.clothing_type = index
        self.img_transform = img_transform

        self.img_list = _get_random_img_list(index)

    def __getitem__(self, idx, use_transform=True):
        img_transform = self.img_transform if use_transform else None
        img_id = self.img_list[idx]
        img_path = _create_img_path_from_id(self.img_root_path, img_id)

        target_img = _get_img_from_path(img_path, img_transform)

        return target_img, img_id
    
    def __len__(self):
        return len(self.img_list)