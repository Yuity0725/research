from tqdm import tqdm

from trainers.abc import AbstractBaseTrainer
from utils.metrics import AverageMeterSet


class TIRGTrainer(AbstractBaseTrainer):
    def __init__(self, models, train_dataloader, criterions, optimizers, lr_schedulers, num_epochs,
                 train_loggers, val_loggers, evaluator, *args, **kwargs):
        super().__init__(models, train_dataloader, criterions, optimizers, lr_schedulers, num_epochs,
                         train_loggers, val_loggers, evaluator, *args, **kwargs)
        self.lower_image_encoder = self.models['lower_image_encoder']
        self.upper_image_encoder = self.models['upper_image_encoder']
        self.text_encoder = self.models['text_encoder']
        self.compositor = self.models['layer4']
        self.metric_loss = self.criterions['metric_loss']

    def print_self(self):
        print(self)

    def train_one_epoch(self, epoch):
        average_meter_set = AverageMeterSet()
        train_dataloader = tqdm(self.train_dataloader, desc="Epoch {}".format(epoch))

        for batch_idx, (ref_images, tar_images, modifiers, len_modifiers) in enumerate(train_dataloader):
            ref_images, tar_images = ref_images.to(self.device), tar_images.to(self.device)
            modifiers, len_modifiers = modifiers.to(self.device), len_modifiers.to(self.device)

            self._reset_grad()
            if batch_idx == 1:
                print("tar_images:", tar_images.shape)
                print("ref_images:", ref_images.shape)
                print("modifiers:", modifiers)
                print("len_modifiers:", len_modifiers)
            # Encode Target Images
            tar_mid_features, _ = self.lower_image_encoder(tar_images)
            if batch_idx == 1:
                print("tar_mid_features:", tar_mid_features.shape)
            tar_features = self.upper_image_encoder(tar_mid_features)
            if batch_idx == 1:
                print("tar_features:", tar_features.shape)

            # Encode and Fuse Reference Images with Texts
            ref_mid_features, _ = self.lower_image_encoder(ref_images)
            if batch_idx == 1:
                print("ref_mid_features:", ref_mid_features.shape)
            text_features = self.text_encoder(modifiers, len_modifiers)
            if batch_idx == 1:
                print("text_features:", text_features.shape)
            composed_ref_features, _ = self.compositor(ref_mid_features, text_features)
            if batch_idx == 1:
                print("composed_ref_features:", composed_ref_features.shape)
            composed_ref_features = self.upper_image_encoder(composed_ref_features)
            if batch_idx == 1:
                print("composed_ref_features:", composed_ref_features.shape)
                print(composed_ref_features[0])

            # Compute Loss
            loss = self.metric_loss(composed_ref_features, tar_features)
            loss.backward()
            average_meter_set.update('loss', loss.item())
            self._update_grad()

        self._step_schedulers()
        train_results = average_meter_set.averages()
        return train_results

    @classmethod
    def code(cls) -> str:
        return 'tirg'
