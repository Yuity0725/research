import logging

import numpy as np
import pandas as pd

from sklearn.linear_model import Lasso
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

logger = logging.getLogger('Log')
logger.setLevel(10)


df = pd.read_csv("preference/data/personal/female0.csv", header=0, index_col=0)

alphas = [5.0, 2.5, 1.0, 0.75, 0.5, 0.1]

for alpha in alphas:
    print(alpha)
    mse = np.array([])
    cnt = np.array([])
    for _ in range(5):
        df_train, df_test = train_test_split(df, test_size=0.2)

        x_train = df_train.iloc[:, 1:]
        x_test = df_test.iloc[:, 1:]

        y_train = df_train.iloc[:, 0]
        y_test = df_test.iloc[:, 0]

        # max_iterはデフォルトの100だと0.1以下で収束しない
        lss = Lasso(alpha, max_iter=15000)
        lss.fit(x_train, y_train)
        y_pred = lss.predict(x_test)

        mse = np.append(mse, mean_squared_error(y_test, y_pred))
        cnt = np.append(cnt, np.count_nonzero(lss.coef_))
    print(np.average(mse), mse)
    print(np.average(cnt), cnt)
