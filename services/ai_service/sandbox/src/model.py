import numpy as np

class LinearRegression:
    def __init__(self):
        self.coeff = None

    def fit(self, X, y):
        # Simple linear regression implementation
        self.coeff = np.mean(y) / np.mean(X)

    def predict(self, X):
        return [x * self.coeff for x in X]