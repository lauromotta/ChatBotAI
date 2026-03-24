"""
Entry point da aplicação — ChatBotAI com FastAPI.

Endpoints:
  GET  /health    → verifica se o servidor está rodando
  POST /webhook   → recebe eventos da Evolution API

Fluxo de uma mensagem:
  Evolution API → POST /webhook → MessageHandler → GeminiService → WhatsAppService
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from loguru import logger

from app.config import settings
from app.handlers.command_handler import CommandHandler
from app.handlers.message_handler import MessageHandler
from app.models.message import WebhookPayload
from app.services.ai_service import GeminiService
from app.services.whatsapp_service import WhatsAppService

# ──────────────────────────────────────────────────────────────────────────
# Configuração do logging (substitui o logging padrão do Python)
# ──────────────────────────────────────────────────────────────────────────
logger.remove()  # Remove o handler padrão do loguru
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO",
    colorize=True,
)
logger.add(
    "logs/bot.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

# ──────────────────────────────────────────────────────────────────────────
# Serviços globais (inicializados no lifespan)
# ──────────────────────────────────────────────────────────────────────────
_message_handler: MessageHandler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    Inicializa os serviços na startup e os limpa no shutdown.
    """
    global _message_handler

    logger.info("🚀 Iniciando ChatBotAI...")
    logger.info(f"   Prefixo de comando: {settings.bot_command_prefix!r}")
    logger.info(f"   Instância Evolution: {settings.evolution_instance}")
    logger.info(f"   TTL de sessão: {settings.session_ttl_minutes} minutos")

    # Instancia os serviços na ordem correta (dependency injection manual)
    ai_service = GeminiService(
        api_key=settings.gemini_api_key,
        system_prompt=settings.bot_system_prompt,
        ttl_minutes=settings.session_ttl_minutes,
    )
    whatsapp_service = WhatsAppService(
        api_url=settings.evolution_api_url,
        api_key=settings.evolution_api_key,
        instance=settings.evolution_instance,
    )
    command_handler = CommandHandler(ai_service=ai_service)
    _message_handler = MessageHandler(
        whatsapp=whatsapp_service,
        commands=command_handler,
        prefix=settings.bot_command_prefix,
    )

    logger.info("✅ ChatBotAI pronto para receber mensagens!")
    yield  # Aplicação roda aqui

    logger.info("Encerrando ChatBotAI...")


# ──────────────────────────────────────────────────────────────────────────
# Aplicação FastAPI
# ──────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ChatBotAI",
    description="Bot para WhatsApp com IA (Gemini) via Evolution API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI: http://localhost:8000/docs
)


# ──────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────


@app.get("/health", tags=["Monitoramento"])
async def health():
    """Verifica se o servidor está operacional."""
    sessions = _message_handler._cmd._ai.session_count() if _message_handler else 0
    return {
        "status": "ok",
        "version": "2.0.0",
        "sessoes_ativas": sessions,
    }


@app.post("/webhook", tags=["Webhook"])
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Recebe eventos da Evolution API.

    Apenas o evento `messages.upsert` é processado.
    O processamento ocorre em background para responder
    imediatamente à Evolution API (evita timeout de webhook).
    """
    # ── Parse do JSON ────────────────────────────────────────────────────
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Corpo da requisição inválido (JSON esperado)")

    # ── Filtra eventos irrelevantes ──────────────────────────────────────
    event = body.get("event", "")
    if event != "messages.upsert":
        logger.debug(f"Evento ignorado: {event!r}")
        return {"status": "ignored", "event": event}

    # ── Valida o payload com Pydantic ────────────────────────────────────
    try:
        payload = WebhookPayload(**body)
    except Exception as exc:
        logger.warning(f"Payload inválido recebido: {exc}")
        # Retorna 200 para não fazer a Evolution API reenviar
        return {"status": "parse_error", "detail": str(exc)}

    # ── Processa em background (não bloqueia a resposta HTTP) ────────────
    if _message_handler:
        background_tasks.add_task(_message_handler.handle_incoming, payload)

    return {"status": "accepted"}
