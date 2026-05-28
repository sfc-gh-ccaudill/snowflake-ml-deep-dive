"""
Shared Trainer class for all training entrypoints.

Provides a consistent train -> evaluate -> register workflow
so individual scripts only need to define their model and hyperparameters.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline
from snowflake.ml.model.task import Task
from snowflake.ml.registry import Registry
from snowflake.snowpark import Session

logger = logging.getLogger(__name__)


class Trainer:
    """Handles train, evaluate, and register for a sklearn-compatible model."""

    def __init__(self, session: Session, model, column_transformer=None):
        self.session = session
        self.model = model
        self.column_transformer = column_transformer
        self.metrics: Dict[str, float] = {}

    def train(self, X_train, y_train, **fit_kwargs):
        logger.info("Training %s ...", type(self.model).__name__)
        self.model.fit(X_train, y_train, **fit_kwargs)
        return self.model

    def evaluate(self, X_test, y_test) -> Dict[str, float]:
        y_pred = self.model.predict(X_test)
        self.metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "f1_macro": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
        }
        logger.info(
            "Results — accuracy: %.4f | f1_macro: %.4f",
            self.metrics["accuracy"],
            self.metrics["f1_macro"],
        )
        logger.info("\n%s", classification_report(y_test, y_pred, zero_division=0))
        return self.metrics

    def _build_registry_model(self):
        if self.column_transformer is not None:
            return Pipeline([("preprocessor", self.column_transformer), ("model", self.model)])
        return self.model

    def register(
        self,
        model_name: str,
        database: str,
        schema: str,
        sample_input: pd.DataFrame,
        dataset=None,
        metrics: Optional[Dict] = None,
        version_name: Optional[str] = None,
        comment: Optional[str] = None,
    ):
        version_name = version_name or f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        metrics = metrics or self.metrics
        comment = comment or f"Trained via ML Jobs — {datetime.now().isoformat()}"

        if dataset is not None:
            from modules.preprocess import FEATURE_COLS
            sample_input_data = dataset.read.to_snowpark_dataframe().select(FEATURE_COLS).limit(10)
            metrics["training_dataset_name"] = dataset.fully_qualified_name
            metrics["training_dataset_version"] = dataset.selected_version.name
        else:
            sample_input_data = sample_input

        registry_model = self._build_registry_model()

        logger.info("Registering model: %s / %s", model_name, version_name)
        registry = Registry(self.session, database_name=database, schema_name=schema)
        registry.log_model(
            model=registry_model,
            model_name=model_name,
            version_name=version_name,
            sample_input_data=sample_input_data,
            metrics=metrics,
            task=Task.TABULAR_MULTI_CLASSIFICATION,
            target_platforms=["WAREHOUSE", "SNOWPARK_CONTAINER_SERVICES"],
            comment=comment,
        )
        logger.info("Model registered: %s / %s", model_name, version_name)
