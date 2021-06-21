import json

import os

from data.utils import _get_img_from_path
from data.abc import AbstractBaseDataset, AbstractBaseTestDataset

_DEFAULT_FASHION_IQ_DATASET_ROOT = '/data/image_retrieval/fashionIQ'
_DEFAULT_FASHION_IQ_VOCAB_PATH = '/data/image_retrieval/fashionIQ/fashion_iq_vocab.pkl'


def _get_img_caption_json(dataset_root, clothing_type, split):
    with open(os.path.join(dataset_root, 'captions', 'cap.{}.{}.json'.format(clothing_type, split))) as json_file:
        img_caption_data = json.load(json_file)
    return img_caption_data


def _get_img_split_json_as_list(dataset_root, clothing_type, split):
    with open(os.path.join(dataset_root, 'image_splits', 'split.{}.{}.json'.format(clothing_type, split))) as json_file:
        img_split_list = json.load(json_file)
    return img_split_list


def _create_img_path_from_id(root, id):
    return os.path.join(root, '{}.png'.format(id))


def _get_img_path_using_idx(img_caption_data, img_root, idx, is_ref=True):
    img_caption_pair = img_caption_data[idx]
    key = 'candidate' if is_ref else 'target'

    img = _create_img_path_from_id(img_root, img_caption_pair[key])
    id = img_caption_pair[key]
    return img, id


def _get_modifier(img_caption_data, idx, reverse=False):
    img_caption_pair = img_caption_data[idx]
    cap1, cap2 = img_caption_pair['captions']
    return _create_modifier_from_attributes(cap1, cap2) if not reverse else _create_modifier_from_attributes(cap2, cap1)


def _create_modifier_from_attributes(ref_attribute, targ_attribute):
    return ref_attribute + " and " + targ_attribute


class AbstractBaseFashionIQDataset(AbstractBaseDataset):

    @classmethod
    def code(cls):
        return 'fashionIQ'

    @classmethod
    def all_codes(cls):
        return ['fashionIQ_dress', 'fashionIQ_shirt', 'fashionIQ_toptee']

    @classmethod
    def vocab_path(cls):
        return _DEFAULT_FASHION_IQ_VOCAB_PATH


class FashionIQDataset(AbstractBaseFashionIQDataset):
    """
    Fashion200K dataset.
    Image pairs in {root_path}/image_pairs/{split}_pairs.pkl

    """

    def __init__(self, root_path=_DEFAULT_FASHION_IQ_DATASET_ROOT, clothing_type='dress', split='train',
                 img_transform=None, text_transform=None):
        super().__init__(root_path, split, img_transform, text_transform)
        self.root_path = root_path
        self.img_root_path = os.path.join(self.root_path, 'images')
        self.clothing_type = clothing_type
        self.split = split
        self.img_transform = img_transform
        self.text_transform = text_transform
        self.img_caption_data = _get_img_caption_json(root_path, clothing_type, split)

    def __getitem__(self, idx):
        safe_idx = idx // 2
        reverse = (idx % 2 == 1)

        ref_img_path, _ = _get_img_path_using_idx(self.img_caption_data, self.img_root_path, safe_idx, is_ref=True)
        targ_img_path, _ = _get_img_path_using_idx(self.img_caption_data, self.img_root_path, safe_idx, is_ref=False)
        reference_img = _get_img_from_path(ref_img_path, self.img_transform)
        target_img = _get_img_from_path(targ_img_path, self.img_transform)

        modifier = _get_modifier(self.img_caption_data, safe_idx, reverse=reverse)
        modifier = self.text_transform(modifier) if self.text_transform else modifier

        return reference_img, target_img, modifier, len(modifier)

    def get_original_item(self, idx):
        safe_idx = idx // 2
        reverse = (idx % 2 == 1)

        ref_img_path, _ = _get_img_path_using_idx(self.img_caption_data, self.img_root_path, safe_idx, is_ref=True)
        targ_img_path, _ = _get_img_path_using_idx(self.img_caption_data, self.img_root_path, safe_idx, is_ref=False)
        reference_img = _get_img_from_path(ref_img_path)
        target_img = _get_img_from_path(targ_img_path)

        modifier = _get_modifier(self.img_caption_data, safe_idx, reverse=reverse)

        return reference_img, target_img, modifier, len(modifier)

    def __len__(self):
        return len(self.img_caption_data) * 2


class FashionIQTestDataset(AbstractBaseFashionIQDataset, AbstractBaseTestDataset):
    """
    FashionIQ Test (Samples) dataset.
    indexing returns target samples and their unique ID
    """

    def __init__(self, root_path=_DEFAULT_FASHION_IQ_DATASET_ROOT, clothing_type='dress', split='val',
                 img_transform=None, text_transform=None):
        super().__init__(root_path, split, img_transform, text_transform)
        self.root_path = root_path
        self.img_root_path = os.path.join(self.root_path, 'images')
        self.clothing_type = clothing_type
        self.img_transform = img_transform
        self.text_transform = text_transform

        self.img_list = _get_img_split_json_as_list(root_path, clothing_type, split)

        ''' Uncomment below for VAL Evaluation method '''
        # self.img_caption_data = _get_img_caption_json(root_path, clothing_type, split)
        # self.img_list = []
        # for d in self.img_caption_data:
        #     self.img_list.append(d['target'])
        #     self.img_list.append(d['candidate'])
        # self.img_list = list(set(self.img_list))

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


class FashionIQTestQueryDataset(AbstractBaseFashionIQDataset):
    """
        FashionIQ Test (Query) dataset.
        indexing returns ref samples, modifier, target attribute (caption, text) and modifier length
        """

    def __init__(self, root_path=_DEFAULT_FASHION_IQ_DATASET_ROOT, clothing_type='dress', split='val',
                 img_transform=None, text_transform=None):
        super().__init__(root_path, split, img_transform, text_transform)
        self.root_path = root_path
        self.img_root_path = os.path.join(self.root_path, 'images')
        self.clothing_type = clothing_type
        self.img_transform = img_transform
        self.text_transform = text_transform

        self.img_caption_data = _get_img_caption_json(root_path, clothing_type, split)

    def __getitem__(self, idx, use_transform=True):
        safe_idx = idx // 2
        reverse = (idx % 2 == 1)

        img_transform = self.img_transform if use_transform else None
        text_transform = self.text_transform if use_transform else None
        ref_img_path, ref_id = _get_img_path_using_idx(self.img_caption_data, self.img_root_path, safe_idx, is_ref=True)
        targ_img_path, targ_id = _get_img_path_using_idx(self.img_caption_data, self.img_root_path, safe_idx,
                                                         is_ref=False)
        ref_img = _get_img_from_path(ref_img_path, img_transform)

        modifier = _get_modifier(self.img_caption_data, safe_idx, reverse=reverse)
        modifier = text_transform(modifier) if text_transform else modifier

        return ref_img, ref_id, modifier, targ_id, len(modifier)

    def __len__(self):
        return len(self.img_caption_data) * 2
