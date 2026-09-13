# Dependency Inventory (Raw) — Phase 3A (Read-Only)

- Generated: 2026-09-13
- Method: automated AST import extraction (`ast.parse`); no environment changes, no installs, no locks, no Git operations.
- Scope read: `pyproject.toml`, all `requirements*.txt` (7 files), `Dockerfile`, `Dockerfile.dev`, build/test workflows (`ci.yml`, `commit-check.yml`, `release.yml`, `pre-deploy-validation.yml`, `migration-safety.yml`), and Python sources under `src/`, `main.py`, `tests/`, `tools/ctrader_smoke_test/`, `scripts/`.
- Files scanned for imports: **295**; parse errors: **0**
- This is a documented inventory only. It is not a fix/unification phase. Phase 3B requires explicit approval.

## 1. Import classification summary

- Python standard library modules used: 42 → `__future__`, `abc`, `argparse`, `ast`, `asyncio`, `collections`, `contextlib`, `copy`, `csv`, `dataclasses`, `datetime`, `decimal`, `enum`, `functools`, `getpass`, `hashlib`, `importlib`, `inspect`, `io`, `json`, `logging`, `math`, `os`, `pathlib`, `platform`, `random`, `re`, `shutil`, `sqlite3`, `stat`, `subprocess`, `sys`, `tarfile`, `tempfile`, `time`, `tomllib`, `traceback`, `typing`, `unittest`, `urllib`, `uuid`, `zoneinfo`
- First-party modules/packages imported: `main, scripts, src, tools` plus relative imports (all resolve inside the repo).
- Distinct third-party top-level import names found: **32**

## 2. Third-party packages actually imported (with files)

Import name → declared distribution name shown when the mapping is non-1:1 (all mappings below are unambiguous; nothing required guessing).

### `MetaTrader5`
Files (3):
  - src/providers/mt5/market_data.py
  - src/trading/mt5_connector.py
  - tests/test_system_bootstrap_to_execution.py

### `alembic`
Files (1):
  - scripts/verify_migrations.py

### `ctrader_open_api`  (distribution: `ctrader-open-api`)
Files (5):
  - tools/ctrader_smoke_test/historical_data.py
  - tools/ctrader_smoke_test/smoke_test.py
  - tools/ctrader_smoke_test/spot_stream.py
  - tools/ctrader_smoke_test/symbol_discovery.py
  - tools/ctrader_smoke_test/symbol_schedule_reconciliation.py

### `dotenv`  (distribution: `python-dotenv`)
Files (7):
  - scripts/doctor.py
  - scripts/generate_incident_report.py
  - tools/ctrader_smoke_test/historical_data.py
  - tools/ctrader_smoke_test/smoke_test.py
  - tools/ctrader_smoke_test/spot_stream.py
  - tools/ctrader_smoke_test/symbol_discovery.py
  - tools/ctrader_smoke_test/symbol_schedule_reconciliation.py

### `fastapi`
Files (2):
  - src/core/health.py
  - tests/test_health.py

### `gymnasium`
Files (2):
  - src/environment/gym_env.py
  - src/trading/trading_env.py

### `httpx`
Files (3):
  - scripts/smoke_test.py
  - src/data/event_intelligence.py
  - tests/test_release_readiness_tools.py

### `jinja2`
Files (1):
  - src/research/reporting.py

### `joblib`
Files (2):
  - src/models/regime_detector.py
  - tests/test_security_mitigation.py

### `metaapi_cloud_sdk`  (distribution: `metaapi-cloud-sdk`)
Files (1):
  - src/trading/mt5_connector.py

### `nest_asyncio`  (distribution: `nest-asyncio`)
Files (1):
  - src/trading/mt5_connector.py

### `numpy`
Files (66):
  - scripts/benchmark_db.py
  - scripts/benchmark_hotspots.py
  - scripts/doctor.py
  - scripts/generate_research_report.py
  - scripts/verify_backtest_audit.py
  - scripts/verify_benchmarking.py
  - scripts/verify_hyperopt_walkforward.py
  - scripts/verify_stress_lab.py
  - src/analytics/execution_quality.py
  - src/analytics/journal_mining.py
  - src/core/feature_engineering.py
  - src/core/trade_logger.py
  - src/environment/gym_env.py
  - src/models/base_model.py
  - src/models/calibration.py
  - src/models/dreamer_agent.py
  - src/models/dynamic_ensemble.py
  - src/models/ensemble.py
  - src/models/lstm_model.py
  - src/models/ppo_agent.py
  - src/models/regime_detector.py
  - src/models/transformer_model.py
  - src/research/benchmark_demo.py
  - src/research/benchmarks.py
  - src/research/hyperopt_walkforward.py
  - src/research/rare_event_simulator.py
  - src/research/rl_evaluation.py
  - src/research/rl_evaluation_demo.py
  - src/research/stress_lab.py
  - src/trading/backtester.py
  - src/trading/execution_filter.py
  - src/trading/trading_env.py
  - src/utils/synthetic_data.py
  - tests/conftest.py
  - tests/test_adaptive_feedback_loop.py
  - tests/test_backtest_auditing.py
  - tests/test_backtest_reporting_pipeline.py
  - tests/test_backtest_slope_optimization.py
  - tests/test_backtester.py
  - tests/test_backtester_institutional.py
  - tests/test_backtester_new.py
  - tests/test_benchmarks.py
  - tests/test_benchmarks_extended.py
  - tests/test_calibration.py
  - tests/test_data_pipeline_integration.py
  - tests/test_decision_pipeline_integration.py
  - tests/test_enterprise_audit_integration.py
  - tests/test_env_consistency.py
  - tests/test_execution_filter.py
  - tests/test_feature_engineering.py
  - tests/test_hyperopt_walkforward.py
  - tests/test_integration_flow.py
  - tests/test_model_robustness.py
  - tests/test_models_stubs.py
  - tests/test_mtf_synthetic_data.py
  - tests/test_performance_instrumentation.py
  - tests/test_performance_optimizations.py
  - tests/test_rare_event_simulator.py
  - tests/test_regime_detector.py
  - tests/test_reporting_integration.py
  - tests/test_rl_evaluation.py
  - tests/test_stress_lab.py
  - tests/test_synthetic_data.py
  - tests/test_system_bootstrap_to_execution.py
  - tests/test_trading_env_optimization.py
  - tests/verify_integration.py

