# NetGuard Pro — Архитектура системы

## 1. Общая архитектурная диаграмма

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Web Browser  │  │ Mobile App   │  │ API Clients  │  │ SIEM/SOAR    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼─────────────────┼─────────────────┼─────────────────┼────────────┘
          │                 │                 │                 │
          │    HTTPS        │    HTTPS        │    REST API     │   Syslog/CEF
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LOAD BALANCER / HAProxy                              │
│                    (TLS Termination, SSL Offloading)                        │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (FastAPI)                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Authentication Middleware (JWT, OAuth2, Kerberos, LDAP, ЕСИА)       │  │
│  │  Rate Limiting • Request Validation • Audit Logging                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CORE SERVICES LAYER                                    │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   User      │  │   Policy    │  │   Billing   │  │  Reporting  │       │
│  │   Service   │  │   Service   │  │   Service   │  │   Service   │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         │                │                │                │               │
│  ┌──────▼────────────────▼────────────────▼────────────────▼──────┐       │
│  │                    EVENT BUS (Redis Pub/Sub)                   │       │
│  └──────┬────────────────┬────────────────┬────────────────┬──────┘       │
│         │                │                │                │               │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐      │
│  │  Firewall   │  │   Proxy     │  │    QoS      │  │   Monitor   │      │
│  │  Controller │  │  Controller │  │  Controller │  │   Service   │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────┘      │
└─────────┼─────────────────┼─────────────────┼─────────────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NETWORK CONTROL PLANE                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              Platform Abstraction Layer (PAL)                       │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │   │
│  │  │   Linux (AL)     │  │   Windows        │  │   Common         │  │   │
│  │  │   nftables       │  │   WFP            │  │   Interfaces     │  │   │
│  │  │   iptables-nat   │  │   NAT Engine     │  │   (Abstract)     │  │   │
│  │  │   tc/HTB         │  │   QoS Windows    │  │                  │  │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DATA PERSISTENCE LAYER                                  │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ PostgreSQL   │  │ TimescaleDB  │  │    Redis     │  │   MinIO/S3   │   │
│  │ (Primary DB) │  │ (Time Series)│  │   (Cache)    │  │  (Logs/Certs)│   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   EXTERNAL INTEGRATIONS                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ Active Dir  │  │   RADIUS    │  │    ЕСИА     │  │ Antivirus   │       │
│  │ (LDAP/Kerb) │  │   Server    │  │  (OAuth2)   │  │ (ICAP/KAV)  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Suricata  │  │  SMTP GW    │  │    SIEM     │  │  Webhooks   │       │
│  │  (IDS/IPS)  │  │  (Postfix)  │  │ (Syslog)    │  │             │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Потоки данных

### 2.1. Поток аутентификации пользователя
```
User → Web UI → API Gateway → Auth Service → [AD/LDAP/DB/ЕСИА] 
       → JWT Token → Redis Session → Response
```

### 2.2. Поток сетевого трафика
```
Client → Network Interface → Firewall (nftables/WFP) 
       → Proxy (Transparent/Explicit) → SSL Inspection 
       → Content Filter → IDS/IPS → Internet
       
       ↓ Parallel
       
       Accounting → Billing Service → PostgreSQL/TimescaleDB
       Logs → Monitoring Service → Redis → Frontend (WebSocket)
```

### 2.3. Поток применения политик
```
Admin → Web UI → Policy API → Validation → Event Bus 
      → Firewall Controller → PAL → nftables/WFP
      → Proxy Controller → Squid/Custom Proxy Config
      → QoS Controller → tc/Windows QoS
```

### 2.4. Поток биллинга
```
Traffic Data → Accounting Module → Rating Engine 
            → Tariff Calculation → Balance Update 
            → Notification (if low balance) 
            → Enforcement (block/throttle if needed)
```

## 3. Модульная структура компонентов

### 3.1. Core Services
| Модуль | Описание | Технология |
|--------|----------|------------|
| **Auth Service** | Аутентификация, авторизация, сессии, MFA | FastAPI, JWT, bcrypt |
| **User Service** | Управление пользователями, группами, профилями | FastAPI, SQLAlchemy |
| **Policy Service** | Политики доступа, правила firewall, расписания | FastAPI, Rule Engine |
| **Billing Service** | Тарифы, баланс, лимиты, начисления | FastAPI, Decimal precision |
| **Reporting Service** | Отчёты, статистика, экспорт | FastAPI, Pandas, Asyncpg |
| **Monitoring Service** | Реал-тайм мониторинг, алерты | FastAPI, WebSocket, Redis |

### 3.2. Network Controllers
| Контроллер | Описание | Платформа |
|------------|----------|-----------|
| **Firewall Controller** | Управление правилами NGFW | nftables (Linux), WFP (Windows) |
| **NAT Controller** | SNAT/DNAT, Port Forwarding, DMZ | iptables-nat, Windows NAT |
| **Proxy Controller** | HTTP/HTTPS/SOCKS proxy, кэширование | Squid + Custom MITM |
| **SSL Inspection Controller** | Перехват HTTPS, управление CA | OpenSSL, mitmproxy core |
| **QoS Controller** | Шейпинг, приоритизация | tc/HTB, Windows QoS |
| **Routing Controller** | PBR, failover, load balancing | iproute2, Windows Routing |

