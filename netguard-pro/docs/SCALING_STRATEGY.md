# NetGuard Pro - Стратегия масштабирования и кластеризации

## 1. Архитектура масштабирования

### 1.1. Уровни масштабирования

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOAD BALANCER LAYER                          │
│              (HAProxy / NGINX / Cloud LB)                       │
│                                                                 │
│         ┌─────────────┬─────────────┬─────────────┐            │
│         │    LB-1     │    LB-2     │    LB-3     │            │
│         │  (Active)   │  (Active)   │   (Standby) │            │
│         └──────┬──────┴──────┬──────┴──────┬──────┘            │
└────────────────┼─────────────┼─────────────┼───────────────────┘
                 │             │             │
┌────────────────▼─────────────▼─────────────▼───────────────────┐
│                   API GATEWAY LAYER                             │
│                  (Stateless, Auto-scaling)                      │
│                                                                 │
│    ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐          │
│    │ API-1│  │ API-2│  │ API-3│  │API-N │  │API-N+1│         │
│    └───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘  └───┬───┘          │
│        │         │         │         │         │               │
│        └─────────┴────┬────┴─────────┴─────────┘               │
│                       │                                        │
└───────────────────────┼────────────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────────────┐
│                    SERVICE LAYER                                │
│           (Microservices / Modular Monolith)                    │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Auth      │  │   Policy    │  │   Billing   │            │
│  │  Service    │  │   Service   │  │   Service   │            │
│  │  [x2-x10]   │  │   [x2-x10]  │  │   [x2-x10]  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Firewall   │  │   Proxy     │  │  Monitoring │            │
│  │ Controller  │  │ Controller  │  │   Service   │            │
│  │   [x1-x5]   │  │   [x1-x5]   │  │   [x2-x10]  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────────────┐
│                   DATA LAYER                                    │
│              (Sharded, Replicated, Cached)                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   PostgreSQL Cluster                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │  Master  │◄─┤ Replica-1│◄─┤ Replica-N│              │   │
│  │  │ (Write)  │  │ (Read)   │  │ (Read)   │              │   │
│  │  └────┬─────┘  └──────────┘  └──────────┘              │   │
│  │       │                                                 │   │
│  │  ┌────▼──────────────────────────────────────┐          │   │
│  │  │         TimescaleDB (Time-series)         │          │   │
│  │  │    Traffic logs, Metrics, Events          │          │   │
│  │  │    [Partitioned by time + user_id]        │          │   │
│  │  └───────────────────────────────────────────┘          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Redis Cluster                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │ Master-1 │  │ Master-2 │  │ Master-N │              │   │
│  │  │ +Slave   │  │ +Slave   │  │ +Slave   │              │   │
│  │  │ (Shard)  │  │ (Shard)  │  │ (Shard)  │              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  │                                                          │   │
│  │  Use: Sessions, Cache, Pub/Sub, Rate Limiting           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Стратегии масштабирования

### 2.1. Горизонтальное масштабирование (Scale-Out)

#### API Gateway Layer
```yaml
# Kubernetes HPA Configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
```

#### Stateless Services
- Все API сервисы stateless
- Сессии хранятся в Redis Cluster
- Конфигурация через ConfigMap/Secrets
- Health checks для автоматического восстановления

### 2.2. Вертикальное масштабирование (Scale-Up)

#### Database Tier
| Компонент | Минимум | Рекомендуется | Максимум |
|-----------|---------|---------------|----------|
| **PostgreSQL Master** | 4 CPU, 8GB RAM | 8 CPU, 32GB RAM | 32 CPU, 256GB RAM |
| **PostgreSQL Replica** | 2 CPU, 4GB RAM | 4 CPU, 16GB RAM | 16 CPU, 128GB RAM |
| **Redis Master** | 2 CPU, 4GB RAM | 4 CPU, 8GB RAM | 8 CPU, 32GB RAM |
| **TimescaleDB** | 4 CPU, 8GB RAM | 8 CPU, 32GB RAM | 32 CPU, 256GB RAM |

### 2.3. Шардирование базы данных