### `optuna`
Files (1):
  - src/research/hyperopt_walkforward.py

### `pandas`
Files (66):
  - main.py
  - scripts/benchmark_hotspots.py
  - scripts/generate_research_report.py
  - scripts/label_market_regimes.py
  - scripts/verify_backtest_audit.py
  - scripts/verify_benchmarking.py
  - scripts/verify_hyperopt_walkforward.py
  - scripts/verify_stress_lab.py
  - src/analytics/drift_analyzer.py
  - src/analytics/journal_mining.py
  - src/core/feature_engineering.py
  - src/environment/gym_env.py
  - src/models/regime_detector.py
  - src/research/benchmark_demo.py
  - src/research/benchmarks.py
  - src/research/hyperopt_walkforward.py
  - src/research/rare_event_simulator.py
  - src/research/rl_evaluation.py
  - src/research/rl_evaluation_demo.py
  - src/research/stress_lab.py
  - src/trading/backtester.py
  - src/trading/execution_filter.py
  - src/trading/mt5_connector.py
  - src/trading/risk_engine.py
  - src/trading/trading_env.py
  - src/utils/synthetic_data.py
  - tests/test_adaptive_feedback_loop.py
  - tests/test_backtest_auditing.py
  - tests/test_backtest_metrics_determinism.py
  - tests/test_backtest_reporting_pipeline.py
  - tests/test_backtester.py
  - tests/test_backtester_institutional.py
  - tests/test_backtester_new.py
  - tests/test_benchmarks.py
  - tests/test_benchmarks_extended.py
  - tests/test_data_pipeline_integration.py
  - tests/test_decision_pipeline_integration.py
  - tests/test_enterprise_audit_integration.py
  - tests/test_execution_analysis_pipeline.py
  - tests/test_execution_filter.py
  - tests/test_execution_quality.py
  - tests/test_execution_quality_enhanced.py
  - tests/test_execution_quality_institutional.py
  - tests/test_execution_quality_robustness.py
  - tests/test_execution_traceability.py
  - tests/test_feature_engineering.py
  - tests/test_hyperopt_walkforward.py
  - tests/test_integration_flow.py
  - tests/test_journal_mining.py
  - tests/test_journal_mining_institutional.py
  - tests/test_macro_synthetic_scenarios.py
  - tests/test_model_robustness.py
  - tests/test_model_stability_guard.py
  - tests/test_models_stubs.py
  - tests/test_performance_instrumentation.py
  - tests/test_performance_optimizations.py
  - tests/test_rare_event_simulator.py
  - tests/test_regime_detector.py
  - tests/test_reporting_integration.py
  - tests/test_risk_engine_new.py
  - tests/test_rl_evaluation.py
  - tests/test_stress_lab.py
  - tests/test_synthetic_data.py
  - tests/test_system_bootstrap_to_execution.py
  - tests/test_trading_env_optimization.py
  - tests/verify_integration.py

### `playwright`
Files (1):
  - tests/verify_reporting_frontend.py

### `prometheus_client`  (distribution: `prometheus-client`)
Files (2):
  - src/core/health.py
  - src/core/monitor.py

### `psutil`
Files (3):
  - src/core/health.py
  - src/core/monitor.py
  - tests/verify_integration.py

### `pydantic`
Files (35):
  - main.py
  - src/analytics/drift_analyzer.py
  - src/analytics/execution_quality.py
  - src/analytics/journal_mining.py
  - src/core/config.py
  - src/core/decision_support.py
  - src/core/explainability.py
  - src/core/health.py
  - src/core/schemas.py
  - src/data/event_models.py
  - src/models/calibration.py
  - src/models/regime_detector.py
  - src/research/hyperopt_walkforward.py
  - src/research/rare_event_simulator.py
  - src/research/reporting.py
  - src/research/rl_evaluation.py
  - src/research/stress_lab.py
  - src/trading/capital_allocator.py
  - tests/test_capital_allocator.py
  - tests/test_cli_ux.py
  - tests/test_config_security.py
  - tests/test_config_validator.py
  - tests/test_decision_support.py
  - tests/test_decision_support_validation.py
  - tests/test_event_model_validation.py
  - tests/test_health.py
  - tests/test_integration_flow.py
  - tests/test_jules05_stability.py
  - tests/test_schema_enforcement.py
  - tests/test_schemas.py
  - tests/test_schemas_governance.py
  - tests/test_secret_masking_hardening.py
  - tests/test_secret_masking_traceback.py
  - tests/test_security_hardening.py
  - tests/test_security_hardening_jules.py

### `pydantic_settings`  (distribution: `pydantic-settings`)
Files (1):
  - src/core/config.py

