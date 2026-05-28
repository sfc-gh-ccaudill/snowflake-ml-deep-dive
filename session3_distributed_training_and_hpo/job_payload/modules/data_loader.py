"""
Shared data loading module for all training entrypoints.

Handles loading training data from either a Feature Store Dataset
(preserving lineage) or a plain Snowflake table, plus test data
from a table. Normalizes column names to uppercase.
"""

import logging
from datetime import datetime

import pandas as pd
from snowflake.snowpark import Session

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads train/test DataFrames from Snowflake."""

    def __init__(self, session: Session, database: str, schema: str):
        self.session = session
        self.database = database
        self.schema = schema

    def _fqn(self, name: str) -> str:
        return f"{self.database}.{self.schema}.{name}"

    @staticmethod
    def _normalize(df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [c.upper() for c in df.columns]
        return df

    def _get_latest_dataset_version(self, dataset_name: str) -> str:
        fqn = self._fqn(dataset_name)
        rows = self.session.sql(f"SHOW VERSIONS IN DATASET {fqn}").collect()
        if not rows:
            raise ValueError(f"No versions found for dataset {fqn}")
        latest = rows[-1]["version"]
        logger.info("Resolved latest dataset version: %s", latest)
        return latest

    def _load_dataset(self, dataset_name: str, version: str = None):
        from snowflake.ml.dataset import load_dataset

        if version is None:
            version = self._get_latest_dataset_version(dataset_name)

        logger.info("Loading dataset: %s (version=%s)", dataset_name, version)
        ds = load_dataset(self.session, self._fqn(dataset_name), version=version)
        df = self._normalize(ds.read.to_pandas())
        logger.info("  Rows: %d", len(df))
        return df, ds

    def generate_training_dataset(
        self,
        dataset_name: str = "PATIENT_TRAINING_DATASET",
        feature_view_name: str = "PATIENT_FEATURES",
        feature_view_version: str = "v1",
        spine_table: str = "RAW_PATIENT_DATA",
        spine_timestamp_col: str = "TIMESTAMP",
        spine_label_cols: list = None,
        dataset_version: str = None,
    ) -> str:
        from snowflake.ml.feature_store import FeatureStore

        spine_label_cols = spine_label_cols or ["RISK_LEVEL"]
        if dataset_version is None:
            dataset_version = datetime.now().strftime("v_%Y%m%d_%H%M%S")

        logger.info("Generating training dataset from Feature Store")
        logger.info("  Feature view: %s (version=%s)", feature_view_name, feature_view_version)
        logger.info("  Spine table: %s", spine_table)
        logger.info("  Dataset: %s (version=%s)", dataset_name, dataset_version)

        warehouse = self.session.get_current_warehouse()
        fs = FeatureStore(self.session, self.database, self.schema, default_warehouse=warehouse)
        fv = fs.get_feature_view(feature_view_name, feature_view_version)

        spine_df = self.session.table(self._fqn(spine_table)).select(
            "PATIENT_ID", spine_timestamp_col, *spine_label_cols
        )

        ds = fs.generate_dataset(
            name=self._fqn(dataset_name),
            spine_df=spine_df,
            features=[fv],
            spine_timestamp_col=spine_timestamp_col,
            spine_label_cols=spine_label_cols,
            version=dataset_version,
        )

        logger.info("  Dataset generated: %s/%s", dataset_name, dataset_version)
        return dataset_version

    def load_table(self, table_name: str) -> pd.DataFrame:
        logger.info("Loading table: %s", table_name)
        df = self._normalize(self.session.table(table_name).to_pandas())
        logger.info("  Rows: %d", len(df))
        return df

    def load_train_test(
        self,
        train_dataset_name: str = None,
        train_dataset_version: str = None,
        train_table_name: str = None,
        test_table_name: str = "TEST_FEATURES",
    ) -> tuple:
        dataset = None
        if train_dataset_name:
            train_df, dataset = self._load_dataset(train_dataset_name, version=train_dataset_version)
        elif train_table_name:
            train_df = self.load_table(train_table_name)
        else:
            raise ValueError("Provide either train_dataset_name or train_table_name")

        test_df = self.load_table(test_table_name)
        return train_df, test_df, dataset
