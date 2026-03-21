from fastapi import FastAPI
from routers import query, health

app = FastAPI(title="GLPI Grafana Backend", version="1.0.0")

app.include_router(health.router)
app.include_router(query.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
