---
name: ml-from-scratch
description: Use when implementing ML algorithms from first principles, learning how models work internally, or building NumPy-based ML code without frameworks.
---

# ML From Scratch

## Overview
Build machine learning algorithms using only NumPy to gain deep understanding of how models actually work under the hood. Prioritize transparency over efficiency.

## When to Use
- You want to understand how gradient descent, backprop, or SVMs actually work
- You're learning ML and want to go beyond sklearn/PyTorch black boxes
- You need to explain or teach an algorithm step by step
- You're building a minimal proof-of-concept without framework overhead

## Core Categories

### Supervised Learning
- Linear Regression, Logistic Regression
- Decision Trees, Random Forest, Gradient Boosting, XGBoost
- Support Vector Machines (SVM)
- K-Nearest Neighbors
- Neural Networks (fully custom with backprop)

### Unsupervised Learning
- K-Means, DBSCAN (clustering)
- PCA (dimensionality reduction)
- Autoencoders, GANs (generative models)

### Reinforcement Learning
- Deep Q-Network (DQN)

### Deep Learning Building Blocks
- Dense, Convolutional, Recurrent layers
- Batch Normalization, Dropout
- Optimizers: SGD, Adam, RMSProp

## Implementation Pattern

```python
import numpy as np

class LinearRegression:
    def fit(self, X, y, lr=0.01, epochs=1000):
        self.w = np.zeros(X.shape[1])
        self.b = 0
        for _ in range(epochs):
            y_pred = X @ self.w + self.b
            dw = (2/len(y)) * X.T @ (y_pred - y)
            db = (2/len(y)) * np.sum(y_pred - y)
            self.w -= lr * dw
            self.b -= lr * db

    def predict(self, X):
        return X @ self.w + self.b
```

## Key Principles
1. **Vectorize everything** — avoid Python loops, use NumPy broadcasting
2. **Numerical stability** — clip values before log/exp operations
3. **Gradient check** — verify backprop with finite differences
4. **No magic** — every operation should be derivable from the math

## Reference
Source: [eriklindernoren/ML-From-Scratch](https://github.com/eriklindernoren/ML-From-Scratch) — 31K stars