### `pytest`
Files (103):
  - tests/contracts/test_domain_contracts.py
  - tests/integration/test_data_validation.py
  - tests/temporal/test_data_leakage.py
  - tests/temporal/test_temporal_enforcement.py
  - tests/test_adaptive_feedback_loop.py
  - tests/test_adversarial_scenarios.py
  - tests/test_anomaly_scenarios.py
  - tests/test_audit_health.py
  - tests/test_audit_traceability.py
  - tests/test_backtest_metrics_determinism.py
  - tests/test_backtest_reporting_pipeline.py
  - tests/test_backtester.py
  - tests/test_backtester_institutional.py
  - tests/test_backtester_new.py
  - tests/test_benchmarks.py
  - tests/test_benchmarks_extended.py
  - tests/test_calibration.py
  - tests/test_capital_allocator.py
  - tests/test_circuit_breaker.py
  - tests/test_cli_ux.py
  - tests/test_config.py
  - tests/test_config_new.py
  - tests/test_config_validator.py
  - tests/test_ctrader_historical_data.py
  - tests/test_ctrader_spot_stream.py
  - tests/test_data_cleanup_system.py
  - tests/test_data_pipeline_integration.py
  - tests/test_database_security.py
  - tests/test_debt_cleanup.py
  - tests/test_decision_pipeline_integration.py
  - tests/test_decision_support.py
  - tests/test_decision_support_v2.py
  - tests/test_decision_support_validation.py
  - tests/test_doctor_diagnostics.py
  - tests/test_e2e_scenarios.py
  - tests/test_enhanced_synthetic_scenarios.py
  - tests/test_ensemble_scenarios.py
  - tests/test_enterprise_audit_integration.py
  - tests/test_event_intelligence.py
  - tests/test_event_intelligence_enhanced.py
  - tests/test_event_intelligence_extended.py
  - tests/test_event_intelligence_robustness.py
  - tests/test_event_intelligence_v2.py
  - tests/test_event_intelligence_v3.py
  - tests/test_event_model_validation.py
  - tests/test_execution_analysis_pipeline.py
  - tests/test_execution_filter.py
  - tests/test_execution_quality.py
  - tests/test_execution_quality_enhanced.py
  - tests/test_execution_quality_institutional.py
  - tests/test_execution_quality_robustness.py
  - tests/test_execution_scenarios.py
  - tests/test_execution_traceability.py
  - tests/test_failure_propagation.py
  - tests/test_feature_engineering.py
  - tests/test_gate4_session_validation.py
  - tests/test_health.py
  - tests/test_hyperopt_walkforward.py
  - tests/test_institutional_feedback_loop.py
  - tests/test_institutional_integration.py
  - tests/test_institutional_scenarios.py
  - tests/test_integration_flow.py
  - tests/test_journal_mining.py
  - tests/test_jules05_stability.py
  - tests/test_jules_risk_hardening.py
  - tests/test_jules_ux_enhancements.py
  - tests/test_lifecycle_scenarios.py
  - tests/test_macro_integration.py
  - tests/test_main_integration.py
  - tests/test_model_stability_guard.py
  - tests/test_models_stubs.py
  - tests/test_mt5_connector_new.py
  - tests/test_mt5_connector_resilience_v4.py
  - tests/test_mt5_resilience_recovery.py
  - tests/test_mtf_synthetic_data.py
  - tests/test_observability_funnel_v2.py
  - tests/test_performance_optimizations.py
  - tests/test_portfolio_scenarios.py
  - tests/test_rare_event_simulator.py
  - tests/test_reconciliation_scenarios.py
  - tests/test_reporting.py
  - tests/test_reporting_integration.py
  - tests/test_resilience.py
  - tests/test_resilience_v2.py
  - tests/test_risk_engine_new.py
  - tests/test_risk_manager_harmonized.py
  - tests/test_risk_scenarios.py
  - tests/test_rl_evaluation.py
  - tests/test_schema_enforcement.py
  - tests/test_schemas.py
  - tests/test_schemas_governance.py
  - tests/test_security_hardening.py
  - tests/test_security_hardening_jules.py
  - tests/test_security_mitigation.py
  - tests/test_session_alignment.py
  - tests/test_sqlite_hardening.py
  - tests/test_stress_lab.py
  - tests/test_synthetic_data.py
  - tests/test_system_bootstrap_to_execution.py
  - tests/test_trace_correlation.py
  - tests/test_trade_logger.py
  - tests/unit/test_validators.py
  - tests/verify_integration.py

### `redis`
Files (1):
  - src/core/health.py

### `rich`
Files (14):
  - main.py
  - scripts/doctor.py
  - scripts/verify_benchmarking.py
  - scripts/verify_explainability_ui.py
  - scripts/verify_stress_lab.py
  - src/core/decision_support.py
  - src/core/explainability.py
  - src/models/regime_detector.py
  - src/research/benchmark_demo.py
  - src/research/generate_audit_report.py
  - src/research/reporting.py
  - src/research/stress_test_demo.py
  - tests/test_decision_support.py
  - tests/test_palette_ux.py

### `scipy`
Files (5):
  - src/analytics/drift_analyzer.py
  - src/models/regime_detector.py
  - src/research/benchmarks.py
  - src/research/rl_evaluation.py
  - src/trading/execution_filter.py

### `sklearn`  (distribution: `scikit-learn`)
Files (1):
  - src/models/regime_detector.py

