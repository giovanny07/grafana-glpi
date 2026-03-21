from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from glpi_client import get_api, build_response
import handlers

router = APIRouter()

class Filters(BaseModel):
    entity_id: Optional[int] = None
    status: list[int] = []
    priority: list[int] = []
    category_id: Optional[int] = None
    technician_id: Optional[int] = None
    group_id: Optional[int] = None
    ticket_type: Optional[int] = None

class TrendOptions(BaseModel):
    interval: str = "day"
    group_by: str = "none"

class SlaOptions(BaseModel):
    sla_id: Optional[int] = None
    show_percentage: bool = True

class ResolutionOptions(BaseModel):
    unit: str = "hours"
    show_percentile: bool = False

class AssetOptions(BaseModel):
    itemtype: str = "Computer"

class QueryRequest(BaseModel):
    query_type: str
    filters: Filters = Filters()
    group_by_entity: bool = False
    max_results: int = 100
    time_from: str
    time_to: str

    glpi_url: str
    app_token: str
    user_token: str = ""
    username: str = ""
    password: str = ""
    verify_ssl: bool = True

    trend_options: Optional[TrendOptions] = None
    sla_options: Optional[SlaOptions] = None
    resolution_options: Optional[ResolutionOptions] = None
    asset_options: Optional[AssetOptions] = None

HANDLER_MAP = {
    "ticket_summary":       handlers.ticket_summary,
    "ticket_trend":         handlers.ticket_trend,
    "ticket_list":          handlers.ticket_list,
    "ticket_by_category":   handlers.ticket_by_category,
    "ticket_by_technician": handlers.ticket_by_technician,
    "sla_compliance":       handlers.sla_compliance,
    "sla_breaches":         handlers.sla_breaches,
    "resolution_time":      handlers.resolution_time,
    "priority_breakdown":   handlers.priority_breakdown,
    "asset_count":          handlers.asset_count,
    "asset_list":           handlers.asset_list,
    "user_workload":        handlers.user_workload,
    "entity_summary":       handlers.entity_summary,
    "satisfaction":         handlers.satisfaction,
}

@router.post("/query")
def query(req: QueryRequest):
    handler = HANDLER_MAP.get(req.query_type)
    if not handler:
        return JSONResponse(status_code=400, content={"error": f"Unknown query_type: {req.query_type}"})

    try:
        api = get_api(req)
        result = handler(api, req)
        api.logout()
        return result

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
