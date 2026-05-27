import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session


@dataclass
class SnowflakeConfig:
    connection_name: str
    database: str
    schema_name: str
    warehouse: str


@dataclass
class ComputeConfig:
    compute_pool: str
    instance_family: str
    min_nodes: int
    max_nodes: int


@dataclass
class FeatureConfig:
    raw_numeric_features: List[str]
    categorical_features: List[str]
    computed_features: List[str]
    target_column: str
    class_labels: List[str]


@dataclass
class StagesConfig:
    job_payloads: str = "JOB_PAYLOADS"


@dataclass
class TablesConfig:
    raw_data: str = "RAW_PATIENT_DATA"
    test_features: str = "TEST_FEATURES"


@dataclass
class ModelConfig:
    model_name: str = "PATIENT_RISK_MODEL"
    target_platforms: List[str] = field(default_factory=lambda: ["SNOWPARK_CONTAINER_SERVICES"])


@dataclass
class DeployConfig:
    service_name: str = "PATIENT_RISK_SERVICE"
    min_instances: int = 1
    max_instances: int = 1
    auto_suspend_secs: int = 3600


@dataclass
class EvaluationConfig:
    accuracy_threshold: float = 0.80
    f1_macro_threshold: float = 0.75


@dataclass
class DriftAlertConfig:
    alert_name: str = "PREDICTION_DRIFT_ALERT"
    column: str = "RISK_LEVEL"
    drift_metric: str = "POPULATION_STABILITY_INDEX"
    drift_threshold: float = 0.25
    schedule: str = "USING CRON 0 6 * * * America/Los_Angeles"


@dataclass
class MonitorConfig:
    monitor_name: str = "PATIENT_RISK_MONITOR"
    inference_logs_view: str = "INFERENCE_LOGS_VIEW"
    baseline_table: str = "MONITOR_BASELINE"
    drift_alert_enabled: bool = True
    retrain_root_task: str = "PIPELINE_FEATURE_ENG_TASK"
    drift_alerts: List[DriftAlertConfig] = field(default_factory=list)


@dataclass
class WorkshopConfig:
    snowflake: SnowflakeConfig
    compute: ComputeConfig
    features: FeatureConfig
    stages: StagesConfig
    tables: TablesConfig = field(default_factory=TablesConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    deploy: DeployConfig = field(default_factory=DeployConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)

    @property
    def full_raw_table(self) -> str:
        return f"{self.snowflake.database}.{self.snowflake.schema_name}.{self.tables.raw_data}"


def get_config(config_path: str = "config.yaml") -> WorkshopConfig:
    with open(config_path, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f)

    sf = d.get("snowflake", {})
    if not sf.get("connection_name"):
        sf["connection_name"] = os.getenv("SNOWFLAKE_CONNECTION_NAME", "default")

    tables_d = d.get("tables", {})
    model_d = d.get("model", {})
    deploy_d = d.get("deploy", {})
    eval_d = d.get("evaluation", {})
    monitor_d = d.get("monitor", {})

    drift_alerts = [
        DriftAlertConfig(**{k: v for k, v in a.items() if k in ("alert_name", "column", "drift_metric", "drift_threshold", "schedule")})
        for a in monitor_d.get("drift_alerts", [])
    ]

    return WorkshopConfig(
        snowflake=SnowflakeConfig(
            connection_name=sf.get("connection_name", ""),
            database=sf.get("database"),
            schema_name=sf.get("schema"),
            warehouse=sf.get("warehouse"),
        ),
        compute=ComputeConfig(**{k: v for k, v in d.get("compute", {}).items()}),
        features=FeatureConfig(**{k: v for k, v in d.get("features", {}).items()}),
        stages=StagesConfig(**{k: v for k, v in d.get("stages", {}).items() if k in ("job_payloads",)}),
        tables=TablesConfig(**{k: v for k, v in tables_d.items() if k in ("raw_data", "test_features")}),
        model=ModelConfig(
            model_name=model_d.get("model_name", "PATIENT_RISK_MODEL"),
            target_platforms=model_d.get("target_platforms", ["SNOWPARK_CONTAINER_SERVICES"]),
        ),
        deploy=DeployConfig(
            service_name=deploy_d.get("service_name", "PATIENT_RISK_SERVICE"),
            min_instances=deploy_d.get("min_instances", 1),
            max_instances=deploy_d.get("max_instances", 1),
            auto_suspend_secs=deploy_d.get("auto_suspend_secs", 3600),
        ),
        evaluation=EvaluationConfig(
            accuracy_threshold=eval_d.get("accuracy_threshold", 0.80),
            f1_macro_threshold=eval_d.get("f1_macro_threshold", 0.75),
        ),
        monitor=MonitorConfig(
            monitor_name=monitor_d.get("monitor_name", "PATIENT_RISK_MONITOR"),
            inference_logs_view=monitor_d.get("inference_logs_view", "INFERENCE_LOGS_VIEW"),
            baseline_table=monitor_d.get("baseline_table", "MONITOR_BASELINE"),
            drift_alert_enabled=monitor_d.get("drift_alert_enabled", True),
            retrain_root_task=monitor_d.get("retrain_root_task", "PIPELINE_FEATURE_ENG_TASK"),
            drift_alerts=drift_alerts,
        ),
    )


def get_session(
    connection_name: Optional[str] = None,
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
    warehouse_name: Optional[str] = None,
) -> Session:
    try:
        session = get_active_session()
    except Exception:
        if connection_name is None:
            connection_name = os.getenv("SNOWFLAKE_CONNECTION_NAME")
        session = Session.builder.config("connection_name", connection_name).create()

    if database_name:
        session.use_database(database_name)
    if schema_name:
        session.use_schema(schema_name)
    if warehouse_name:
        session.use_warehouse(warehouse_name)

    return session


def get_feature_config(config: WorkshopConfig) -> Dict[str, Any]:
    fc = config.features
    return {
        "raw_numeric_features": fc.raw_numeric_features,
        "categorical_features": fc.categorical_features,
        "computed_features": fc.computed_features,
        "all_numeric_features": fc.raw_numeric_features
        + ["SHOCK_INDEX", "PULSE_PRESSURE", "VITAL_SIGNS_SEVERITY"],
        "all_categorical_features": fc.categorical_features + ["BMI_CATEGORY"],
        "target_column": fc.target_column,
        "class_labels": fc.class_labels,
        "id_columns": ["PATIENT_ID", "ENCOUNTER_ID"],
        "timestamp_column": "TIMESTAMP",
    }
