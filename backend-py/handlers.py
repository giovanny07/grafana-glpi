"""
Handlers para cada query_type.
Cada función recibe (api: GlpiAPI, req: QueryRequest) y retorna build_response(columns, rows).
"""
from datetime import datetime
from collections import defaultdict
from glpi_client import build_response

# ── Constantes GLPI ──────────────────────────────────────────────────────────

STATUS_NAMES = {1: "New", 2: "Assigned", 3: "Planned", 4: "Waiting", 5: "Solved", 6: "Closed"}
PRIORITY_NAMES = {1: "Very low", 2: "Low", 3: "Medium", 4: "High", 5: "Very high", 6: "Major"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _ticket_search_criteria(filters) -> list[dict]:
    """Construye criterios de búsqueda GLPI desde los filtros del request."""
    criteria = []
    if filters.status:
        for i, s in enumerate(filters.status):
            criteria.append({"link": "OR" if i > 0 else "AND", "field": 12, "searchtype": "equals", "value": s})
    if filters.priority:
        for i, p in enumerate(filters.priority):
            criteria.append({"link": "OR" if i > 0 else "AND", "field": 3, "searchtype": "equals", "value": p})
    if filters.category_id:
        criteria.append({"field": 7, "searchtype": "equals", "value": filters.category_id})
    if filters.technician_id:
        criteria.append({"field": 5, "searchtype": "equals", "value": filters.technician_id})
    if filters.ticket_type:
        criteria.append({"field": 14, "searchtype": "equals", "value": filters.ticket_type})
    return criteria

def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def _date_criteria(time_from: str, time_to: str) -> list[dict]:
    """Filtra por fecha de creación dentro del time range de Grafana."""
    return [
        {"field": 15, "searchtype": "morethan",  "value": _parse_dt(time_from).strftime("%Y-%m-%d %H:%M:%S")},
        {"field": 15, "searchtype": "lessthan",  "value": _parse_dt(time_to).strftime("%Y-%m-%d %H:%M:%S")},
    ]

def _get_all_tickets(api, req, extra_fields: list[int] = None) -> list[dict]:
    """Fetch paginado de tickets con filtros aplicados."""
    criteria = _date_criteria(req.time_from, req.time_to) + _ticket_search_criteria(req.filters)
    # Campos base: id(2), título(1), status(12), prioridad(3), fecha_creación(15), categoría(7)
    forcedisplay = [1, 2, 3, 7, 12, 15]
    if extra_fields:
        forcedisplay += [f for f in extra_fields if f not in forcedisplay]

    kwargs = {"forcedisplay": forcedisplay}
    if criteria:
        kwargs["criteria"] = criteria
    if req.filters.entity_id is not None:
        kwargs["is_recursive"] = True  # incluye sub-entidades

    return api.ticket.get_all_pages(page_size=min(req.max_results, 200), **kwargs)

# ── Handlers ──────────────────────────────────────────────────────────────────

def ticket_summary(api, req) -> dict:
    """Totales por estado — ideal para Stat panels y Pie charts."""
    tickets = _get_all_tickets(api, req)
    counts = defaultdict(int)
    for t in tickets:
        status = t.get("status", t.get("12", 1))
        counts[STATUS_NAMES.get(int(status), str(status))] += 1

    columns = [{"name": "status", "type": "string"}, {"name": "count", "type": "number"}]
    rows = [[name, cnt] for name, cnt in sorted(counts.items())]
    return build_response(columns, rows)


def ticket_trend(api, req) -> dict:
    """Serie de tiempo de tickets — ideal para Time series panels."""
    tickets = _get_all_tickets(api, req)
    interval = req.trend_options.interval if req.trend_options else "day"
    group_by = req.trend_options.group_by if req.trend_options else "none"

    def bucket(dt_str: str) -> str:
        dt = datetime.strptime(dt_str[:19], "%Y-%m-%d %H:%M:%S")
        if interval == "hour":  return dt.strftime("%Y-%m-%dT%H:00:00Z")
        if interval == "week":  return dt.strftime("%Y-W%W")
        if interval == "month": return dt.strftime("%Y-%m-01T00:00:00Z")
        return dt.strftime("%Y-%m-%dT00:00:00Z")  # day

    if group_by == "none":
        counts = defaultdict(int)
        for t in tickets:
            counts[bucket(t.get("date", t.get("15", "")))] += 1
        columns = [{"name": "time", "type": "time"}, {"name": "count", "type": "number"}]
        rows = [[ts, cnt] for ts, cnt in sorted(counts.items())]
    else:
        field_map = {"status": ("status", "12", STATUS_NAMES),
                     "priority": ("priority", "3", PRIORITY_NAMES)}
        key_name, key_id, name_map = field_map.get(group_by, ("status", "12", STATUS_NAMES))
        counts = defaultdict(lambda: defaultdict(int))
        groups = set()
        for t in tickets:
            ts = bucket(t.get("date", t.get("15", "")))
            val = name_map.get(int(t.get(key_name, t.get(key_id, 1))), "Unknown")
            counts[ts][val] += 1
            groups.add(val)
        groups = sorted(groups)
        columns = [{"name": "time", "type": "time"}] + [{"name": g, "type": "number"} for g in groups]
        rows = [[ts] + [counts[ts].get(g, 0) for g in groups] for ts in sorted(counts)]

    return build_response(columns, rows)


def ticket_list(api, req) -> dict:
    """Tabla raw de tickets — ideal para Table panels."""
    # Campo 19 = técnico asignado, campo 8 = grupo asignado
    tickets = _get_all_tickets(api, req, extra_fields=[5, 8, 19, 17, 18])
    columns = [
        {"name": "id",         "type": "number"},
        {"name": "title",      "type": "string"},
        {"name": "status",     "type": "string"},
        {"name": "priority",   "type": "string"},
        {"name": "category",   "type": "string"},
        {"name": "created",    "type": "time"},
    ]
    rows = []
    for t in tickets[:req.max_results]:
        rows.append([
            t.get("id", t.get("2")),
            t.get("name", t.get("1", "")),
            STATUS_NAMES.get(int(t.get("status", t.get("12", 1))), "?"),
            PRIORITY_NAMES.get(int(t.get("priority", t.get("3", 3))), "?"),
            t.get("itilcategories_id", t.get("7", "")),
            t.get("date", t.get("15", "")),
        ])
    return build_response(columns, rows)


def ticket_by_category(api, req) -> dict:
    """Distribución por categoría ITIL — Bar chart."""
    tickets = _get_all_tickets(api, req, extra_fields=[7])
    counts = defaultdict(int)
    for t in tickets:
        cat = t.get("itilcategories_id", t.get("7", "Uncategorized")) or "Uncategorized"
        counts[str(cat)] += 1
    columns = [{"name": "category", "type": "string"}, {"name": "count", "type": "number"}]
    rows = sorted([[k, v] for k, v in counts.items()], key=lambda x: x[1], reverse=True)
    return build_response(columns, rows)


def ticket_by_technician(api, req) -> dict:
    """Carga por técnico — Bar chart."""
    tickets = _get_all_tickets(api, req, extra_fields=[5, 19])
    counts = defaultdict(int)
    for t in tickets:
        tech = t.get("users_id_assign", t.get("5", "Unassigned")) or "Unassigned"
        counts[str(tech)] += 1
    columns = [{"name": "technician", "type": "string"}, {"name": "tickets", "type": "number"}]
    rows = sorted([[k, v] for k, v in counts.items()], key=lambda x: x[1], reverse=True)
    return build_response(columns, rows)


def sla_compliance(api, req) -> dict:
    """% tickets dentro de SLA — Gauge / Stat."""
    tickets = _get_all_tickets(api, req, extra_fields=[17, 18, 30, 31])
    total = len(tickets)
    if total == 0:
        return build_response([{"name": "compliance_pct", "type": "number"}], [[None]])

    # Campo 30/31 = tiempo_resolución_excedido (aproximación sin SLA API)
    # Por ahora: solved tickets donde closedate <= due date
    within = sum(1 for t in tickets if t.get("status", t.get("12", 1)) in [5, 6])
    pct = round((within / total) * 100, 2) if req.sla_options and req.sla_options.show_percentage else within

    columns = [
        {"name": "total",      "type": "number"},
        {"name": "within_sla", "type": "number"},
        {"name": "value",      "type": "number"},
    ]
    label = "compliance_pct" if (req.sla_options and req.sla_options.show_percentage) else "within_sla_count"
    columns[2]["name"] = label
    return build_response(columns, [[total, within, pct]])


def sla_breaches(api, req) -> dict:
    """Tickets que excedieron SLA — Table."""
    # Tickets abiertos con estado != solved/closed
    tickets = _get_all_tickets(api, req, extra_fields=[5, 17, 18])
    open_tickets = [t for t in tickets if int(t.get("status", t.get("12", 1))) not in [5, 6]]
    columns = [
        {"name": "id",       "type": "number"},
        {"name": "title",    "type": "string"},
        {"name": "priority", "type": "string"},
        {"name": "created",  "type": "time"},
        {"name": "status",   "type": "string"},
    ]
    rows = [
        [
            t.get("id", t.get("2")),
            t.get("name", t.get("1", "")),
            PRIORITY_NAMES.get(int(t.get("priority", t.get("3", 3))), "?"),
            t.get("date", t.get("15", "")),
            STATUS_NAMES.get(int(t.get("status", t.get("12", 1))), "?"),
        ]
        for t in open_tickets[:req.max_results]
    ]
    return build_response(columns, rows)


def resolution_time(api, req) -> dict:
    """Tiempo promedio de resolución — Stat / Histogram."""
    tickets = _get_all_tickets(api, req, extra_fields=[17, 18])
    unit = req.resolution_options.unit if req.resolution_options else "hours"
    show_p95 = req.resolution_options.show_percentile if req.resolution_options else False

    divisors = {"minutes": 60, "hours": 3600, "days": 86400}
    divisor = divisors.get(unit, 3600)

    durations = []
    for t in tickets:
        created = t.get("date", t.get("15", ""))
        closed  = t.get("closedate", t.get("17", "")) or t.get("solvedate", t.get("18", ""))
        if created and closed:
            try:
                c = datetime.strptime(created[:19], "%Y-%m-%d %H:%M:%S")
                r = datetime.strptime(closed[:19],  "%Y-%m-%d %H:%M:%S")
                durations.append((r - c).total_seconds() / divisor)
            except Exception:
                pass

    if not durations:
        cols = [{"name": f"avg_{unit}", "type": "number"}]
        if show_p95:
            cols.append({"name": f"p95_{unit}", "type": "number"})
        return build_response(cols, [[None] + ([None] if show_p95 else [])])

    avg = round(sum(durations) / len(durations), 2)
    cols = [{"name": f"avg_{unit}", "type": "number"}]
    row = [avg]

    if show_p95:
        sorted_d = sorted(durations)
        idx = int(len(sorted_d) * 0.95)
        p95 = round(sorted_d[idx], 2)
        cols.append({"name": f"p95_{unit}", "type": "number"})
        row.append(p95)

    return build_response(cols, [row])


def priority_breakdown(api, req) -> dict:
    """Distribución por prioridad — Pie chart."""
    tickets = _get_all_tickets(api, req)
    counts = defaultdict(int)
    for t in tickets:
        p = int(t.get("priority", t.get("3", 3)))
        counts[PRIORITY_NAMES.get(p, str(p))] += 1
    columns = [{"name": "priority", "type": "string"}, {"name": "count", "type": "number"}]
    rows = [[k, v] for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)]
    return build_response(columns, rows)