### 3.3. Integrations
| Интеграция | Протокол | Назначение |
|------------|----------|------------|
| **Active Directory** | LDAP/LDAPS, Kerberos, GSSAPI | Импорт пользователей, SSO |
| **RADIUS** | RADIUS/FreeRADIUS | Аутентификация NAS/VPN |
| **ЕСИА** | OAuth2.0 | Вход через Госуслуги |
| **Antivirus** | ICAP (Kaspersky, Panda) | Проверка трафика |
| **Suricata** | AF_PACKET, Unix Socket | IDS/IPS |
| **SMTP Gateway** | SMTP/LMTP | Почтовый шлюз |
| **SIEM** | Syslog, CEF, LEEF | Экспорт логов |

## 4. Технологический стек

### Backend
- **Язык:** Python 3.11+ (async-first)
- **Framework:** FastAPI 0.109+
- **ORM:** SQLAlchemy 2.0 (AsyncSession)
- **Migration:** Alembic
- **Validation:** Pydantic v2
- **Task Queue:** Celery + Redis/RabbitMQ
- **Caching:** Redis 7+
- **Database:** PostgreSQL 15+ с расширением TimescaleDB

### Network Core
- **Firewall:** nftables (Astra Linux), Windows Filtering Platform
- **Proxy:** Squid 5.x + модифицированный mitmproxy для SSL Inspection
- **IDS/IPS:** Suricata 7.x с правилами ET/Open
- **QoS:** tc с HTB/FQ_Codel (Linux), Windows QoS APIs
- **SSL/TLS:** OpenSSL 3.x, BoringSSL для производительности

### Frontend
- **Framework:** React 18+ с TypeScript
- **State Management:** Redux Toolkit + RTK Query
- **UI Library:** Material-UI (MUI) v5
- **Charts:** Recharts, Apache ECharts
- **Real-time:** WebSocket, Server-Sent Events

### Infrastructure
- **Containerization:** Docker 24+, Docker Compose
- **Orchestration:** Kubernetes 1.28+ (Helm charts)
- **CI/CD:** GitLab CI / GitHub Actions
- **Monitoring:** Prometheus, Grafana, Loki
- **Logging:** Structured JSON logging → ELK/Loki

## 5. Модель безопасности

### 5.1. Уровни защиты
1. **Периметр:** Firewall, DDoS protection, rate limiting
2. **Транспорт:** TLS 1.3, mutual TLS для сервисов
3. **Приложение:** RBAC, input validation, SQL injection prevention
4. **Данные:** AES-256 encryption at rest, bcrypt/argon2 для паролей
5. **Аудит:** Полное логирование всех операций, immutable logs

### 5.2. RBAC модель
```
Roles:
- Super Admin (полный доступ)
- Security Admin (firewall, policies, IDS/IPS)
- Network Admin (routing, QoS, NAT)
- Billing Admin (тарифы, платежи, отчёты)
- Help Desk (просмотр, базовые операции)
- Auditor (только чтение логов и отчётов)
- User (self-service портал)

Permissions:
- resource:action (e.g., firewall:read, policy:write, billing:admin)
- Context-aware (по группам, VLAN, времени)
```

### 5.3. Соответствие требованиям
- **ФЗ-152:** Шифрование ПДн, разграничение доступа, аудит
- **ГОСТ Р 57580:** Требования к СЗИ
- **PCI DSS:** Для платёжных данных (если применимо)
- **Enterprise Hardening:** CIS Benchmarks для ОС и приложений

## 6. Масштабируемость

### Вертикальное масштабирование
- Многопоточная обработка запросов (uvicorn workers)
- Async I/O для сетевых операций
- Connection pooling для БД

### Горизонтальное масштабирование
- Stateless API сервисы (за исключением session data в Redis)
- Шардирование базы данных по tenant/customer
- Репликация PostgreSQL (master-slave, multi-master)
- Распределённый кэш Redis Cluster

### Кластеризация
- Kubernetes StatefulSets для БД
- Deployment для stateless сервисов
- HPA (Horizontal Pod Autoscaler) по CPU/memory/custom metrics
- Service mesh (Istio/Linkerd) для mTLS и observability

## 7. Производительность

### Целевые показатели
- **API Latency:** < 50ms (p95), < 200ms (p99)
- **Throughput:** 10,000+ RPS на узел API
- **Concurrent Users:** 10,000+ одновременных сессий
- **Traffic Processing:** 10 Gbps+ на узел (с аппаратным ускорением)
- **Rule Evaluation:** < 1ms на правило firewall

### Оптимизации
- Compiled regex для URL фильтрации (RE2 library)
- Bloom filters для blacklist lookup
- LRU cache для частых запросов
- Batch operations для БД
- Zero-copy networking где возможно

## 8. Отказоустойчивость

### Стратегии
- **Health Checks:** Liveness/readiness probes для всех сервисов
- **Circuit Breakers:** Для внешних интеграций (AD, RADIUS, ЕСИА)
- **Retry Logic:** Exponential backoff с jitter
- **Graceful Degradation:** При отказе второстепенных сервисов
- **Failover:** Автоматическое переключение на резервный канал/узел

### Recovery
- **Backup:** Ежедневные full + hourly incremental backups
- **Point-in-Time Recovery:** WAL archiving для PostgreSQL
- **Disaster Recovery:** Geo-redundant deployment option
- **RTO:** < 15 минут, **RPO:** < 5 минут
