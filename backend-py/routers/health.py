from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from glpi_utils import GlpiAPI
from glpi_utils import GlpiAuthError, GlpiAPIError

router = APIRouter()

class HealthRequest(BaseModel):
    glpi_url: str
    app_token: str
    user_token: str = ""
    username: str = ""
    password: str = ""
    verify_ssl: bool = True

@router.post("/health")
def health_check(req: HealthRequest):
    try:
        api = GlpiAPI(
            url=req.glpi_url,
            app_token=req.app_token,
            verify_ssl=req.verify_ssl,
        )
        if req.user_token:
            api.login(user_token=req.user_token)
        else:
            api.login(username=req.username, password=req.password)

        version = str(api.version)
        api.logout()

        return {"status": "ok", "glpi_version": version}

    except GlpiAuthError as e:
        return JSONResponse(status_code=401, content={"error": f"Auth failed: {e}"})
    except GlpiAPIError as e:
        return JSONResponse(status_code=502, content={"error": f"GLPI error: {e}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
