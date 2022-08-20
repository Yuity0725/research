def main():
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
                new_model_params[key + ".module." + key1] = model_params["model_state_dict"][key][key1]
        except AttributeError:
            continue
    
    net.load_state_dict(new_model_params)

    # ランダムで画像を1枚持ってくる
    clothing_type = "dress"
    ref_image_path = _get_random_ref_image(clothing_type)
    ref_img = Image.open(ref_image_path).convert('RGB')
    ref_img = image_transform['val'](ref_img)
    ref_img = ref_img.detach().numpy()
    ref_img = torch.tensor([ref_img])

    # 修正指示文を入力
    print("modifier:")
    modifier = input()
    #modifier = "is more colorful and shorter sleeves and Is more floral and shorter sleeves"
    modifier = text_transform['val'](modifier)
    modifier = modifier.detach().numpy()
    len_modifier = torch.tensor([len(modifier)])
    modifier = torch.tensor([modifier])
    print("modifier:", modifier.shape)
    print("len_modifier:", len_modifier)
    composed_features = net._extract_composed_features(ref_img, modifier, len_modifier)
    print("composed_features:", composed_features.shape)
    tar_data = []

    # データローダー
    demo_dataset = demoDataset(_DEFAULT_FASHION_IQ_DATASET_ROOT, 'dress', image_transform['val'])
    demo_sample_dataloader = demo_dataloader_factory(demo_dataset, configs)
    print("len:", len(demo_sample_dataloader))
    best_similarity_matrix = torch.Tensor()
    best_similarity_idx = 0
    best_similarity_id = []
    for i, (images, filename_list) in enumerate(demo_sample_dataloader):
        image_features = net._extract_image_features(images)
        similarity_matrix = composed_features.mm(image_features.t())
        if i == 0:
            best_similarity_matrix, best_similarity_idx = similarity_matrix.topk(1)
            best_similarity_id = filename_list[best_similarity_idx]
            print(best_similarity_matrix, best_similarity_idx, best_similarity_id)
        else:
            #similarity_matrix = torch.cat((top_similarity_matrix, similarity_matrix), 1)
            top_similarity_matrix, top_similarity_idx = similarity_matrix.topk(1)
            if top_similarity_matrix > best_similarity_matrix:
                best_similarity_matrix = top_similarity_matrix
                best_similarity_idx = i * 32 + top_similarity_idx
                best_similarity_id = filename_list[top_similarity_idx]
        del image_features, similarity_matrix
        
    print("best:", best_similarity_matrix, best_similarity_idx)
    best_similarity_img_path = os.path.join(_DEFAULT_FASHION_IQ_DATASET_ROOT, 'images', '{}.png'.format(best_similarity_id))
    print(best_similarity_img_path)
