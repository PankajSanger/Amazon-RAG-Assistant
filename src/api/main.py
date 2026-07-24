import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from src.api.routers import admin, products, reviews, scrape

#In Docker, docker-compose's env_file: injects .env values directly into the
#process environment before Python starts, so this is a no-op there. In local
#(non-Docker) dev, nothing else reliably runs before every router - e.g.
#src/rag/pipeline.py's load_environment() only loads .env lazily, on first use
#of the RAG pipeline - so routers that read env vars without going through
#that path (like admin.py's ADMIN_PASSWORD) would otherwise never see it.
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Amazon Product & Review Intelligence API")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape.router)
app.include_router(products.router)
app.include_router(reviews.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


#main.py -> api -> src -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", PROJECT_ROOT / "frontend" / "dist"))

#Registered last so /api/* above always takes priority. Only mounted when a
#build actually exists, so API-only local dev (no `npm run build` yet) is unaffected.
if FRONTEND_DIST.is_dir():

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
