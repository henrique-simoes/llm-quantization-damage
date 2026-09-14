# Grafana provisioning — compose change (for the lead, deployment phase D3)

Nothing here has been applied. The `tel-grafana` container and
`/srv/bench/telemetry/docker-compose.yml` are untouched.

## 1. Copy the provisioning tree to the host

```bash
sudo mkdir -p /srv/bench/telemetry/grafana-provisioning
sudo rsync -a --delete \
  <repo>/infra/telemetry/grafana/provisioning/ \
  /srv/bench/telemetry/grafana-provisioning/
# Grafana runs as uid 472 and only reads these files, so world-readable is enough.
sudo chmod -R a+rX /srv/bench/telemetry/grafana-provisioning
```

Do **not** mount it under `/srv/bench/telemetry/grafana` — that directory is Grafana's
`/var/lib/grafana` data volume.

## 2. Edit the `grafana` service in `/srv/bench/telemetry/docker-compose.yml`

Current:

```yaml
  grafana:
    image: grafana/grafana-oss:latest
    container_name: tel-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=<set on host>
      - GF_ANALYTICS_REPORTING_ENABLED=false
      - GF_ANALYTICS_CHECK_FOR_UPDATES=false
    volumes:
      - /srv/bench/telemetry/grafana:/var/lib/grafana
```

Required (two additions, marked `# ADDED`):

```yaml
  grafana:
    image: grafana/grafana-oss:latest
    container_name: tel-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    extra_hosts:                                                        # ADDED
      - "host.docker.internal:host-gateway"                             # ADDED: reach Prometheus on the host's :9091
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=<set on host>
      - GF_ANALYTICS_REPORTING_ENABLED=false
      - GF_ANALYTICS_CHECK_FOR_UPDATES=false
    volumes:
      - /srv/bench/telemetry/grafana:/var/lib/grafana
      - /srv/bench/telemetry/grafana-provisioning:/etc/grafana/provisioning:ro   # ADDED
```

The read-only mount replaces the image's default (empty) `/etc/grafana/provisioning`, so it must
contain every subdirectory Grafana scans. The repo tree already has `datasources/` and
`dashboards/`. Grafana logs a harmless warning for missing `plugins/`, `alerting/` and
`notifiers/` directories; create them empty if you want a clean log.

## 3. Recreate only Grafana

```bash
cd /srv/bench/telemetry
docker compose config --quiet                       # syntax check
docker compose up -d --no-deps --force-recreate grafana
```

## 4. Verify

```bash
curl -s -u "$GRAFANA_AUTH" localhost:3000/api/datasources/uid/prom-multivac | python3 -m json.tool | head
curl -s -u "$GRAFANA_AUTH" -X POST localhost:3000/api/datasources/uid/prom-multivac/health   # "status":"OK"
curl -s -u "$GRAFANA_AUTH" 'localhost:3000/api/search?type=dash-db' | python3 -m json.tool   # 4 dashboards in "multivac LLM serving"
```

If the datasource health check fails with a connection error, the host firewall is blocking the
docker bridge from reaching `:9091`; Prometheus listens on all interfaces (`--web.listen-address=:9091`).

> **Superseded in deployment (DEC-T8, 2026-09-14).** The bridge-network variant above could not reach
> Prometheus on the host (connection timed out). The deployed service uses `network_mode: host`
> (no `ports:` / `extra_hosts:`), and the datasource URL is `http://localhost:9091`. Credentials are
> set on the host only; export `GRAFANA_AUTH=user:password` for the commands above.
