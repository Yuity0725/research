from torch import nn


# モデル
class Net_demo(nn.Module):
    def __init__(self, models):
        super(Net_demo, self).__init__()
        self.models = models
        self.lower_image_encoder = self.models['lower_image_encoder']
        self.upper_image_encoder = self.models['upper_image_encoder']
        self.text_encoder = self.models['text_encoder']
        self.compositor = self.models['layer4']
    
    def _extract_composed_features(self, image, modifiers, len_modifiers):
        print("image:", image.shape)
        mid_image_features, _ = self.lower_image_encoder(image)
        print("mid_image_features:", mid_image_features.shape)
        text_features = self.text_encoder(modifiers, len_modifiers)
        print("text_features:", text_features.shape)
        composed_features, _ = self.compositor(mid_image_features, text_features)
        print("composed_features:", composed_features.shape)
        composed_features = self.upper_image_encoder(composed_features)
        print("composed_features:",composed_features.shape)
        return composed_features
    
    def _extract_image_features(self, image):
        mid_image_features, _ = self.lower_image_encoder(image)
        image_features = self.upper_image_encoder(mid_image_features)
        return image_features
