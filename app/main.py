"""
Ponto de entrada da aplicação FastAPI — Agente de Mídia IA com Chat Interface.

Para rodar localmente:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Acesse a interface de chat em: http://localhost:8000/
Docs interativas disponíveis em: http://localhost:8000/docs
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inicialização do FastAPI
# ---------------------------------------------------------------------------

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API de um Agente de IA Autônomo focado em análise de dados de mídia "
        "com interface de chat web (STT & TTS integrados). "
        "Utiliza Claude (Anthropic) para raciocínio e BigQuery para dados."
    ),
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Middlewares
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restringir em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Roteamento da API
# ---------------------------------------------------------------------------

app.include_router(router)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Health"], summary="Verifica se a API está online")
async def health_check() -> dict[str, str]:
    """Endpoint de saúde para monitoramento e probes de infraestrutura."""
    return {"status": "ok", "version": settings.app_version}


# ---------------------------------------------------------------------------
# Servir arquivos estáticos (Frontend de Chat)
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
    logger.info(f"✅ Arquivos estáticos montados em: {STATIC_DIR}")
else:
    logger.warning(f"⚠️ Diretório de arquivos estáticos não encontrado: {STATIC_DIR}")
