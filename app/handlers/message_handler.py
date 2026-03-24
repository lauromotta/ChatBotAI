"""
Handler de mensagens recebidas.

Ponto central de processamento: recebe o payload do webhook,
aplica filtros, identifica o comando e despacha para o handler correto.
"""

from __future__ import annotations

from loguru import logger

from app.models.message import WebhookPayload
from app.services.whatsapp_service import WhatsAppService
from app.handlers.command_handler import CommandHandler

# Mensagem de erro genérica enviada ao usuário quando algo falha
ERROR_TEXT = (
    "⚠️ Ocorreu um erro ao processar sua mensagem. "
    "Tente novamente em alguns instantes."
)


class MessageHandler:
    """
    Roteador de mensagens recebidas via webhook.

    Responsabilidades:
    1. Filtrar mensagens que não devem ser processadas
    2. Extrair o texto e identificar o comando
    3. Chamar o handler correto
    4. Enviar a resposta via WhatsAppService
    """

    def __init__(
        self,
        whatsapp: WhatsAppService,
        commands: CommandHandler,
        prefix: str = "/bot",
    ) -> None:
        self._wa = whatsapp
        self._cmd = commands
        # Garante que o prefixo seja sempre minúsculo para comparação
        self._prefix = prefix.lower().strip()

    async def handle_incoming(self, payload: WebhookPayload) -> None:
        """
        Processa uma mensagem recebida do webhook.

        A função segue um padrão de "early return":
        retorna imediatamente se a mensagem não deve ser processada,
        evitando aninhamento excessivo de condições.

        Args:
            payload: Payload validado do webhook da Evolution API.
        """
        # ── Filtro 1: ignorar mensagens enviadas pelo próprio bot ────────────
        if payload.is_from_me():
            return

        # ── Filtro 2: ignorar mensagens sem texto ────────────────────────────
        text = payload.get_text()
        if not text or not text.strip():
            return

        text_clean = text.strip()
        text_lower = text_clean.lower()
        sender_jid = payload.get_sender_jid()
        session_id = payload.get_session_id()
        push_name = payload.get_push_name()

        logger.info(
            f"Mensagem recebida | de={push_name} ({sender_jid}) | "
            f"texto={text_clean[:60]!r} | grupo={payload.is_group()}"
        )

        # ── Filtro 3: ignorar mensagens sem prefixo de comando ───────────────
        is_bot_command = (
            text_lower.startswith(self._prefix + " ")
            or text_lower == self._prefix
        )
        is_help_command = text_lower == "/ajuda"
        is_clear_command = text_lower == "/limpar"

        if not (is_bot_command or is_help_command or is_clear_command):
            # Mensagem sem comando — ignora silenciosamente
            return

        # ── Processamento: envia indicador de digitação ──────────────────────
        await self._wa.send_typing(sender_jid)

        try:
            response = await self._route_command(
                text_clean=text_clean,
                text_lower=text_lower,
                session_id=session_id,
                is_bot_command=is_bot_command,
                is_help_command=is_help_command,
            )
        except Exception as exc:
            logger.error(
                f"Erro ao processar comando | session={session_id} | erro={exc}"
            )
            response = ERROR_TEXT

        # ── Envio da resposta ────────────────────────────────────────────────
        await self._wa.send_text(sender_jid, response)

    async def _route_command(
        self,
        text_clean: str,
        text_lower: str,
        session_id: str,
        is_bot_command: bool,
        is_help_command: bool,
    ) -> str:
        """Encaminha a mensagem para o handler do comando correto."""
        if is_bot_command:
            # Extrai a query removendo o prefixo do início
            query = text_clean[len(self._prefix) :].strip()
            return await self._cmd.handle_bot(query, session_id)

        if is_help_command:
            return self._cmd.handle_help()

        # /limpar
        return self._cmd.handle_clear(session_id)
