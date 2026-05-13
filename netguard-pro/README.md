# NetGuard Pro

**Universal Internet Gateway, Proxy Server, Firewall and Billing System**

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

## Описание

NetGuard Pro — это комплексное серверное решение для контроля и управления доступом 
к интернет в корпоративных и образовательных сетях. Платформа объединяет в себе 
функционал межсетевого экрана нового поколения (NGFW), прокси-сервера, системы 
биллинга и мониторинга сетевого трафика.

## Ключевые возможности

### 🔒 Безопасность
- **Next-Generation Firewall** с гибкой системой правил
- **SSL/TLS Inspection** для расшифровки HTTPS трафика
- **IDS/IPS** интеграция (Suricata) для обнаружения атак
- **RBAC** система разграничения доступа
- **MFA** многофакторная аутентификация
- **Audit Logging** полное логирование всех событий

### 🌐 Сетевой функционал
- **Прокси-сервер** HTTP/HTTPS/SOCKS5
- **NAT** SNAT/DNAT, Port Forwarding, DMZ
- **QoS** шейпинг трафика и приоритизация
- **Policy-Based Routing** маршрутизация по политикам
- **Load Balancing** балансировка нагрузки
- **Failover** автоматическое переключение

### 👥 Управление пользователями
- **Интеграция с AD** LDAP, Kerberos, SSO
- **RADIUS** аутентификация
- **ЕСИА** вход через Госуслуги
- **Групповые политики** применение настроек по группам
- **Self-service портал** личный кабинет пользователя

### 💰 Биллинг
- **Тарифные планы** гибкая система тарификации
- **Учёт трафика** поминутный и побатовый
- **Балансы** предоплата и постоплата
- **Автопополнение** интеграция с платёжными системами
- **Отчёты** детализация расходов

### 📊 Мониторинг и отчёты
- **Real-time dashboard** мониторинг в реальном времени
- **Графики и статистика** визуализация данных
- **Экспорт отчётов** PDF, CSV, XLSX
- **SIEM интеграция** экспорт логов в CEF/Syslog
- **Алерты** уведомления о событиях

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Interface                           │
│                  (React + TypeScript)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS
┌───────────────────────────▼─────────────────────────────────┐
│                    API Gateway                               │
│                   (FastAPI + JWT)                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                   Core Services                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │  Auth   │ │ Policy  │ │ Billing │ │ Monitor │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                Network Controllers                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │Firewall │ │  Proxy  │ │   QoS   │ │   NAT   │          │
│  │(nftables│ │ (Squid) │ │  (tc)   │ │(iptables│          │
│  │  /WFP)  │ │         │ │         │ │  /WFP)  │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                  Data Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ PostgreSQL  │  │ TimescaleDB │  │    Redis    │        │
│  │  (Primary)  │  │ (Time-series│  │  (Cache)    │        │
│  │             │  │   +Analytics)│  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Технологический стек

| Компонент | Технология |
|-----------|------------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy, Pydantic |
| **Frontend** | React 18, TypeScript, Redux Toolkit, MUI |
| **Database** | PostgreSQL 15, TimescaleDB |
| **Cache** | Redis 7 |
| **Network** | nftables, Squid, Suricata, tc/HTB |
| **Deployment** | Docker, Kubernetes, Helm |
| **CI/CD** | GitHub Actions, GitLab CI |
| **Monitoring** | Prometheus, Grafana, Loki |

## Быстрый старт

### Требования
- Docker 24+ и Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Запуск через Docker Compose

```bash
# Клонировать репозиторий
git clone https://github.com/netguard/netguard-pro.git
cd netguard-pro

# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps

# Посмотреть логи
docker-compose logs -f backend
```

### Локальная разработка

```bash
# Установить зависимости
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt

# Настроить переменные окружения
cp .env.example .env
# Отредактировать .env

# Запустить миграции
alembic upgrade head

# Запустить сервер разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Документация

- [Архитектура системы](docs/ARCHITECTURE.md)
- [Структура репозитория](docs/REPOSITORY_STRUCTURE.md)
- [Стратегия масштабирования](docs/SCALING_STRATEGY.md)
- [План разработки](docs/DEVELOPMENT_PLAN.md)
- [DevOps Pipeline](docs/DEVOPS_PIPELINE.md)
- [API Documentation](http://localhost:8000/docs)

## Конфигурация

### Переменные окружения

```bash
# Application
APP_NAME=NetGuard Pro
ENVIRONMENT=development
SECRET_KEY=your-secret-key-min-32-chars

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=netguard
DB_USER=netguard
DB_PASSWORD=secure-password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_WORKERS=4
```

## Тестирование

```bash
# Запустить unit тесты
pytest backend/tests/unit -v

# Запустить integration тесты
pytest backend/tests/integration -v

# Запустить e2e тесты
pytest backend/tests/e2e -v

# Проверка покрытия
pytest --cov=backend/app --cov-report=html
```

## Безопасность

### Соответствие требованиям
- ✅ ФЗ-152 "О персональных данных"
- ✅ ГОСТ Р 57580 (требования к СЗИ)
- ✅ CIS Benchmarks для ОС и приложений
- ✅ OWASP Top 10 защита

### Security Features
- TLS 1.3 для всех соединений
- AES-256 шифрование данных
- bcrypt/argon2 для паролей
- Rate limiting и защита от brute-force
- Audit logging всех операций
- Регулярные security scanning

## Производительность

| Метрика | Значение |
|---------|----------|
| API Latency (p95) | < 50ms |
| API Throughput | 10,000+ RPS |
| Concurrent Users | 10,000+ |
| Traffic Processing | 10 Gbps+ |
| Rule Evaluation | < 1ms |

## Лицензия

Proprietary software. Все права защищены.

## Контакты

- Website: https://netguard.pro
- Email: dev@netguard.pro
- Support: support@netguard.pro

## Changelog

См. [CHANGELOG.md](CHANGELOG.md)

## Contributing

Этот проект является проприетарным. Вклад внешних разработчиков возможен только 
по приглашению команды разработки.

---

© 2024 NetGuard Team. All rights reserved.