### `sqlalchemy`
Files (31):
  - scripts/benchmark_db.py
  - scripts/data_cleanup.py
  - scripts/doctor.py
  - scripts/verify_journal_mining.py
  - src/analytics/execution_quality.py
  - src/analytics/journal_mining.py
  - src/core/audit_log.py
  - src/core/config_validator.py
  - src/core/database.py
  - src/core/health.py
  - src/core/trade_logger.py
  - src/persistence/models.py
  - tests/test_adaptive_feedback_loop.py
  - tests/test_backtest_auditing.py
  - tests/test_config_security.py
  - tests/test_data_cleanup.py
  - tests/test_data_cleanup_system.py
  - tests/test_database_performance.py
  - tests/test_database_utility.py
  - tests/test_enterprise_audit_integration.py
  - tests/test_execution_analysis_pipeline.py
  - tests/test_execution_traceability.py
  - tests/test_institutional_feedback_loop.py
  - tests/test_reconciliation_scenarios.py
  - tests/test_security_hardening.py
  - tests/test_security_hardening_jules.py
  - tests/test_sqlite_hardening.py
  - tests/test_system_bootstrap_to_execution.py
  - tests/test_trace_correlation.py
  - tests/test_trade_logger.py
  - tests/verify_db.py

### `stable_baselines3`  (distribution: `stable-baselines3`)
Files (1):
  - src/models/ppo_agent.py

### `structlog`
Files (17):
  - main.py
  - scripts/label_market_regimes.py
  - src/analytics/execution_quality.py
  - src/analytics/journal_mining.py
  - src/core/audit_log.py
  - src/core/monitor.py
  - src/core/profiler.py
  - src/core/resilience.py
  - src/core/trade_logger.py
  - src/data/event_intelligence.py
  - src/models/dynamic_ensemble.py
  - src/models/regime_detector.py
  - src/trading/backtester.py
  - src/trading/capital_allocator.py
  - src/trading/mt5_connector.py
  - tests/test_institutional_feedback_loop.py
  - tests/test_trace_correlation.py

### `talib`  (distribution: `TA-Lib`)
Files (3):
  - scripts/doctor.py
  - src/core/feature_engineering.py
  - src/research/benchmarks.py

### `telegram`  (distribution: `python-telegram-bot`)
Files (1):
  - src/core/monitor.py

### `tomli`
Files (1):
  - scripts/verify_dependencies.py

### `torch`
Files (11):
  - main.py
  - scripts/doctor.py
  - src/core/health.py
  - src/models/ensemble.py
  - src/models/lstm_model.py
  - src/models/ppo_agent.py
  - src/models/transformer_model.py
  - src/research/benchmarks.py
  - tests/test_benchmarks.py
  - tests/test_institutional_integration.py
  - tests/test_integration_flow.py

### `twisted`
Files (5):
  - tools/ctrader_smoke_test/historical_data.py
  - tools/ctrader_smoke_test/smoke_test.py
  - tools/ctrader_smoke_test/spot_stream.py
  - tools/ctrader_smoke_test/symbol_discovery.py
  - tools/ctrader_smoke_test/symbol_schedule_reconciliation.py

## 3. Packages declared in `pyproject.toml`

### [project.dependencies]

- `sqlalchemy>=2.0`
- `alembic>=1.12`
- `psycopg2-binary>=2.9`
- `numpy>=1.24`
- `pandas>=2.0`
- `pyyaml>=6.0`
- `python-dotenv>=1.0`
- `httpx>=0.25`
- `structlog>=23.0`
- `pytz>=2023.3`

### [project.optional-dependencies].dev

- `pytest>=7.4`
- `pytest-cov>=4.1`
- `pytest-asyncio>=0.21`
- `hypothesis>=6.80`
- `ruff>=0.1`
- `mypy>=1.5`

## 4. Packages declared per requirements file

### requirements.txt

- `sqlalchemy>=2.0`
- `alembic>=1.12`
- `psycopg2-binary>=2.9`
- `numpy>=1.24`
- `pandas>=2.0`
- `pyyaml>=6.0`
- `python-dotenv>=1.0`
- `httpx>=0.25`
- `structlog>=23.0`
- `pytz>=2023.3`
- `pytest>=7.4`
- `pytest-cov>=4.1`
- `hypothesis>=6.80`
- `ruff>=0.1`
- `mypy>=1.5`

### requirements-test.txt

- `numpy==2.4.6`
- `scipy==1.15.3`
- `scikit-learn==1.7.2`
- `pandas==3.0.5`
- `sqlalchemy==2.0.52`
- `alembic==1.19.2`
- `redis==8.1.0`
- `pydantic==2.13.5`
- `pydantic-settings==2.15.0`
- `metaapi-cloud-sdk==29.1.1`
- `python-socketio==5.16.4`
- `optuna==4.9.0`
- `pytest==9.1.1`
- `pytest-asyncio==1.4.0`
- `pytest-cov==7.1.0`
- `pytest-mock==3.15.1`
- `python-telegram-bot==22.8`
- `fastapi==0.141.1`
- `requests==2.34.2`
- `httpx==0.28.1`
- `structlog==26.1.0`
- `rich==13.9.4`
- `gymnasium==1.3.0`
- `jinja2==3.1.6`
- `prometheus-client==0.26.0`
- `psutil==7.2.2`
- `nest-asyncio==1.6.0`
- `types-redis==4.6.0.20241004`
- `types-requests==2.33.0.20260906`
- `types-python-dateutil==2.9.0.20260807`
- `types-setuptools==84.0.0.20260812`
- `types-PyYAML==6.0.12.20260815`

### requirements-ci.txt

