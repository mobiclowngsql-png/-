# NetGuard Pro - DevOps Pipeline

## 1. CI/CD Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPER WORKFLOW                            │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │  Feature │───►│   Code   │───►│   Push   │                  │
│  │  Branch  │    │  Review  │    │   to     │                  │
│  │          │    │          │    │  Git     │                  │
│  └──────────┘    └──────────┘    └────┬─────┘                  │
│                                        │                         │
└────────────────────────────────────────┼────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────┐
│                    CI/CD PIPELINE                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              GitHub Actions / GitLab CI                   │  │
│  │                                                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │  │
│  │  │  Lint   │─►│  Test   │─►│ Security│─►│  Build  │    │  │
│  │  │  &      │  │  Unit   │  │  Scan   │  │  Docker │    │  │
│  │  │  Type   │  │  & Int  │  │  SAST   │  │  Image  │    │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │  │
│  │                                              │           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐     ▼           │  │
│  │  │ Deploy  │◄─│  E2E    │◄─│  Push   │  Registry      │  │
│  │  │  Prod   │  │  Tests  │  │  to     │  (Docker Hub)  │  │
│  │  └─────────┘  └─────────┘  │  Registry│                │  │
│  │                             └─────────┘                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────┐
│                    DEPLOYMENT TARGETS                            │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Development │  │  Staging    │  │ Production  │            │
│  │  (Auto)     │  │  (Manual)   │  │  (Manual)   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Kubernetes Cluster                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │   Dev    │  │  Stage   │  │   Prod   │              │   │
│  │  │ Namespace│  │ Namespace│  │ Namespace│              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 2. GitHub Actions Workflow

### .github/workflows/ci.yml
```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.11"
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  lint-and-type:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements-dev.txt
      
      - name: Lint with flake8
        run: |
          flake8 backend/app --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 backend/app --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
      
      - name: Check formatting with black
        run: |
          black --check backend/app
      
      - name: Type check with mypy
        run: |
          mypy backend/app --ignore-missing-imports

  test:
    runs-on: ubuntu-latest
    needs: lint-and-type
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: netguard_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install -r backend/requirements-dev.txt
      
      - name: Run unit tests
        run: |
          pytest backend/tests/unit \
            --cov=backend/app \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=80 \
            -v
      
      - name: Run integration tests
        run: |
          pytest backend/tests/integration \
            --cov=backend/app \
            --cov-append \
            -v
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/netguard_test
          REDIS_URL: redis://localhost:6379/0
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests

  security-scan:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Bandit (security linter)
        run: |
          bandit -r backend/app -f json -o bandit-report.json
      
      - name: Run Safety (dependency check)
        run: |
          safety check --json --output safety-report.json
      
      - name: Run Trivy on Dockerfile
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  build-docker:
    runs-on: ubuntu-latest
    needs: [test, security-scan]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=raw,value=latest
            type=semver,pattern={{version}}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/backend/Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            BUILD_DATE=${{ github.event.head_commit.timestamp }}
            VERSION=${{ github.sha }}

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build-docker
    environment: staging
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Staging
        run: |
          # Deploy to staging Kubernetes cluster
          kubectl set image deployment/netguard-backend \
            netguard-backend=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            -n netguard-staging
        
      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/netguard-backend -n netguard-staging --timeout=300s
      
      - name: Run smoke tests
        run: |
          pytest backend/tests/e2e/test_smoke.py \
            --base-url=https://staging.netguard.example.com

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Production
        run: |
          # Manual approval required via GitHub Environment
          kubectl set image deployment/netguard-backend \
            netguard-backend=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            -n netguard-prod
        
      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/netguard-backend -n netguard-prod --timeout=600s
      
      - name: Verify deployment
        run: |
          kubectl get pods -n netguard-prod -l app=netguard-backend
          kubectl get svc -n netguard-prod
      
      - name: Notify on success
        uses: slackapi/slack-github-action@v1
        with:
          channel-id: '#deployments'
          slack-message: "NetGuard Pro deployed to production: ${{ github.sha }}"
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
```

## 3. Docker Configuration

