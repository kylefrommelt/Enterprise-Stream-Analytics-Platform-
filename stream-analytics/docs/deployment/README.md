# Stream Analytics Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (for production deployment)
- Helm (for Kubernetes deployment)
- PostgreSQL 13+
- Python 3.8+

## Development Environment Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/stream-analytics.git
   cd stream-analytics
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

3. **Start Development Environment**
   ```bash
   docker-compose up -d
   ```

4. **Run Tests**
   ```bash
   pytest tests/
   ```

## Production Deployment

### Docker Compose Deployment

1. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start Services**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. **Verify Deployment**
   ```bash
   docker-compose ps
   ```

### Kubernetes Deployment

1. **Configure Helm Values**
   ```bash
   cp helm/values.yaml helm/values.prod.yaml
   # Edit values.prod.yaml with your configuration
   ```

2. **Deploy Using Helm**
   ```bash
   helm install stream-analytics ./helm -f ./helm/values.prod.yaml
   ```

3. **Verify Deployment**
   ```bash
   kubectl get pods
   kubectl get services
   ```

## Monitoring Setup

1. **Configure Prometheus**
   ```bash
   # Edit prometheus.yml with your targets
   docker-compose restart prometheus
   ```

2. **Configure Grafana**
   - Access Grafana at http://localhost:3000
   - Import dashboards from `monitoring/grafana/dashboards/`
   - Configure datasources

3. **Configure Alertmanager**
   - Edit `alertmanager.yml` with your notification settings
   - Restart Alertmanager

## Database Setup

1. **Initialize Database**
   ```bash
   # Run migrations
   alembic upgrade head
   ```

2. **Verify Database**
   ```bash
   psql -h localhost -U postgres -d stream_analytics
   \dt
   ```

## Scaling Considerations

### Horizontal Scaling

1. **Kafka Scaling**
   ```bash
   # Add more Kafka brokers
   docker-compose scale kafka=3
   ```

2. **Spark Scaling**
   ```bash
   # Configure Spark workers
   export SPARK_WORKER_INSTANCES=3
   ```

3. **PostgreSQL Scaling**
   ```bash
   # Configure read replicas
   docker-compose scale postgresql-replica=2
   ```

### Resource Limits

1. **Memory Limits**
   ```yaml
   # In docker-compose.yml
   services:
     spark:
       deploy:
         resources:
           limits:
             memory: 4G
   ```

2. **CPU Limits**
   ```yaml
   services:
     kafka:
       deploy:
         resources:
           limits:
             cpus: '2'
   ```

## Backup and Recovery

1. **Database Backup**
   ```bash
   # Create backup
   pg_dump -h localhost -U postgres stream_analytics > backup.sql
   ```

2. **Database Recovery**
   ```bash
   # Restore backup
   psql -h localhost -U postgres stream_analytics < backup.sql
   ```

## Troubleshooting

### Common Issues

1. **Kafka Connection Issues**
   ```bash
   # Check Kafka logs
   docker-compose logs kafka
   ```

2. **Spark Processing Issues**
   ```bash
   # Check Spark logs
   docker-compose logs spark
   ```

3. **Database Issues**
   ```bash
   # Check PostgreSQL logs
   docker-compose logs postgresql
   ```

### Health Checks

1. **Service Health**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Metrics Collection**
   ```bash
   curl http://localhost:8000/metrics
   ```

## Security Considerations

1. **API Authentication**
   ```bash
   # Generate API key
   python scripts/generate_api_key.py
   ```

2. **Database Security**
   ```bash
   # Change default passwords
   docker-compose exec postgresql psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'new_password';"
   ```

3. **Network Security**
   ```bash
   # Configure firewall rules
   ufw allow 9090/tcp  # Prometheus
   ufw allow 3000/tcp  # Grafana
   ufw allow 9093/tcp  # Alertmanager
   ``` 