#### Стратегия шардирования по tenant/customer
```python
# Shard key: organization_id / customer_id
# Each shard = independent PostgreSQL database

SHARD_CONFIG = {
    "shard_001": {
        "host": "pg-shard-001.internal",
        "port": 5432,
        "database": "netguard_001",
        "tenant_range": (1, 1000),  # Tenant IDs 1-1000
    },
    "shard_002": {
        "host": "pg-shard-002.internal",
        "port": 5432,
        "database": "netguard_002",
        "tenant_range": (1001, 2000),
    },
    # ... additional shards
}

# Shard routing middleware
async def get_shard_db(tenant_id: int) -> AsyncSession:
    """Get database session for specific shard."""
    shard_key = find_shard_for_tenant(tenant_id)
    engine = get_engine_for_shard(shard_key)
    async with engine() as session:
        return session
```

#### TimescaleDB гипертреблицы
```sql
-- Create hypertable for traffic logs
SELECT create_hypertable('traffic_logs', 'timestamp', 
                         chunk_time_interval => INTERVAL '1 day',
                         create_default_indexes => TRUE);

-- Add partitioning by user_id for multi-tenant
SELECT add_dimension('traffic_logs', 'user_id', 
                     number_partitions => 16,
                     column_type => 'integer');

-- Compression policy for old data
SELECT add_compression_policy('traffic_logs', 
                              INTERVAL '7 days',
                              if_not_exists => TRUE);

-- Continuous aggregates for fast reporting
CREATE MATERIALIZED VIEW traffic_stats_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS hour,
    user_id,
    SUM(bytes_in) as total_bytes_in,
    SUM(bytes_out) as total_bytes_out,
    COUNT(*) as packet_count
FROM traffic_logs
GROUP BY hour, user_id
WITH NO DATA;
```

## 3. Кластеризация

### 3.1. PostgreSQL Cluster (Patroni + etcd)

```yaml
# patroni.yml configuration
scope: netguard-postgres
namespace: /db/
name: pg-node-1

restapi:
  listen: 0.0.0.0:8008
  connect_address: pg-node-1.internal:8008

etcd:
  hosts:
    - etcd-1.internal:2379
    - etcd-2.internal:2379
    - etcd-3.internal:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    synchronous_mode: true
    postgresql:
      use_pg_rewind: true
      parameters:
        wal_level: replica
        hot_standby: "on"
        max_wal_senders: 10
        max_replication_slots: 10
        synchronous_commit: remote_apply

postgresql:
  listen: 0.0.0.0:5432
  connect_address: pg-node-1.internal:5432
  data_dir: /var/lib/postgresql/data
  pgpass: /tmp/pgpass
  authentication:
    replication:
      username: replicator
      password: secure_password
    superuser:
      username: postgres
      password: secure_password
  parameters:
    unix_socket_directories: '.'
    shared_buffers: 4GB
    effective_cache_size: 12GB
    work_mem: 64MB
    maintenance_work_mem: 512MB
    checkpoint_completion_target: 0.9
    wal_buffers: 16MB
    default_statistics_target: 100

tags:
  nofailover: false
  noloadbalance: false
  clonefrom: false
  nosync: false
```

### 3.2. Redis Cluster

```bash
# Redis Cluster setup (6 nodes: 3 masters + 3 slaves)
redis-cli --cluster create \
  redis-node-1:6379 redis-node-2:6379 redis-node-3:6379 \
  redis-node-4:6379 redis-node-5:6379 redis-node-6:6379 \
  --cluster-replicas 1 \
  --cluster-yes

# Cluster configuration
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
cluster-require-full-coverage no
cluster-replica-validity-factor 10
```

### 3.3. Kubernetes Cluster Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Control Plane                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Master  │  │  Master  │  │  Master  │  (HA, 3 nodes)   │
│  │   Node   │  │   Node   │  │   Node   │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                     Worker Nodes                              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Worker-1   │  │   Worker-N   │  │   Worker-M   │      │
│  │              │  │              │  │              │      │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │      │
│  │ │   Pod    │ │  │ │   Pod    │ │  │ │   Pod    │ │      │
│  │ │  (API)   │ │  │ │(Service) │ │  │ │  (DB)    │ │      │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │      │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │      │
│  │ │   Pod    │ │  │ │   Pod    │ │  │ │   Pod    │ │      │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 4. Производительность и оптимизация

### 4.1. Кэширование

#### Многоуровневое кэширование
```python
# L1: In-memory cache (per-instance)
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_permissions(user_id: int, resource: str) -> set:
    # Fast lookup for frequently accessed data
    ...

# L2: Redis cache (shared)
class RedisCache:
    def __init__(self):
        self.redis = redis.asyncio.from_url(settings.redis.url)
    
    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        await self.redis.setex(key, ttl, json.dumps(value))

# L3: Database query cache (TimescaleDB continuous aggregates)
# See hypertable examples above
```

