---
name: mlops-production
description: Use when moving ML models from notebooks to production, setting up MLOps pipelines, or applying software engineering practices to machine learning systems.
---

# MLOps & Production ML

## Overview
Production ML requires combining data science knowledge with software engineering discipline. The gap between a working notebook and a reliable deployed system is enormous — this skill bridges it.

## When to Use
- Moving a model from Jupyter notebook to a deployed service
- Setting up experiment tracking, versioning, or CI/CD for ML
- Building reproducible training pipelines
- Preparing for ML system design interviews

## Production ML Lifecycle

```
Data → Training → Evaluation → Serving → Monitoring → Iteration
  ↑___________________________________________________|
```

### 1. Data
- Version datasets (DVC, Delta Lake)
- Validate schemas and distributions
- Document lineage and transformations

### 2. Training
- Parameterize everything (no hardcoded values)
- Log all experiments with MLflow
- Use distributed training (Ray) for scale

```python
import mlflow

mlflow.set_experiment("my-model")
with mlflow.start_run():
    mlflow.log_param("lr", 0.01)
    mlflow.log_metric("accuracy", 0.95)
    mlflow.sklearn.log_model(model, "model")
```

### 3. Evaluation
- Slice-based evaluation (not just overall accuracy)
- Behavioral testing (invariance, directional, minimum functionality)
- Compare against baselines and previous versions

### 4. Serving
- Expose via REST API (FastAPI)
- Containerize with Docker
- Separate inference from training code

```python
from fastapi import FastAPI
app = FastAPI()

@app.post("/predict")
def predict(payload: PredictRequest):
    return {"prediction": model.predict([payload.features])[0]}
```

### 5. Monitoring
- Track prediction drift and data drift
- Alert on performance degradation
- Log inputs/outputs for retraining

## Key Tools

| Need | Tool |
|------|------|
| Experiment tracking | MLflow |
| Distributed training | Ray |
| Testing | pytest |
| Serving | FastAPI |
| Orchestration | Airflow / Prefect |
| Containerization | Docker |

## Engineering Standards
- Write Python scripts, not just notebooks
- Test data pipelines, not just model accuracy
- Pin all dependency versions
- Never hardcode credentials or file paths

## Reference
Source: [GokuMohandas/Made-With-ML](https://github.com/GokuMohandas/Made-With-ML) — Serves 40K+ developers
