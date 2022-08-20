from demo.demo_dataloader import demo_dataloader_factory, favarDataset
from demo.demo_network import configs, net, image_transform


_DEFAULT_FASHION_IQ_DATASET_ROOT = 'static/image'


def main():
    for i in range(11):
        sum_var = []
        print("index: ", i)
        dataset_candidate = favarDataset(_DEFAULT_FASHION_IQ_DATASET_ROOT, i, image_transform['val'])
        candidate_dataloader = demo_dataloader_factory(dataset_candidate, configs)
        for _, (images, filename_list) in enumerate(candidate_dataloader):
            image_features = net._extract_image_features(images)
            var_features = image_features.var(axis=0)
            sum_var.append(sum([float(v) for v in var_features]))
        print(sum_var)


if __name__ == "__main__":
    main()