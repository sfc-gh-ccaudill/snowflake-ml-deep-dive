# Snowflake ML Deep Dive — Workshop Series

Hands-on workshops exploring Snowflake's machine learning capabilities in depth. Each session is a standalone set of notebooks that teaches one area of the ML platform through guided, interactive examples.

**Use case**: Patient Risk Stratification (same domain as the [production pipeline repo](https://github.com/ccaudill/snowflake-ml-pipeline)) — classifying patients as LOW/MEDIUM/HIGH/CRITICAL risk from clinical vitals.

> **Looking for the end-to-end production pipeline?**
> See [snowflake-ml-pipeline](https://github.com/ccaudill/snowflake-ml-pipeline) — a complete production-grade ML pipeline with Feature Store, distributed training, model serving, drift monitoring, and automated retraining, all orchestrated by Snowflake Tasks. Session 1 of this workshop series provides the overview of that system.

---

## Workshop Sessions

| Session | Topic | Notebooks | Presentation |
|---------|-------|-----------|--------------|
| **1** | End-to-End ML Pipeline Overview | *(see [snowflake-ml-pipeline](https://github.com/ccaudill/snowflake-ml-pipeline))* | *(in pipeline repo)* |
| **2** | Feature Store & Experiment Tracking | `session2_features_and_experiments/` | `docs/presentations/session2/` |
| **3** | ML Jobs, Distributed Training & HPO | `session3_distributed_training_and_hpo/` | `docs/presentations/session3/` |
| **4** | Model Deployment, Inference & MLOps | `session4_deployment_inference_and_mlops/` | `docs/presentations/session4/` |

---

## Session 2: Feature Store & Experiment Tracking

| Notebook | Duration | What You Learn |
|----------|----------|----------------|
| 01 - Feature Engineering Fundamentals | ~20 min | Snowflake Feature Store entities, feature views, time-travel |
| 02 - Feature Store Advanced | ~20 min | Managed refresh, versioning, training datasets, point-in-time joins |
| 03 - Experiment Tracking | ~25 min | Snowflake Experiments API, run comparison, artifact logging |
| 04 - Model Registry Integration | ~20 min | Registry API, model versions, metrics, lineage from experiments |

## Session 3: ML Jobs, Distributed Training & HPO

| Notebook | Duration | What You Learn |
|----------|----------|----------------|
| 01 - ML Jobs: Source Directory | ~15 min | `submit_directory()` to run local Python on SPCS compute pools |
| 02 - ML Jobs: Dockerfile | ~15 min | Custom Docker images for ML Jobs with pip dependencies |
| 03 - Distributed Training | ~20 min | Multi-node training with Ray on SPCS |
| 04 - Hyperparameter Optimization | ~25 min | Ray Tune + ASHA scheduler on SPCS |

## Session 4: Deployment, Inference & MLOps

| Notebook | Duration | What You Learn |
|----------|----------|----------------|
| 01 - Model Deployment | ~20 min | Model serving on SPCS, REST endpoints, auto-suspend |
| 02 - Inference | ~15 min | Batch inference, real-time REST calls, streaming patterns |
| 03 - Model Monitoring | ~25 min | Drift detection, PSI metrics, automated alerting & retraining |

---

## Prerequisites

- Snowflake account with SPCS (Snowpark Container Services) enabled
- Snowflake CLI (`snow`) installed and configured
- Python 3.10+
- `snowflake-ml-python` package
- **Data**: The workshops expect `ML_DEMO_PIPELINE_DB.HEALTHCARE.RAW_PATIENT_DATA` and related tables to exist. Run setup (below) or use the [pipeline repo](https://github.com/ccaudill/snowflake-ml-pipeline) to generate data.

---

## Setup

### 1. Provision infrastructure (one-time)

Run the SQL in `setup/setup.sql` via Snowsight or the Snowflake CLI:

```bash
snow sql -f setup/setup.sql
```

### 2. Configure your connection

Edit `config.yaml` and set `connection_name` to match your Snowflake CLI connection:

```yaml
snowflake:
  connection_name: DEMO  # your connection name here
```

### 3. Run notebooks

Each session's notebooks are numbered and meant to be run in order. Open in VS Code, JupyterLab, or Snowflake Notebooks.

```bash
cd session2_features_and_experiments
jupyter lab
```

---

## Directory Structure

```
snowflake-ml-deep-dive/
├── config.yaml                              # Shared configuration (connection, compute, features)
├── utils/                                   # Lightweight session & config utilities
│   ├── __init__.py
│   └── session_utils.py
├── setup/
│   └── setup.sql                            # Idempotent infrastructure DDL
├── session2_features_and_experiments/
│   ├── 01_feature_engineering_fundamentals.ipynb
│   ├── 02_feature_store_advanced.ipynb
│   ├── 03_experiment_tracking.ipynb
│   ├── 04_model_registry_integration.ipynb
│   └── experiment_utils.py
├── session3_distributed_training_and_hpo/
│   ├── 01_ml_jobs_source_directory.ipynb
│   ├── 02_ml_jobs_dockerfile.ipynb
│   ├── 03_distributed_training.ipynb
│   ├── 04_hyperparameter_optimization.ipynb
│   └── job_payload/                         # Self-contained training scripts for ML Jobs
├── session4_deployment_inference_and_mlops/
│   ├── 01_model_deployment.ipynb
│   ├── 02_inference.ipynb
│   └── 03_model_monitoring.ipynb
└── docs/
    └── presentations/
        ├── session2/
        ├── session3/
        └── session4/
```

---

## Relationship to snowflake-ml-pipeline

This repo teaches **how individual Snowflake ML features work**. The [snowflake-ml-pipeline](https://github.com/ccaudill/snowflake-ml-pipeline) repo shows **how to compose them into a production system**.

| | This Repo (Deep Dive) | Pipeline Repo |
|---|---|---|
| **Purpose** | Teach ML platform features | Show production architecture |
| **Format** | Interactive notebooks with explanations | Framework code + Task DAG |
| **Audience** | "How does Feature Store work?" | "What does production ML look like?" |
| **Dependencies** | Self-contained per session | Full integrated system |
