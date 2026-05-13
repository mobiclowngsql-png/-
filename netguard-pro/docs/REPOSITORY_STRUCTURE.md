# NetGuard Pro — Структура репозитория

## Production-Ready Repository Structure

```
netguard-pro/
├── .github/                          # GitHub Actions workflows
│   ├── workflows/
│   │   ├── ci.yml                    # Continuous Integration
│   │   ├── cd.yml                    # Continuous Deployment
│   │   ├── security-scan.yml         # Security scanning
│   │   └── release.yml               # Release automation
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
│
├── .gitlab-ci.yml                    # GitLab CI configuration (alternative)
├── .dockerignore                     # Docker ignore rules
├── .editorconfig                     # Editor configuration
├── .pre-commit-config.yaml           # Pre-commit hooks
├── .pylintrc                         # Python linting configuration
├── .flake8                           # Flake8 configuration
├── .mypy.ini                         # MyPy type checking
├── .black.toml                       # Black formatter config
├── .isort.cfg                        # Import sorting
│
├── backend/                          # Backend application (Python/FastAPI)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # Application entry point
│   │   ├── config.py                 # Configuration management
│   │   ├── logging_config.py         # Logging setup
│   │   │
│   │   ├── api/                      # API layer
│   │   │   ├── __init__.py
│   │   │   ├── deps.py               # Dependencies (DI)
│   │   │   ├── router.py             # Main router
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py           # Authentication endpoints
│   │   │       ├── users.py          # User management
│   │   │       ├── groups.py         # Group management
│   │   │       ├── policies.py       # Access policies
│   │   │       ├── firewall.py       # Firewall rules
│   │   │       ├── nat.py            # NAT configuration
│   │   │       ├── proxy.py          # Proxy settings
│   │   │       ├── qos.py            # QoS policies
│   │   │       ├── billing.py        # Billing operations
│   │   │       ├── tariffs.py        # Tariff plans
│   │   │       ├── reports.py        # Reporting endpoints
│   │   │       ├── monitoring.py     # Real-time monitoring
│   │   │       └── integrations/
│   │   │           ├── __init__.py
│   │   │           ├── active_directory.py
│   │   │           ├── radius.py
│   │   │           ├── esia.py       # Госуслуги OAuth2
│   │   │           └── smtp.py
│   │   │
│   │   ├── core/                     # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── security.py           # Security utilities (JWT, password hashing)
│   │   │   ├── rbac.py               # Role-Based Access Control
│   │   │   ├── audit.py              # Audit logging
│   │   │   ├── events.py             # Event bus (Redis Pub/Sub)
│   │   │   └── exceptions.py         # Custom exceptions
│   │   │
│   │   ├── db/                       # Database layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # SQLAlchemy base
│   │   │   ├── session.py            # Database sessions
│   │   │   ├── engine.py             # Database engine setup
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       ├── user_repo.py
│   │   │       ├── policy_repo.py
│   │   │       ├── billing_repo.py
│   │   │       ├── traffic_repo.py
│   │   │       └── audit_repo.py
│   │   │
│   │   ├── migrations/               # Database migrations (Alembic)
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   │
│   │   ├── models/                   # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── group.py
│   │   │   ├── policy.py
│   │   │   ├── firewall_rule.py
│   │   │   ├── nat_rule.py
│   │   │   ├── tariff.py
│   │   │   ├── account.py
│   │   │   ├── traffic_log.py
│   │   │   ├── audit_log.py
│   │   │   └── integration.py
│   │   │
│   │   ├── schemas/                  # Pydantic schemas (validation)
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── policy.py
│   │   │   ├── firewall.py
│   │   │   ├── billing.py
│   │   │   └── common.py
│   │   │
│   │   ├── services/                 # Business services
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── policy_service.py
│   │   │   ├── billing_service.py
│   │   │   ├── tariff_service.py
│   │   │   ├── reporting_service.py
│   │   │   └── notification_service.py
│   │   │
│   │   ├── controllers/              # Network controllers
│   │   │   ├── __init__.py
│   │   │   ├── firewall_controller.py
│   │   │   ├── nat_controller.py
│   │   │   ├── proxy_controller.py
│   │   │   ├── qos_controller.py
│   │   │   ├── routing_controller.py
│   │   │   └── ssl_inspect_controller.py
│   │   │
│   │   ├── platform/                 # Platform abstraction layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Abstract base classes
│   │   │   ├── linux/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── nftables.py
│   │   │   │   ├── tc.py
│   │   │   │   └── utils.py
│   │   │   └── windows/
│   │   │       ├── __init__.py
│   │   │       ├── wfp.py
│   │   │       ├── netsh.py
│   │   │       └── utils.py
│   │   │
│   │   ├── integrations/             # External integrations
│   │   │   ├── __init__.py
│   │   │   ├── active_directory.py
│   │   │   ├── ldap_client.py
│   │   │   ├── kerberos_auth.py
│   │   │   ├── radius_client.py
│   │   │   ├── esia_oauth.py
│   │   │   ├── icap_client.py        # Antivirus (Kaspersky, Panda)
│   │   │   ├── suricata_client.py
│   │   │   └── smtp_gateway.py
│   │   │
│   │   ├── tasks/                    # Background tasks (Celery)
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   ├── billing_tasks.py
│   │   │   ├── reporting_tasks.py
│   │   │   ├── cleanup_tasks.py
│   │   │   └── sync_tasks.py
│   │   │
│   │   └── middleware/               # ASGI middleware
│   │       ├── __init__.py
│   │       ├── authentication.py
│   │       ├── rate_limiter.py
│   │       ├── audit_logger.py
│   │       └── cors.py
│   │
│   ├── tests/                        # Backend tests
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest fixtures
│   │   ├── unit/
│   │   │   ├── test_auth.py
│   │   │   ├── test_users.py
│   │   │   ├── test_policies.py
│   │   │   └── test_billing.py
│   │   ├── integration/
│   │   │   ├── test_api_auth.py
│   │   │   ├── test_api_users.py
│   │   │   └── test_database.py
│   │   └── e2e/
│   │       ├── test_full_workflow.py
│   │       └── test_performance.py
│   │
│   ├── alembic.ini                   # Alembic configuration
│   ├── pyproject.toml                # Project metadata & dependencies
│   ├── requirements.txt              # Dependencies (pip)
│   ├── requirements-dev.txt          # Development dependencies
│   └── Dockerfile                    # Backend Docker image
│
├── core/                             # High-performance network core (Rust/C++)
│   ├── src/
│   │   ├── lib.rs
│   │   ├── firewall/
│   │   │   ├── mod.rs
│   │   │   ├── engine.rs
│   │   │   └── rule_evaluator.rs
│   │   ├── nat/
│   │   │   ├── mod.rs
│   │   │   └── translator.rs
│   │   ├── proxy/
│   │   │   ├── mod.rs
│   │   │   ├── http_proxy.rs
│   │   │   └── socks_proxy.rs
│   │   ├── ssl_inspect/
│   │   │   ├── mod.rs
│   │   │   ├── mitm_engine.rs
│   │   │   └── cert_manager.rs
│   │   ├── qos/
│   │   │   ├── mod.rs
│   │   │   └── shaper.rs
│   │   └── accounting/
│   │       ├── mod.rs
│   │       └── traffic_collector.rs
│   │
│   ├── Cargo.toml                    # Rust dependencies
│   ├── build.rs                      # Build script
│   └── bindings/                     # Python bindings (PyO3)
│       └── python_module.rs
│
├── frontend/                         # Web UI (React + TypeScript)
│   ├── public/
│   │   ├── index.html
│   │   └── manifest.json
│   │
│   ├── src/
│   │   ├── index.tsx
│   │   ├── App.tsx
│   │   ├── reportWebVitals.ts
│   │   │
│   │   ├── components/               # Reusable components
│   │   │   ├── common/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Table.tsx
│   │   │   │   └── Form.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── StatsCard.tsx
│   │   │   │   ├── TrafficChart.tsx
│   │   │   │   └── ActivityFeed.tsx
│   │   │   ├── users/
│   │   │   │   ├── UserList.tsx
│   │   │   │   ├── UserForm.tsx
│   │   │   │   └── UserDetail.tsx
│   │   │   ├── policies/
│   │   │   │   ├── PolicyList.tsx
│   │   │   │   ├── PolicyEditor.tsx
│   │   │   │   └── RuleBuilder.tsx
│   │   │   ├── firewall/
│   │   │   │   ├── FirewallRules.tsx
│   │   │   │   └── RuleEditor.tsx
│   │   │   ├── billing/
│   │   │   │   ├── TariffList.tsx
│   │   │   │   ├── TariffEditor.tsx
│   │   │   │   └── BalanceWidget.tsx
│   │   │   └── reports/
│   │   │       ├── ReportGenerator.tsx
│   │   │       └── ChartViewer.tsx
│   │   │
│   │   ├── pages/                    # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Users.tsx
│   │   │   ├── Groups.tsx
│   │   │   ├── Policies.tsx
│   │   │   ├── Firewall.tsx
│   │   │   ├── NAT.tsx
│   │   │   ├── Proxy.tsx
│   │   │   ├── QoS.tsx
│   │   │   ├── Billing.tsx
│   │   │   ├── Tariffs.tsx
│   │   │   ├── Reports.tsx
│   │   │   ├── Monitoring.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── SelfService.tsx
│   │   │
│   │   ├── services/                 # API clients
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   ├── users.ts
│   │   │   ├── policies.ts
│   │   │   ├── billing.ts
│   │   │   └── monitoring.ts
│   │   │
│   │   ├── store/                    # Redux state management
│   │   │   ├── store.ts
│   │   │   ├── hooks.ts
│   │   │   └── slices/
│   │   │       ├── authSlice.ts
│   │   │       ├── userSlice.ts
│   │   │       ├── policySlice.ts
│   │   │       └── monitoringSlice.ts
│   │   │
│   │   ├── types/                    # TypeScript types
│   │   │   ├── index.ts
│   │   │   ├── user.ts
│   │   │   ├── policy.ts
│   │   │   ├── billing.ts
│   │   │   └── api.ts
│   │   │
│   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useUsers.ts
│   │   │   └── useMonitoring.ts
│   │   │
│   │   ├── utils/                    # Utilities
│   │   │   ├── formatters.ts
│   │   │   ├── validators.ts
│   │   │   └── constants.ts
│   │   │
│   │   └── styles/                   # Global styles
│   │       ├── index.css
│   │       └── theme.ts
│   │
│   ├── tests/                        # Frontend tests
│   │   ├── components/
│   │   └── pages/
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── jest.config.js
│   └── Dockerfile
│
├── shared/                           # Shared code between services
│   ├── proto/                        # Protocol Buffers definitions
│   │   ├── user.proto
│   │   ├── policy.proto
│   │   ├── billing.proto
│   │   └── events.proto
│   │
│   └── python_lib/                   # Shared Python library
│       ├── __init__.py
│       ├── models.py
│       └── utils.py
│
├── docker/                           # Docker configurations
│   ├── docker-compose.yml            # Local development
│   ├── docker-compose.prod.yml       # Production deployment
│   ├── docker-compose.cluster.yml    # Cluster deployment
│   │
│   ├── backend/
│   │   └── Dockerfile
│   ├── frontend/
│   │   └── Dockerfile
│   ├── postgres/
│   │   └── Dockerfile
│   ├── redis/
│   │   └── Dockerfile
│   └── nginx/
│       └── Dockerfile
│
├── deploy/                           # Deployment configurations
│   ├── kubernetes/
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── secrets.yaml
│   │   ├── postgres-statefulset.yaml
│   │   ├── redis-deployment.yaml
│   │   ├── backend-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── ingress.yaml
│   │   └── hpa.yaml
│   │
│   ├── helm/
│   │   └── netguard-pro/
│   │       ├── Chart.yaml
│   │       ├── values.yaml
│   │       └── templates/
│   │
│   └── ansible/
│       ├── inventory/
│       ├── playbooks/
│       │   ├── install.yml
│       │   ├── configure.yml
│       │   └── update.yml
│       └── roles/
│           ├── common/
│           ├── backend/
│           ├── frontend/
│           └── database/
│
├── docs/                             # Documentation
│   ├── ARCHITECTURE.md               # Architecture documentation
│   ├── API.md                        # API documentation
│   ├── DEPLOYMENT.md                 # Deployment guide
│   ├── DEVELOPMENT.md                # Development guide
│   ├── SECURITY.md                   # Security documentation
│   ├── USER_GUIDE.md                 # User manual
│   └── diagrams/                     # Architecture diagrams
│       ├── system_architecture.png
│       ├── data_flow.png
│       └── deployment.png
│
├── scripts/                          # Utility scripts
│   ├── setup_dev.sh                  # Development environment setup
│   ├── run_tests.sh                  # Test runner
│   ├── build.sh                      # Build script
│   ├── deploy.sh                     # Deployment script
│   ├── backup.sh                     # Backup script
│   └── migrate_db.sh                 # Database migration
│
├── tests/                            # End-to-end tests
│   ├── conftest.py
│   ├── test_integration.py
│   └── test_performance.py
│
├── LICENSE                           # License file
├── README.md                         # Project overview
├── CHANGELOG.md                      # Version history
└── CONTRIBUTING.md                   # Contribution guidelines
```

## Ключевые принципы организации

### 1. Модульность
- Чёткое разделение ответственности между модулями
- Каждый модуль имеет единую зону ответственности
- Минимизация耦合 (coupling) между модулями

### 2. Масштабируемость
- Горизонтальная структура для лёгкого добавления новых модулей
- Поддержка микросервисной архитектуры в будущем
- Независимое масштабирование компонентов

### 3. Тестируемость
- Отдельные директории для unit, integration и e2e тестов
- Фикстуры и моки в `conftest.py`
- Покрытие тестами > 80%

### 4. Безопасность
- Конфигурации безопасности в отдельных файлах
- Secrets management через environment variables
- Audit logging всех критических операций

### 5. DevOps-friendly
- Dockerfile для каждого компонента
- Helm charts для Kubernetes deployment
- Ansible playbooks для автоматизации
- CI/CD pipelines в `.github/workflows`

### 6. Документированность
- Полная документация архитектуры
- API documentation (OpenAPI/Swagger)
- Руководства по развёртыванию и разработке
- Диаграммы и визуализации