- `numpy==2.4.6`
- `scipy==1.15.3`
- `scikit-learn==1.7.2`
- `pandas==3.0.5`
- `TA-Lib==0.7.1`
- `sqlalchemy==2.0.52`
- `alembic==1.19.2`
- `redis==8.1.0`
- `pydantic==2.13.5`
- `pydantic-settings==2.15.0`
- `metaapi-cloud-sdk==29.1.1`
- `python-socketio==5.16.4`
- `optuna==4.9.0`
- `pytest==9.1.1`
- `pytest-asyncio==1.4.0`
- `pytest-cov==7.1.0`
- `pytest-mock==3.15.1`
- `python-telegram-bot==22.8`
- `fastapi==0.141.1`
- `requests==2.34.2`
- `httpx==0.28.1`
- `structlog==26.1.0`
- `rich==13.9.4`
- `gymnasium==1.3.0`
- `jinja2==3.1.6`
- `prometheus-client==0.26.0`
- `psutil==7.2.2`
- `nest-asyncio==1.6.0`
- `types-redis==4.6.0.20241004`
- `types-requests==2.33.0.20260906`
- `types-python-dateutil==2.9.0.20260807`
- `types-setuptools==84.0.0.20260812`
- `types-PyYAML==6.0.12.20260815`

### requirements-ci-no-talib.txt

- `numpy==2.4.6`
- `scipy==1.15.3`
- `scikit-learn==1.7.2`
- `pandas==3.0.5`
- `sqlalchemy==2.0.52`
- `alembic==1.19.2`
- `redis==8.1.0`
- `pydantic==2.13.5`
- `pydantic-settings==2.15.0`
- `metaapi-cloud-sdk==29.1.1`
- `python-socketio==5.16.4`
- `optuna==4.9.0`
- `pytest==9.1.1`
- `pytest-asyncio==1.4.0`
- `pytest-cov==7.1.0`
- `pytest-mock==3.15.1`
- `python-telegram-bot==22.8`
- `fastapi==0.141.1`
- `requests==2.34.2`
- `httpx==0.28.1`
- `structlog==26.1.0`
- `rich==13.9.4`
- `gymnasium==1.3.0`
- `jinja2==3.1.6`
- `prometheus-client==0.26.0`
- `psutil==7.2.2`
- `nest-asyncio==1.6.0`
- `types-redis==4.6.0.20241004`
- `types-requests==2.33.0.20260906`
- `types-python-dateutil==2.9.0.20260807`
- `types-setuptools==84.0.0.20260812`
- `types-PyYAML==6.0.12.20260815`

### requirements-docker.txt

- `torch==2.14.0+cpu`
- `stable-baselines3==2.9.0`
- `gymnasium==1.3.0`
- `numpy==2.4.6`
- `scipy==1.15.3`
- `scikit-learn==1.7.2`
- `pandas==3.0.5`
- `TA-Lib==0.7.1`
- `requests==2.34.2`
- `aiohttp==3.14.3`
- `httpx==0.28.1`
- `metaapi-cloud-sdk==29.1.1`
- `psycopg2-binary==2.9.12`
- `sqlalchemy==2.0.52`
- `alembic==1.19.2`
- `redis==8.1.0`
- `prometheus-client==0.26.0`
- `structlog==26.1.0`
- `rich==13.9.4`
- `tqdm==4.70.0`
- `jinja2==3.1.6`
- `fastapi==0.141.1`
- `uvicorn[standard]==0.52.4`
- `python-dotenv==1.2.3`
- `pydantic==2.13.5`
- `pydantic-settings==2.15.0`
- `tomli==2.4.1`
- `python-socketio==5.16.4`
- `python-dateutil==2.9.0.post0`
- `nest-asyncio==1.6.0`
- `pytz==2026.3.post1`
- `click==8.4.2`
- `tabulate==0.10.0`
- `joblib==1.6.0`
- `python-telegram-bot==22.8`
- `psutil==7.2.2`
- `optuna==4.9.0`

### requirements-linux.txt

- `torch==2.14.0+cpu`
- `stable-baselines3==2.9.0`
- `gymnasium==1.3.0`
- `numpy==2.4.6`
- `scipy==1.15.3`
- `scikit-learn==1.7.2`
- `pandas==3.0.5`
- `TA-Lib==0.7.1`
- `requests==2.34.2`
- `aiohttp==3.14.3`
- `httpx==0.28.1`
- `metaapi-cloud-sdk==29.1.1`
- `psycopg2-binary==2.9.12`
- `sqlalchemy==2.0.52`
- `alembic==1.19.2`
- `redis==8.1.0`
- `prometheus-client==0.26.0`
- `structlog==26.1.0`
- `rich==13.9.4`
- `tqdm==4.70.0`
- `fastapi==0.141.1`
- `uvicorn[standard]==0.52.4`
- `python-dotenv==1.2.3`
- `pydantic==2.13.5`
- `pydantic-settings==2.15.0`
- `tomli==2.4.1`
- `pytest==9.1.1`
- `pytest-asyncio==1.4.0`
- `pytest-cov==7.1.0`
- `hypothesis==6.165.10`
- `optuna==4.9.0`
- `pre-commit==4.6.2`
- `ruff==0.16.6`
- `mypy==2.3.1`
- `python-socketio==5.16.4`
- `python-dateutil==2.9.0.post0`
- `pytz==2026.3.post1`
- `click==8.4.2`
- `tabulate==0.10.0`
- `joblib==1.6.0`
- `python-telegram-bot==22.8`
- `psutil==7.2.2`

### requirements-temp.txt

