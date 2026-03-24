"""
Serviço de Inteligência Artificial — integração com Google Gemini.

Funcionalidades:
- Memória de conversa por sessão (número WhatsApp do usuário)
- TTL automático: sessões inativas por N minutos são limpas
- System prompt configurável via variável de ambiente
- Tratamento de erros com logging
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import google.generativeai as genai
from loguru import logger


class GeminiService:
    """
    Serviço de IA usando Google Gemini 2.0 Flash.

    Mantém uma sessão de chat separada por usuário (session_id),
    permitindo que a IA se lembre do contexto da conversa.
    """

    def __init__(
        self,
        api_key: str,
        system_prompt: str,
        model_name: str = "gemini-2.0-flash",
        ttl_minutes: int = 30,
    ) -> None:
        genai.configure(api_key=api_key)

        self._model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
        )

        # Armazena sessões de chat ativas: session_id → ChatSession
        self._sessions: dict[str, genai.ChatSession] = {}
        # Rastreia o horário do último acesso de cada sessão
        self._last_activity: dict[str, datetime] = {}
        self._ttl = timedelta(minutes=ttl_minutes)

        logger.info(
            f"GeminiService inicializado | modelo={model_name} | TTL={ttl_minutes}min"
        )

    async def get_response(self, session_id: str, message: str) -> str:
        """
        Envia uma mensagem para a IA e retorna a resposta em texto.

        Args:
            session_id: Identificador único do usuário (JID do WhatsApp).
            message: Texto enviado pelo usuário.

        Returns:
            Resposta gerada pela IA em texto plano.

        Raises:
            RuntimeError: Se a IA falhar após tentativa.
        """
        chat = self._get_or_create_session(session_id)
        logger.debug(f"Enviando para Gemini | session={session_id} | msg={message[:60]!r}")

        try:
            # Executa a chamada síncrona em uma thread separada
            # para não bloquear o loop de eventos assíncrono do FastAPI
            response = await asyncio.to_thread(chat.send_message, message)
            result = response.text
            logger.debug(f"Resposta Gemini | session={session_id} | chars={len(result)}")
            return result

        except Exception as exc:
            logger.error(f"Erro no Gemini | session={session_id} | erro={exc}")
            raise RuntimeError(
                "Não consegui processar sua pergunta no momento. Tente novamente em alguns segundos."
            ) from exc

    def clear_session(self, session_id: str) -> None:
        """Limpa o histórico de conversa de um usuário específico."""
        removed = bool(self._sessions.pop(session_id, None))
        self._last_activity.pop(session_id, None)
        if removed:
            logger.info(f"Sessão limpa | session={session_id}")

    def session_count(self) -> int:
        """Retorna o número de sessões ativas (útil para monitoramento)."""
        return len(self._sessions)

    # ──────────────────────────────────────────────────────────────
    # Métodos privados
    # ──────────────────────────────────────────────────────────────

    def _get_or_create_session(self, session_id: str) -> genai.ChatSession:
        """Recupera ou cria uma sessão de chat para o usuário."""
        self._cleanup_expired()

        if session_id not in self._sessions:
            self._sessions[session_id] = self._model.start_chat(history=[])
            logger.info(f"Nova sessão criada | session={session_id}")

        self._last_activity[session_id] = datetime.now()
        return self._sessions[session_id]

    def _cleanup_expired(self) -> None:
        """Remove sessões que estão inativas além do TTL configurado."""
        now = datetime.now()
        expired = [
            key
            for key, last in self._last_activity.items()
            if now - last > self._ttl
        ]
        for key in expired:
            self._sessions.pop(key, None)
            self._last_activity.pop(key, None)

        if expired:
            logger.debug(f"{len(expired)} sessão(ões) expirada(s) removida(s)")
