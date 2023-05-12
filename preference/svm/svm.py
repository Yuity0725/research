from sklearn.svm import SVC
import numpy as np

def make_classifier(selected, filename_2_index, features):
    clf = SVC()
    labels = []
    images = []
    for id in selected.keys():
        try:
            index = filename_2_index[id]
        except KeyError:
            print(id)
            continue
        print(features[index[0]][index[1]].numpy().shape)
        images.append(np.ravel(features[index[0]][index[1]].numpy()))
        labels.append(selected[id])
    
    print(labels)
    print(len(images), images[0].shape)
    
    clf.fit(images, labels)
    
    test_estimation = clf.predict(images)
    print(test_estimation)
    
    return clf