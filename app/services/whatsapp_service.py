"""
Serviço de comunicação com o WhatsApp via Evolution API.

Evolution API — documentação: https://doc.evolution-api.com
Todas as chamadas são assíncronas usando httpx.AsyncClient.
"""

from __future__ import annotations

import httpx
from loguru import logger


class WhatsAppService:
    """
    Cliente HTTP para a Evolution API (REST).

    Encapsula todas as chamadas à Evolution API,
    centralizando autenticação e tratamento de erros HTTP.
    """

    # Timeout padrão para envio de mensagens (segundos)
    _DEFAULT_TIMEOUT = 30
    # Timeout para indicador de digitação (pode falhar silenciosamente)
    _TYPING_TIMEOUT = 10

    def __init__(self, api_url: str, api_key: str, instance: str) -> None:
        self._base_url = api_url.rstrip("/")
        self._instance = instance
        self._headers = {
            "apikey": api_key,
            "Content-Type": "application/json",
        }
        logger.info(
            f"WhatsAppService inicializado | url={self._base_url} | instância={instance}"
        )

    async def send_text(self, to: str, text: str) -> bool:
        """
        Envia uma mensagem de texto para um número ou grupo.

        Args:
            to: JID do destinatário (ex: '5511999999999@s.whatsapp.net').
            text: Texto a ser enviado.

        Returns:
            True se o envio foi bem-sucedido, False caso contrário.
        """
        url = f"{self._base_url}/message/sendText/{self._instance}"
        payload = {"number": to, "text": text}

        try:
            async with httpx.AsyncClient(timeout=self._DEFAULT_TIMEOUT) as client:
                response = await client.post(url, json=payload, headers=self._headers)
                response.raise_for_status()
                logger.info(f"Mensagem enviada para {to} | chars={len(text)}")
                return True

        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Erro HTTP ao enviar mensagem para {to} | "
                f"status={exc.response.status_code} | detalhe={exc.response.text[:200]}"
            )
            return False

        except httpx.RequestError as exc:
            logger.error(
                f"Erro de conexão com a Evolution API ao enviar para {to} | erro={exc}"
            )
            return False

    async def send_typing(self, to: str, duration_ms: int = 2000) -> None:
        """
        Envia o indicador "digitando..." antes de responder.

        Falha silenciosamente pois é uma funcionalidade secundária.

        Args:
            to: JID do destinatário.
            duration_ms: Duração do indicador em milissegundos.
        """
        url = f"{self._base_url}/chat/sendPresence/{self._instance}"
        payload = {
            "number": to,
            "presence": "composing",
            "delay": duration_ms,
        }

        try:
            async with httpx.AsyncClient(timeout=self._TYPING_TIMEOUT) as client:
                await client.post(url, json=payload, headers=self._headers)
                logger.debug(f"Indicador 'digitando' enviado para {to}")

        except Exception as exc:
            # Não falha o fluxo principal se o indicador não funcionar
            logger.warning(f"Não foi possível enviar indicador de digitação | erro={exc}")