### docker/backend/Dockerfile
```dockerfile
# Multi-stage build for optimal image size
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# Runtime image
FROM python:3.11-slim as runtime

WORKDIR /app

# Create non-root user
RUN groupadd -r netguard && useradd -r -g netguard netguard

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    nftables \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy wheels from builder
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY backend/app ./app
COPY backend/pyproject.toml .

# Set ownership
RUN chown -R netguard:netguard /app

# Switch to non-root user
USER netguard

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Build arguments
ARG BUILD_DATE
ARG VERSION

# Labels
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.title="NetGuard Pro Backend" \
      org.opencontainers.image.vendor="NetGuard Team"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml (Development)
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: docker/backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=netguard
      - DB_USER=netguard
      - DB_PASSWORD=devpassword
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - SECRET_KEY=dev-secret-key-change-in-production
    volumes:
      - ./backend/app:/app/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=netguard
      - POSTGRES_USER=netguard
      - POSTGRES_PASSWORD=devpassword
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U netguard"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## 4. Versioning Strategy

### Semantic Versioning
```
MAJOR.MINOR.PATCH

Examples:
- 1.0.0 - Initial production release
- 1.2.0 - New features (backward compatible)
- 1.2.3 - Bug fixes
- 2.0.0 - Breaking changes
```

### Git Tagging
```bash
# Create version tag
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0

# Automated via GitHub Actions on release
```

### Changelog Format
```markdown
## [1.2.0] - 2024-01-15

### Added
- New feature X
- Integration with Y

### Changed
- Improved performance of Z

### Fixed
- Bug fix for issue #123

### Security
- Patched vulnerability CVE-XXXX-XXXX
```

## 5. Rollback Strategy

### Kubernetes Rollback
```bash
# Check rollout history
kubectl rollout history deployment/netguard-backend -n netguard-prod

# Rollback to previous version
kubectl rollout undo deployment/netguard-backend -n netguard-prod

# Rollback to specific revision
kubectl rollout undo deployment/netguard-backend -n netguard-prod --to-revision=2

# Watch rollback status
kubectl rollout status deployment/netguard-backend -n netguard-prod
```

### Database Rollback
```bash
# Using Alembic
alembic downgrade -1  # Downgrade one migration
alembic downgrade <revision_id>  # Specific revision

# Point-in-time recovery (PostgreSQL)
# Restore from WAL archive
```

### Automated Rollback Triggers
```yaml
# In deployment workflow
- name: Monitor deployment
  run: |
    # Check error rate
    ERROR_RATE=$(curl -s https://prometheus.netguard.internal/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m]))
    
    if (( $(echo "$ERROR_RATE > 0.1" | bc -l) )); then
      echo "High error rate detected, initiating rollback"
      kubectl rollout undo deployment/netguard-backend -n netguard-prod
      exit 1
    fi
```

## 6. Monitoring the Pipeline

### Key Metrics
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Build time | < 10 min | > 15 min |
| Test coverage | > 80% | < 70% |
| Deployment frequency | Daily | Weekly |
| Change failure rate | < 5% | > 10% |
| Mean time to recovery | < 1 hour | > 4 hours |

### Pipeline Dashboard
```yaml
# Grafana dashboard configuration
dashboard:
  title: "CI/CD Pipeline Metrics"
  panels:
    - title: "Build Duration"
      query: "github_actions_job_duration_seconds"
    - title: "Test Coverage Trend"
      query: "codecov_coverage_percentage"
    - title: "Deployment Success Rate"
      query: "deployment_success_rate"
    - title: "Rollback Frequency"
      query: "rollback_count"
```

## 7. Security Best Practices

### Secrets Management
```yaml
# Never commit secrets
# Use GitHub Secrets or external vault

# In workflow:
- name: Use secret
  run: echo "${{ secrets.DATABASE_PASSWORD }}"
  
# For production: HashiCorp Vault integration
- name: Get secrets from Vault
  uses: hashicorp/vault-action@v2
  with:
    url: https://vault.example.com
    token: ${{ secrets.VAULT_TOKEN }}
    secrets: |
      secret/data/netguard/prod DATABASE_PASSWORD;
```

### Image Signing
```bash
# Sign Docker images with Cosign
cosign sign --key cosign.key ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

# Verify before deployment
cosign verify --key cosign.pub ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
```

### Supply Chain Security
- Dependabot for dependency updates
- SLSA compliance level 3
- SBOM generation with Syft
- Vulnerability scanning with Trivy
