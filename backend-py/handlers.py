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
    return [
        {"field": 15, "searchtype": "morethan",  "value": _parse_dt(time_from).strftime("%Y-%m-%d %H:%M:%S")},
        {"field": 15, "searchtype": "lessthan",  "value": _parse_dt(time_to).strftime("%Y-%m-%d %H:%M:%S")},
    ]

def _get_all_tickets(api, req, extra_fields: list[int] = None) -> list[dict]:
    """Fetch paginado con expand_dropdowns para obtener nombres en lugar de IDs."""
    criteria = _date_criteria(req.time_from, req.time_to) + _ticket_search_criteria(req.filters)
    forcedisplay = [1, 2, 3, 7, 12, 15]
    if extra_fields:
        forcedisplay += [f for f in extra_fields if f not in forcedisplay]

    kwargs = {
        "forcedisplay": forcedisplay,
        "expand_dropdowns": True,  # nombres en lugar de IDs
    }
    if criteria:
        kwargs["criteria"] = criteria

    return api.ticket.get_all_pages(page_size=min(req.max_results, 200), **kwargs)

def _str(val, fallback="Unknown") -> str:
    if val is None or val == "" or val == 0:
        return fallback
    return str(val)

def _bucket(dt_str: str, interval: str) -> str:
    try:
        dt = datetime.strptime(str(dt_str)[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return "unknown"
    if interval == "hour":  return dt.strftime("%Y-%m-%dT%H:00:00Z")
    if interval == "week":  return dt.strftime("%Y-W%W")
    if interval == "month": return dt.strftime("%Y-%m-01T00:00:00Z")
    return dt.strftime("%Y-%m-%dT00:00:00Z")

def _parse_dt_str(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

# ── Handlers ──────────────────────────────────────────────────────────────────

def ticket_summary(api, req) -> dict:
    """Totales por estado — Stat / Pie / Bar."""
    tickets = _get_all_tickets(api, req)
    counts = defaultdict(int)
    for t in tickets:
        # Con expand_dropdowns el status viene como string nombre
        raw = t.get("status", t.get("12", 1))
        if isinstance(raw, int):
            label = STATUS_NAMES.get(raw, str(raw))
        else:
            label = str(raw) if raw else "Unknown"
        counts[label] += 1

    columns = [{"name": "status", "type": "string"}, {"name": "count", "type": "number"}]
    rows = [[name, cnt] for name, cnt in sorted(counts.items())]
    return build_response(columns, rows)


def ticket_trend(api, req) -> dict:
    """Serie de tiempo — Time series panel."""
    tickets = _get_all_tickets(api, req)
    interval = req.trend_options.interval if req.trend_options else "day"
    group_by  = req.trend_options.group_by  if req.trend_options else "none"

    date_field = "date"

    if group_by == "none":
        counts = defaultdict(int)
        for t in tickets:
            counts[_bucket(t.get(date_field, ""), interval)] += 1
        columns = [{"name": "time", "type": "time"}, {"name": "count", "type": "number"}]
        rows = [[ts, cnt] for ts, cnt in sorted(counts.items()) if ts != "unknown"]
    else:
        counts = defaultdict(lambda: defaultdict(int))
        groups = set()
        for t in tickets:
            ts  = _bucket(t.get(date_field, ""), interval)
            if ts == "unknown":
                continue
            if group_by == "status":
                raw = t.get("status", t.get("12", 1))
                val = STATUS_NAMES.get(raw, str(raw)) if isinstance(raw, int) else _str(raw)
            elif group_by == "priority":
                raw = t.get("priority", t.get("3", 3))
                val = PRIORITY_NAMES.get(raw, str(raw)) if isinstance(raw, int) else _str(raw)
            else:
                val = _str(t.get("itilcategories_id", t.get("7")), "Uncategorized")
            counts[ts][val] += 1
            groups.add(val)
        groups = sorted(groups)
        columns = [{"name": "time", "type": "time"}] + [{"name": g, "type": "number"} for g in groups]
        rows = [[ts] + [counts[ts].get(g, 0) for g in groups] for ts in sorted(counts)]

    return build_response(columns, rows)


def ticket_list(api, req) -> dict:
    """Tabla raw de tickets — Table panel."""
    tickets = _get_all_tickets(api, req, extra_fields=[5, 8, 17, 18])
    columns = [
        {"name": "id",         "type": "number"},
        {"name": "title",      "type": "string"},
        {"name": "status",     "type": "string"},
        {"name": "priority",   "type": "string"},
        {"name": "category",   "type": "string"},
        {"name": "technician", "type": "string"},
        {"name": "created",    "type": "time"},
    ]
    rows = []
    for t in tickets[:req.max_results]:
        raw_status   = t.get("status",   t.get("12", 1))
        raw_priority = t.get("priority", t.get("3",  3))
        rows.append([
            t.get("id",   t.get("2")),
            _str(t.get("name", t.get("1")),   "—"),
            STATUS_NAMES.get(raw_status,   str(raw_status))   if isinstance(raw_status,   int) else _str(raw_status),
            PRIORITY_NAMES.get(raw_priority, str(raw_priority)) if isinstance(raw_priority, int) else _str(raw_priority),
            _str(t.get("itilcategories_id", t.get("7")),  "Uncategorized"),
            _str(t.get("users_id_assign",   t.get("5")),  "Unassigned"),
            t.get("date", t.get("15", "")),
        ])
    return build_response(columns, rows)


def ticket_by_category(api, req) -> dict:
    """Distribución por categoría ITIL — Bar chart."""
    tickets = _get_all_tickets(api, req, extra_fields=[7])
    counts = defaultdict(int)
    for t in tickets:
        cat = _str(t.get("itilcategories_id", t.get("7")), "Uncategorized")
        counts[cat] += 1
    columns = [{"name": "category", "type": "string"}, {"name": "count", "type": "number"}]
    rows = sorted([[k, v] for k, v in counts.items()], key=lambda x: x[1], reverse=True)
    return build_response(columns, rows)


def ticket_by_technician(api, req) -> dict:
    """Carga por técnico — Bar chart."""
    tickets = _get_all_tickets(api, req, extra_fields=[5])
    counts = defaultdict(int)
    for t in tickets:
        tech = _str(t.get("users_id_assign", t.get("5")), "Unassigned")
        counts[tech] += 1
    columns = [{"name": "technician", "type": "string"}, {"name": "tickets", "type": "number"}]
    rows = sorted([[k, v] for k, v in counts.items()], key=lambda x: x[1], reverse=True)
    return build_response(columns, rows)


def sla_compliance(api, req) -> dict:
    """% tickets dentro de SLA — Gauge / Stat."""
    tickets = _get_all_tickets(api, req)
    total = len(tickets)
    if total == 0:
        return build_response(
            [{"name": "total", "type": "number"}, {"name": "within_sla", "type": "number"}, {"name": "value", "type": "number"}],
            [[0, 0, None]]
        )

    within = sum(1 for t in tickets if (
        t.get("status", t.get("12", 1)) in [5, 6] or
        str(t.get("status", "")).lower() in ["solved", "closed"]
    ))
    show_pct = req.sla_options.show_percentage if req.sla_options else True
    value = round((within / total) * 100, 2) if show_pct else within
    label = "compliance_pct" if show_pct else "within_sla_count"

    columns = [
        {"name": "total",   "type": "number"},
        {"name": "within_sla", "type": "number"},
        {"name": label,     "type": "number"},
    ]
    return build_response(columns, [[total, within, value]])


def sla_breaches(api, req) -> dict:
    """Tickets fuera de SLA (abiertos) — Table."""
    tickets = _get_all_tickets(api, req, extra_fields=[5, 17, 18])
    open_tickets = [
        t for t in tickets
        if t.get("status", t.get("12", 1)) not in [5, 6]
        and str(t.get("status", "")).lower() not in ["solved", "closed"]
    ]
    columns = [
        {"name": "id",       "type": "number"},
        {"name": "title",    "type": "string"},
        {"name": "priority", "type": "string"},
        {"name": "status",   "type": "string"},
        {"name": "created",  "type": "time"},
    ]
    rows = []
    for t in open_tickets[:req.max_results]:
        raw_p = t.get("priority", t.get("3", 3))
        raw_s = t.get("status",   t.get("12", 1))
        rows.append([
            t.get("id", t.get("2")),
            _str(t.get("name", t.get("1")), "—"),
            PRIORITY_NAMES.get(raw_p, str(raw_p)) if isinstance(raw_p, int) else _str(raw_p),
            STATUS_NAMES.get(raw_s,   str(raw_s)) if isinstance(raw_s, int) else _str(raw_s),
            t.get("date", t.get("15", "")),
        ])
    return build_response(columns, rows)


def resolution_time(api, req) -> dict:
    """Tiempo promedio de resolución — Stat / Histogram."""
    tickets = _get_all_tickets(api, req, extra_fields=[17, 18])
    unit      = req.resolution_options.unit            if req.resolution_options else "hours"
    show_p95  = req.resolution_options.show_percentile if req.resolution_options else False
    divisors  = {"minutes": 60, "hours": 3600, "days": 86400}
    divisor   = divisors.get(unit, 3600)

    durations = []
    for t in tickets:
        created = t.get("date",      t.get("15", ""))
        closed  = t.get("closedate", t.get("17", "")) or t.get("solvedate", t.get("18", ""))
        c, r    = _parse_dt_str(created), _parse_dt_str(closed)
        if c and r and r > c:
            durations.append((r - c).total_seconds() / divisor)

    cols = [{"name": f"avg_{unit}", "type": "number"}]
    if show_p95:
        cols.append({"name": f"p95_{unit}", "type": "number"})

    if not durations:
        return build_response(cols, [[None] + ([None] if show_p95 else [])])

    avg = round(sum(durations) / len(durations), 2)
    row = [avg]
    if show_p95:
        idx = max(0, int(len(sorted(durations)) * 0.95) - 1)
        row.append(round(sorted(durations)[idx], 2))

    return build_response(cols, [row])


def priority_breakdown(api, req) -> dict:
    """Distribución por prioridad — Pie chart."""
    tickets = _get_all_tickets(api, req)
    counts  = defaultdict(int)
    for t in tickets:
        raw = t.get("priority", t.get("3", 3))
        label = PRIORITY_NAMES.get(raw, str(raw)) if isinstance(raw, int) else _str(raw, "Unknown")
        counts[label] += 1
    columns = [{"name": "priority", "type": "string"}, {"name": "count", "type": "number"}]
    rows    = sorted([[k, v] for k, v in counts.items()], key=lambda x: x[1], reverse=True)
    return build_response(columns, rows)


def asset_count(api, req) -> dict:
    """Total de assets por tipo — Stat panel."""
    itemtype = req.asset_options.itemtype if req.asset_options else "Computer"
    try:
        items = api.item(itemtype).get_all_pages(page_size=200)
        count = len(items)
    except Exception:
        count = 0
    columns = [{"name": "itemtype", "type": "string"}, {"name": "count", "type": "number"}]
    return build_response(columns, [[itemtype, count]])


def asset_list(api, req) -> dict:
    """Inventario de assets — Table panel."""
    itemtype = req.asset_options.itemtype if req.asset_options else "Computer"
    try:
        items = api.item(itemtype).get_all_pages(page_size=min(req.max_results, 200))
    except Exception:
        items = []
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
            _str(i.get("name"),        "—"),
            _str(i.get("serial"),      "—"),
            _str(i.get("locations_id"),"—"),
            _str(i.get("states_id"),   "—"),
        ]
        for i in items[:req.max_results]
    ]
    return build_response(columns, rows)


def user_workload(api, req) -> dict:
    """Tickets abiertos por técnico — Bar chart."""
    tickets = _get_all_tickets(api, req, extra_fields=[5])
    open_tickets = [
        t for t in tickets
        if t.get("status", t.get("12", 1)) not in [5, 6]
        and str(t.get("status", "")).lower() not in ["solved", "closed"]
    ]
    counts = defaultdict(int)
    for t in open_tickets:
        tech = _str(t.get("users_id_assign", t.get("5")), "Unassigned")
        counts[tech] += 1
    columns = [{"name": "technician", "type": "string"}, {"name": "open_tickets", "type": "number"}]
    rows    = sorted([[k, v] for k, v in counts.items()], key=lambda x: x[1], reverse=True)
    return build_response(columns, rows)


def entity_summary(api, req) -> dict:
    """Métricas clave por entidad — Table."""
    try:
        entities = api.entity.get_all_pages()
    except Exception:
        entities = []

    columns = [
        {"name": "entity",        "type": "string"},
        {"name": "total_tickets", "type": "number"},
        {"name": "open_tickets",  "type": "number"},
    ]
    rows = []
    for entity in entities[:20]:
        eid  = entity.get("id")
        name = _str(entity.get("name"), str(eid))
        try:
            total_r = api.ticket.search(
                criteria=[{"field": 80, "searchtype": "equals", "value": eid}],
                forcedisplay=[1], range="0-0",
            )
            total = total_r.get("totalcount", 0)
            open_r = api.ticket.search(
                criteria=[
                    {"field": 80, "searchtype": "equals", "value": eid},
                    {"field": 12, "searchtype": "equals", "value": 1},
                ],
                forcedisplay=[1], range="0-0",
            )
            open_cnt = open_r.get("totalcount", 0)
        except Exception:
            total, open_cnt = None, None
        rows.append([name, total, open_cnt])

    return build_response(columns, rows)


def satisfaction(api, req) -> dict:
    """Rating promedio de encuestas — Gauge."""
    try:
        items   = api.item("TicketSatisfaction").get_all_pages(page_size=200)
        ratings = [float(i["satisfaction"]) for i in items if i.get("satisfaction") is not None]
        avg     = round(sum(ratings) / len(ratings), 2) if ratings else None
    except Exception as e:
        return build_response([{"name": "error", "type": "string"}], [[str(e)]])

    columns = [
        {"name": "avg_satisfaction", "type": "number"},
        {"name": "responses",        "type": "number"},
    ]
    return build_response(columns, [[avg, len(ratings)]])