- `torch==2.14.0+cpu`
- `stable-baselines3==2.9.0`
- `gymnasium==1.3.0`
- `numpy==2.4.6`
- `scipy==1.15.3`
- `scikit-learn==1.7.2`
- `pandas==3.0.5`
- `requests==2.34.2`
- `aiohttp==3.14.3`
- `httpx==0.28.1`
- `metaapi-cloud-sdk==29.1.1`
- `psycopg2-binary==2.9.12`
- `sqlalchemy==2.0.52`
- `alembic==1.19.2`
- `redis==8.1.0`
- `prometheus-client==0.26.0`
- `structlog==26.1.0`
- `rich==13.9.4`
- `tqdm==4.70.0`
- `fastapi==0.141.1`
- `uvicorn[standard]==0.52.4`
- `python-dotenv==1.2.3`
- `pydantic==2.13.5`
- `pydantic-settings==2.15.0`
- `tomli==2.4.1`
- `pytest==9.1.1`
- `pytest-asyncio==1.4.0`
- `pytest-cov==7.1.0`
- `hypothesis==6.165.10`
- `optuna==4.9.0`
- `pre-commit==4.6.2`
- `ruff==0.16.6`
- `mypy==2.3.1`
- `python-socketio==5.16.4`
- `python-dateutil==2.9.0.post0`
- `pytz==2026.3.post1`
- `click==8.4.2`
- `tabulate==0.10.0`
- `joblib==1.6.0`
- `python-telegram-bot==22.8`
- `psutil==7.2.2`

## 5. CI workflow ad-hoc installs (not declared in any requirements file)

Pinned/installed directly inside workflow steps:

- `.github/workflows/ci.yml`: `ruff==0.16.1`, `mypy==2.3.0` (quality job); `pip-audit==2.7.3`; installs `requirements-ci.txt`; builds TA-Lib C library v0.6.4 from source; Docker build.
- `.github/workflows/release.yml`: `ruff==0.16.1`, `mypy==2.3.0`, `pip-audit==2.7.3`, `pip-licenses==5.5.5`, `pytest`, `pytest-cov`; installs `requirements-ci.txt`; release job installs ad-hoc unpinned `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`, `httpx`, `tomli`.
- `.github/workflows/pre-deploy-validation.yml`: `ruff==0.16.1`, `mypy==2.3.0`, `pip-audit==2.7.3`, `pip-licenses==5.5.5`; installs `torch torchvision` from the PyTorch CPU index for the license scan (`torchvision` is declared in **no** requirements file).
- `.github/workflows/migration-safety.yml`: installs `requirements-ci.txt`; builds TA-Lib C library v0.6.4.
- OS-level (not pip): `libpq-dev`/`libpq5`, `gcc/g++/make`, `wget`, `zip`.

## 6. Used in code but NOT declared in any file read

Directly imported in the scanned scope, with no declaration in `pyproject.toml` or any `requirements*.txt`:

- **ctrader_open_api** — 5 file(s):
  - tools/ctrader_smoke_test/historical_data.py
  - tools/ctrader_smoke_test/smoke_test.py
  - tools/ctrader_smoke_test/spot_stream.py
  - tools/ctrader_smoke_test/symbol_discovery.py
  - tools/ctrader_smoke_test/symbol_schedule_reconciliation.py
- **MetaTrader5** — 3 file(s):
  - src/providers/mt5/market_data.py
  - src/trading/mt5_connector.py
  - tests/test_system_bootstrap_to_execution.py
- **playwright** — 1 file(s):
  - tests/verify_reporting_frontend.py
- **twisted** — 5 file(s):
  - tools/ctrader_smoke_test/historical_data.py
  - tools/ctrader_smoke_test/smoke_test.py
  - tools/ctrader_smoke_test/spot_stream.py
  - tools/ctrader_smoke_test/symbol_discovery.py
  - tools/ctrader_smoke_test/symbol_schedule_reconciliation.py

## 7. Declared but NOT appearing in imports (per declaration source)

Annotations are factual categories only (plugin/stub/tool/indirect); no package was reclassified by guessing.

### requirements.txt

- `hypothesis>=6.80`
- `mypy>=1.5` — tooling, no import expected
- `psycopg2-binary>=2.9` — DB driver, used indirectly via SQLAlchemy connection URLs
- `pytest-cov>=4.1` — plugin, no direct import expected
- `pytz>=2023.3`
- `pyyaml>=6.0`
- `ruff>=0.1` — tooling, no import expected

### requirements-test.txt

- `pytest-asyncio==1.4.0` — plugin, no direct import expected
- `pytest-cov==7.1.0` — plugin, no direct import expected
- `pytest-mock==3.15.1` — plugin, no direct import expected
- `python-socketio==5.16.4`
- `requests==2.34.2`
- `types-python-dateutil==2.9.0.20260807` — type stub package
- `types-PyYAML==6.0.12.20260815` — type stub package
- `types-redis==4.6.0.20241004` — type stub package
- `types-requests==2.33.0.20260906` — type stub package
- `types-setuptools==84.0.0.20260812` — type stub package

### requirements-ci.txt

- `pytest-asyncio==1.4.0` — plugin, no direct import expected
- `pytest-cov==7.1.0` — plugin, no direct import expected
- `pytest-mock==3.15.1` — plugin, no direct import expected
- `python-socketio==5.16.4`
- `requests==2.34.2`
- `types-python-dateutil==2.9.0.20260807` — type stub package
- `types-PyYAML==6.0.12.20260815` — type stub package
- `types-redis==4.6.0.20241004` — type stub package
- `types-requests==2.33.0.20260906` — type stub package
- `types-setuptools==84.0.0.20260812` — type stub package

### requirements-ci-no-talib.txt