def asset_count(api, req) -> dict:
    """Total de assets por tipo — Stat panel."""
    itemtype = req.asset_options.itemtype if req.asset_options else "Computer"
    proxy = api.item(itemtype)
    items = proxy.get_all_pages(page_size=1)  # solo necesitamos el total
    # get_all_pages devuelve lista; el total real viene del header Content-Range
    # hacemos una llamada mínima y contamos
    all_items = proxy.get_all_pages(page_size=200)
    columns = [{"name": "itemtype", "type": "string"}, {"name": "count", "type": "number"}]
    return build_response(columns, [[itemtype, len(all_items)]])


def asset_list(api, req) -> dict:
    """Inventario de assets — Table panel."""
    itemtype = req.asset_options.itemtype if req.asset_options else "Computer"
    proxy = api.item(itemtype)
    items = proxy.get_all_pages(page_size=min(req.max_results, 200))
    columns = [
        {"name": "id",       "type": "number"},
        {"name": "name",     "type": "string"},
        {"name": "serial",   "type": "string"},
        {"name": "location", "type": "string"},
        {"name": "status",   "type": "string"},
    ]
    rows = [
        [
            i.get("id"),
            i.get("name", ""),
            i.get("serial", ""),
            i.get("locations_id", ""),
            i.get("states_id", ""),
        ]
        for i in items[:req.max_results]
    ]
    return build_response(columns, rows)


