from glpi_utils import GlpiAPI

def get_api(req) -> GlpiAPI:
    """Crea y autentica un GlpiAPI desde los parámetros del request."""
    api = GlpiAPI(
        url=req.glpi_url,
        app_token=req.app_token,
        verify_ssl=req.verify_ssl,
    )
    if req.user_token:
        api.login(user_token=req.user_token)
    else:
        api.login(username=req.username, password=req.password)
    return api

def build_response(columns: list[dict], rows: list[list]) -> dict:
    return {"columns": columns, "rows": rows}