- `pytest-asyncio==1.4.0` — plugin, no direct import expected
- `pytest-cov==7.1.0` — plugin, no direct import expected
- `pytest-mock==3.15.1` — plugin, no direct import expected
- `python-socketio==5.16.4`
- `requests==2.34.2`
- `types-python-dateutil==2.9.0.20260807` — type stub package
- `types-PyYAML==6.0.12.20260815` — type stub package
- `types-redis==4.6.0.20241004` — type stub package
- `types-requests==2.33.0.20260906` — type stub package
- `types-setuptools==84.0.0.20260812` — type stub package

### requirements-docker.txt

- `aiohttp==3.14.3`
- `click==8.4.2`
- `psycopg2-binary==2.9.12` — DB driver, used indirectly via SQLAlchemy connection URLs
- `python-dateutil==2.9.0.post0`
- `python-socketio==5.16.4`
- `pytz==2026.3.post1`
- `requests==2.34.2`
- `tabulate==0.10.0`
- `tqdm==4.70.0`
- `uvicorn[standard]==0.52.4`

### requirements-linux.txt

- `aiohttp==3.14.3`
- `click==8.4.2`
- `hypothesis==6.165.10`
- `mypy==2.3.1` — tooling, no import expected
- `pre-commit==4.6.2` — tooling, no import expected
- `psycopg2-binary==2.9.12` — DB driver, used indirectly via SQLAlchemy connection URLs
- `pytest-asyncio==1.4.0` — plugin, no direct import expected
- `pytest-cov==7.1.0` — plugin, no direct import expected
- `python-dateutil==2.9.0.post0`
- `python-socketio==5.16.4`
- `pytz==2026.3.post1`
- `requests==2.34.2`
- `ruff==0.16.6` — tooling, no import expected
- `tabulate==0.10.0`
- `tqdm==4.70.0`
- `uvicorn[standard]==0.52.4`

### requirements-temp.txt

- `aiohttp==3.14.3`
- `click==8.4.2`
- `hypothesis==6.165.10`
- `mypy==2.3.1` — tooling, no import expected
- `pre-commit==4.6.2` — tooling, no import expected
- `psycopg2-binary==2.9.12` — DB driver, used indirectly via SQLAlchemy connection URLs
- `pytest-asyncio==1.4.0` — plugin, no direct import expected
- `pytest-cov==7.1.0` — plugin, no direct import expected
- `python-dateutil==2.9.0.post0`
- `python-socketio==5.16.4`
- `pytz==2026.3.post1`
- `requests==2.34.2`
- `ruff==0.16.6` — tooling, no import expected
- `tabulate==0.10.0`
- `tqdm==4.70.0`
- `uvicorn[standard]==0.52.4`

### pyproject.toml [project.dependencies]

- `psycopg2-binary>=2.9` — DB driver, used indirectly via SQLAlchemy connection URLs
- `pytz>=2023.3`
- `pyyaml>=6.0`

### pyproject.toml [project.optional-dependencies].dev

- `hypothesis>=6.80`
- `mypy>=1.5` — tooling, no import expected
- `pytest-asyncio>=0.21` — plugin, no direct import expected
- `pytest-cov>=4.1` — plugin, no direct import expected
- `ruff>=0.1` — tooling, no import expected

## 8. Obvious version conflicts / declaration divergences (only clear-cut items)

### 8.1 Differing exact pins across requirements files (computed)

- None. All exact pins shared between requirements files are identical.

### 8.2 Obvious drift and stale references (observed directly in files read)

- **ruff / mypy drift:** CI workflows pin `ruff==0.16.1` / `mypy==2.3.0`; `requirements-linux.txt` and `requirements-temp.txt` pin `ruff==0.16.6` / `mypy==2.3.1`; `pyproject.toml` declares `ruff>=0.1`, `mypy>=1.5`.
- **Dockerfile stale pins:** `Dockerfile` (AMD64 branch) runs `sed` against `torch==2.3.1` / `torchvision==0.18.1`, but `requirements-docker.txt` pins `torch==2.14.0+cpu` and `torchvision` is declared nowhere → the sed is a no-op; `torchvision` is installed ad-hoc only in `pre-deploy-validation.yml`.
- **TA-Lib C library vs Python binding:** Dockerfile/CI build TA-Lib C library v0.6.4 while the Python binding is pinned `TA-Lib==0.7.1` (version families differ; recorded as-is, not interpreted).
- **Python version:** `pyproject.toml` sets `requires-python = ">=3.11"`; `requirements-linux.txt`/`requirements-temp.txt` headers state "Compatible: Python 3.10+".
- **Two pinning regimes:** `requirements.txt` (and `pyproject.toml`) use open ranges (e.g. `httpx>=0.25`), while `requirements-ci/-docker/-linux/-temp` pin exact versions (e.g. `httpx==0.28.1`). No unsatisfiable range-vs-pin pair was flagged; listed as a regime divergence only.
- **`requirements-ci.txt` gaps:** `psycopg2-binary`, `pyyaml`, `python-dotenv`, `pytz` are declared in `pyproject.toml`/`requirements.txt` but absent from `requirements-ci.txt` (which CI uses). `python-dotenv` is imported by `scripts/doctor.py` and 5 `tools/ctrader_smoke_test/` files; `pydantic-settings` (declared in CI) depends on `python-dotenv` transitively (dependency metadata, not code evidence).
- **TA-Lib optional variants:** `requirements-test.txt`, `requirements-ci-no-talib.txt`, `requirements-temp.txt` intentionally omit `TA-Lib` (empty section headers retained); `talib` is imported by `scripts/doctor.py`, `src/core/feature_engineering.py`, `src/research/benchmarks.py`.

## 9. Needs mapping