def user_workload(api, req) -> dict:
    """Tickets abiertos por técnico — Bar chart."""
    # Solo tickets no cerrados
    from routers.query import Filters
    open_req = type('R', (), {
        'filters': type('F', (), {**req.filters.__dict__, 'status': [1,2,3,4]})(),
        'time_from': req.time_from,
        'time_to': req.time_to,
        'max_results': req.max_results,
    })()
    tickets = _get_all_tickets(api, req, extra_fields=[5])
    open_tickets = [t for t in tickets if int(t.get("status", t.get("12", 1))) not in [5, 6]]
    counts = defaultdict(int)
    for t in open_tickets:
        tech = t.get("users_id_assign", t.get("5", "Unassigned")) or "Unassigned"
        counts[str(tech)] += 1
    columns = [{"name": "technician", "type": "string"}, {"name": "open_tickets", "type": "number"}]
    rows = sorted([[k, v] for k, v in counts.items()], key=lambda x: x[1], reverse=True)
    return build_response(columns, rows)


def entity_summary(api, req) -> dict:
    """Métricas clave por entidad GLPI — Table."""
    entities = api.entity.get_all_pages()
    columns = [
        {"name": "entity",       "type": "string"},
        {"name": "total_tickets","type": "number"},
        {"name": "open_tickets", "type": "number"},
    ]
    rows = []
    for entity in entities[:20]:  # limitar para no sobrecargar
        eid = entity.get("id")
        name = entity.get("name", str(eid))
        # Query rápida por entidad
        try:
            result = api.ticket.search(
                criteria=[{"field": 80, "searchtype": "equals", "value": eid}],
                forcedisplay=[12],
                range="0-0",
            )
            total = result.get("totalcount", 0)
            open_r = api.ticket.search(
                criteria=[
                    {"field": 80, "searchtype": "equals", "value": eid},
                    {"field": 12, "searchtype": "equals", "value": 1},
                ],
                forcedisplay=[12],
                range="0-0",
            )
            open_cnt = open_r.get("totalcount", 0)
            rows.append([name, total, open_cnt])
        except Exception:
            rows.append([name, None, None])
    return build_response(columns, rows)


def satisfaction(api, req) -> dict:
    """Rating promedio de encuestas de satisfacción — Gauge."""
    # GLPI guarda satisfacción en TicketSatisfaction
    try:
        items = api.item("TicketSatisfaction").get_all_pages(page_size=200)
        ratings = [float(i["satisfaction"]) for i in items if i.get("satisfaction") is not None]
        avg = round(sum(ratings) / len(ratings), 2) if ratings else None
        columns = [
            {"name": "avg_satisfaction", "type": "number"},
            {"name": "responses",        "type": "number"},
        ]
        return build_response(columns, [[avg, len(ratings)]])
    except Exception as e:
        return build_response([{"name": "error", "type": "string"}], [[str(e)]])
