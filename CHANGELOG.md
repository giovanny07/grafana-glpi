# Changelog

## 1.0.0 (2026-03-20)

### Features

- 14 query types: ticket summary, ticket trend, ticket list, by category, by technician, SLA compliance, SLA breaches, resolution time, priority breakdown, asset count, asset list, user workload, entity summary, satisfaction
- Go backend plugin with `DataSourceWithBackend` — credentials never reach the browser
- Python FastAPI sidecar powered by `glpi-utils` — full GLPI 9/10/11 compatibility
- ConfigEditor: GLPI URL, App token, User token / username+password (stored encrypted), SSL toggle, default entity, backend URL
- QueryEditor: per-type contextual options — trend interval/group, SLA id, resolution time unit + p95, asset type
- Common filters on all query types: entity, status (multi), priority (multi), category
- Health check on Save & Test — validates GLPI connection end-to-end
- Alerting and annotations support enabled
- Compatible with Grafana >=10.0.0
- GLPI 11.0.x tested and confirmed working