Import names that could not be matched to a declaration in this repo (mapping to a distribution name was not inferred):

- `MetaTrader5` — used, undeclared (see section 6).
- `ctrader_open_api` — used, undeclared (see section 6).
- `playwright` — used, undeclared (see section 6).
- `twisted` — used, undeclared (see section 6).

Note: every other imported third-party name was matched to a declared distribution by direct name correspondence (identity or the explicit table in §2). No package was excluded or guessed.

## 10. Domain sections

### 10.1 cTrader dependencies

- `ctrader_open_api` — imported in 5 files, all under `tools/ctrader_smoke_test/`: `historical_data.py`, `smoke_test.py`, `spot_stream.py`, `symbol_discovery.py`, `symbol_schedule_reconciliation.py`. **Not declared anywhere.**
- `twisted` — imported by the same 5 `tools/ctrader_smoke_test/` files. **Not declared anywhere.**
- `dotenv` (`python-dotenv`) — imported by the same 5 files; declared in `pyproject.toml`, `requirements.txt`, `-docker`, `-linux`, `-temp`; **absent from `requirements-ci.txt`**.
- No cTrader-related package appears in any requirements file; `tools/ctrader_smoke_test/` is not covered by any declaration source read.

### 10.2 MT5 / MetaAPI legacy dependencies

- `MetaTrader5` — imported in `src/providers/mt5/market_data.py`, `src/trading/mt5_connector.py`, `tests/test_system_bootstrap_to_execution.py`. **Not declared anywhere** (release/pre-deploy license scans explicitly exclude it from installs).
- `metaapi_cloud_sdk` (`metaapi-cloud-sdk==29.1.1`) — imported in `src/trading/mt5_connector.py`; declared in `-ci`, `-test`, `-ci-no-talib`, `-docker`, `-linux`, `-temp`.
- `nest_asyncio` (`nest-asyncio`) — imported in `src/trading/mt5_connector.py`; declared in `-ci`, `-test`, `-ci-no-talib`, `-docker`, `-linux`, `-temp`.

### 10.3 Research / ML dependencies

- `torch` (`torch`) — 11 file(s): `main.py`, `scripts/doctor.py`, `src/core/health.py`, `src/models/ensemble.py`, `src/models/lstm_model.py`, `src/models/ppo_agent.py`, `src/models/transformer_model.py`, `src/research/benchmarks.py`, `tests/test_benchmarks.py`, `tests/test_institutional_integration.py`, `tests/test_integration_flow.py`
- `stable_baselines3` (`stable-baselines3`) — 1 file(s): `src/models/ppo_agent.py`
- `gymnasium` (`gymnasium`) — 2 file(s): `src/environment/gym_env.py`, `src/trading/trading_env.py`
- `sklearn` (`scikit-learn`) — 1 file(s): `src/models/regime_detector.py`
- `scipy` (`scipy`) — 5 file(s): `src/analytics/drift_analyzer.py`, `src/models/regime_detector.py`, `src/research/benchmarks.py`, `src/research/rl_evaluation.py`, `src/trading/execution_filter.py`
- `optuna` (`optuna`) — 1 file(s): `src/research/hyperopt_walkforward.py`
- `joblib` (`joblib`) — 2 file(s): `src/models/regime_detector.py`, `tests/test_security_mitigation.py`
- `jinja2` (`jinja2`) — 1 file(s): `src/research/reporting.py`
- `rich` (`rich`) — 14 file(s): `main.py`, `scripts/doctor.py`, `scripts/verify_benchmarking.py`, `scripts/verify_explainability_ui.py`, `scripts/verify_stress_lab.py`, `src/core/decision_support.py`, `src/core/explainability.py`, `src/models/regime_detector.py`, `src/research/benchmark_demo.py`, `src/research/generate_audit_report.py`, `src/research/reporting.py`, `src/research/stress_test_demo.py`, `tests/test_decision_support.py`, `tests/test_palette_ux.py`
- `talib` (`TA-Lib`) — 3 file(s): `scripts/doctor.py`, `src/core/feature_engineering.py`, `src/research/benchmarks.py`
- Core numeric stack `numpy` / `pandas` (66 files each) and `pydantic` (35 files) span the whole codebase — full per-file lists in §2.

### 10.4 Test / lint / type-check dependencies

- `pytest` — imported in 103 test files (full list in §2). Declared in `pyproject.toml` dev, `requirements.txt`, `-ci`, `-test`, `-ci-no-talib`, `-linux`, `-temp`.
- `pytest-cov`, `pytest-asyncio`, `pytest-mock` — declared (pyproject dev / `-ci` / `-linux` / `-temp` as applicable); no direct imports (plugins).
- `hypothesis` — declared in `pyproject.toml` dev, `requirements.txt`, `-linux`, `-temp`; **no direct import found** in the scanned scope.
- `playwright` — imported in `tests/verify_reporting_frontend.py`. **Not declared anywhere.**
- `ruff`, `mypy` — declared in `pyproject.toml` dev, `-linux`, `-temp`; installed ad-hoc in CI at different pins (see §8.2).
- `pip-audit==2.7.3`, `pip-licenses==5.5.5` — CI-only ad-hoc installs; not declared in any requirements file.
- `types-redis`, `types-requests`, `types-python-dateutil`, `types-setuptools`, `types-PyYAML` — stub packages declared in `-ci`, `-test`, `-ci-no-talib`; no imports expected.
- `pre-commit==4.6.2` — declared in `-linux`, `-temp`; tooling, no import expected.

---

_End of raw inventory. Scan: 295 files, 0 parse errors. Read-only phase; no further action taken._