### 4.2. Connection Pooling

```python
# SQLAlchemy pool configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_size=50,           # Connections kept in pool
    max_overflow=100,       # Additional connections when needed
    pool_timeout=30,        # Seconds to wait for connection
    pool_pre_ping=True,     # Verify connection before use
    pool_recycle=3600,      # Recycle connections after 1 hour
    echo=False,
)

# Redis connection pool
redis_pool = redis.asyncio.ConnectionPool(
    host=settings.redis.host,
    port=settings.redis.port,
    password=settings.redis.password,
    db=settings.redis.db,
    max_connections=100,
    decode_responses=True,
)
```

### 4.3. Асинхронная обработка

```python
# Celery task queue for background operations
from celery import Celery

celery_app = Celery(
    'netguard',
    broker=settings.redis.url,
    backend=settings.redis.url,
)

celery_app.conf.update(
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_track_started=True,
    task_time_limit=300,
    result_expires=3600,
)

@celery_app.task(bind=True, max_retries=3)
def process_traffic_accounting(self, user_id: int, bytes_count: int):
    try:
        # Process accounting
        update_user_balance(user_id, bytes_count)
    except Exception as e:
        raise self.retry(exc=e, countdown=60)
```

## 5. Мониторинг и алертинг

### 5.1. Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Business metrics
ACTIVE_USERS = Gauge(
    'active_users_total',
    'Number of active users'
)

TRAFFIC_PROCESSED = Counter(
    'traffic_bytes_total',
    'Total traffic processed',
    ['direction', 'protocol']
)

BILLING_OPERATIONS = Counter(
    'billing_operations_total',
    'Billing operations count',
    ['operation_type', 'status']
)
```

### 5.2. Alert Rules

```yaml
# prometheus_alerts.yml
groups:
- name: netguard_alerts
  rules:
  - alert: HighAPILatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High API latency detected"
      description: "95th percentile latency is {{ $value }}s"

  - alert: DatabaseConnectionPoolExhausted
    expr: db_pool_available_connections == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database connection pool exhausted"

  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value | humanizePercentage }}"

  - alert: RedisMemoryHigh
    expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Redis memory usage high"
```

## 6. Disaster Recovery

### 6.1. Backup Strategy

| Тип данных | Частота | Хранение | RPO | RTO |
|------------|---------|----------|-----|-----|
| PostgreSQL | Continuous WAL + Daily full | S3 + Local | 5 min | 15 min |
| Redis | Hourly RDB snapshots | S3 | 1 hour | 30 min |
| Configurations | On change | Git + S3 | 0 | 5 min |
| Logs | Real-time streaming | ELK/Loki | N/A | N/A |

### 6.2. Geo-Redundancy

```
┌─────────────────────────────────────────────────────────────┐
│                    Primary Region (Active)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │     App     │  │     DB      │  │    Cache    │         │
│  │   Cluster   │  │   Cluster   │  │   Cluster   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                          │
              Async Replication
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                 Secondary Region (Passive)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │     App     │  │     DB      │  │    Cache    │         │
│  │   Cluster   │  │   Replica   │  │   Replica   │         │
│  │  (Scaled    │  │  (Warm      │  │  (Warm      │         │
│  │   Down)     │  │   Standby)  │  │   Standby)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 7. Рекомендации по развертыванию

### 7.1. Для 10-100 пользователей
- 1 API instance (2 CPU, 4GB RAM)
- 1 PostgreSQL (2 CPU, 4GB RAM)
- 1 Redis (1 CPU, 2GB RAM)
- Single-zone deployment

### 7.2. Для 100-1000 пользователей
- 2-3 API instances behind LB
- PostgreSQL with 1 replica
- Redis with persistence
- Multi-AZ deployment

### 7.3. Для 1000-10000 пользователей
- 5-10 API instances with auto-scaling
- PostgreSQL cluster (Patroni) with 2 replicas
- Redis Cluster (3 masters + 3 slaves)
- TimescaleDB for analytics
- Multi-region ready

### 7.4. Для 10000+ пользователей
- 10+ API instances across multiple zones
- Sharded PostgreSQL by tenant
- Redis Cluster with dedicated shards
- Dedicated monitoring infrastructure
- Full geo-redundancy with failover
