"""
Testes para o MessageHandler e CommandHandler.

Usa mocks de WhatsAppService e GeminiService para testar
apenas a lógica de roteamento e filtragem de mensagens.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.handlers.command_handler import (
    CLEAR_SUCCESS_TEXT,
    HELP_TEXT,
    NO_QUERY_TEXT,
    CommandHandler,
)
from app.handlers.message_handler import MessageHandler
from app.models.message import MessageContent, MessageData, MessageKey, WebhookPayload


# ──────────────────────────────────────────────────────────────────────────
# Helpers para construir payloads de teste
# ──────────────────────────────────────────────────────────────────────────


def make_payload(text: str, from_me: bool = False, jid: str = "5511999999999@s.whatsapp.net") -> WebhookPayload:
    """Cria um WebhookPayload de texto simples para testes."""
    return WebhookPayload(
        event="messages.upsert",
        instance="test-bot",
        data=MessageData(
            key=MessageKey(remoteJid=jid, fromMe=from_me),
            message=MessageContent(conversation=text),
            messageType="conversation",
            pushName="Usuário Teste",
        ),
    )


def make_empty_payload() -> WebhookPayload:
    """Cria um payload sem mensagem de texto."""
    return WebhookPayload(
        event="messages.upsert",
        instance="test-bot",
        data=MessageData(
            key=MessageKey(remoteJid="5511999999999@s.whatsapp.net", fromMe=False),
            message=None,
            pushName="Teste",
        ),
    )


# ──────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_whatsapp():
    """Mock do WhatsAppService com métodos assíncronos."""
    wa = MagicMock()
    wa.send_text = AsyncMock(return_value=True)
    wa.send_typing = AsyncMock(return_value=None)
    return wa


@pytest.fixture
def mock_ai():
    """Mock do GeminiService."""
    ai = MagicMock()
    ai.get_response = AsyncMock(return_value="Resposta da IA mockada")
    ai.clear_session = MagicMock()
    ai.session_count = MagicMock(return_value=0)
    return ai


@pytest.fixture
def command_handler(mock_ai):
    return CommandHandler(ai_service=mock_ai)


@pytest.fixture
def message_handler(mock_whatsapp, command_handler):
    return MessageHandler(
        whatsapp=mock_whatsapp,
        commands=command_handler,
        prefix="/bot",
    )


# ──────────────────────────────────────────────────────────────────────────
# Testes do WebhookPayload (modelo)
# ──────────────────────────────────────────────────────────────────────────


class TestWebhookPayload:
    def test_extract_text_de_conversation(self):
        payload = make_payload("/bot Olá!")
        assert payload.get_text() == "/bot Olá!"

    def test_is_from_me_true(self):
        payload = make_payload("texto", from_me=True)
        assert payload.is_from_me() is True

    def test_is_from_me_false(self):
        payload = make_payload("texto", from_me=False)
        assert payload.is_from_me() is False

    def test_is_group_false_para_individual(self):
        payload = make_payload("texto", jid="5511999999999@s.whatsapp.net")
        assert payload.is_group() is False

    def test_is_group_true_para_grupo(self):
        payload = make_payload("texto", jid="120363XXXXXXXX@g.us")
        assert payload.is_group() is True

    def test_get_text_none_quando_sem_mensagem(self):
        payload = make_empty_payload()
        assert payload.get_text() is None


# ──────────────────────────────────────────────────────────────────────────
# Testes do CommandHandler
# ──────────────────────────────────────────────────────────────────────────


class TestCommandHandler:
    @pytest.mark.asyncio
    async def test_handle_bot_chama_ai_e_retorna_resposta(self, command_handler, mock_ai):
        resultado = await command_handler.handle_bot("Qual a capital?", "user_1")
        mock_ai.get_response.assert_called_once_with("user_1", "Qual a capital?")
        assert resultado == "Resposta da IA mockada"

    @pytest.mark.asyncio
    async def test_handle_bot_sem_query_retorna_instrucao(self, command_handler, mock_ai):
        resultado = await command_handler.handle_bot("", "user_1")
        assert resultado == NO_QUERY_TEXT
        mock_ai.get_response.assert_not_called()

    def test_handle_help_retorna_texto_de_ajuda(self, command_handler):
        assert command_handler.handle_help() == HELP_TEXT

    def test_handle_clear_limpa_sessao(self, command_handler, mock_ai):
        resultado = command_handler.handle_clear("user_x")
        mock_ai.clear_session.assert_called_once_with("user_x")
        assert resultado == CLEAR_SUCCESS_TEXT


# ──────────────────────────────────────────────────────────────────────────
# Testes do MessageHandler (roteamento e filtros)
# ──────────────────────────────────────────────────────────────────────────


class TestMessageHandler:
    @pytest.mark.asyncio
    async def test_ignora_mensagens_do_proprio_bot(self, message_handler, mock_whatsapp):
        payload = make_payload("/bot teste", from_me=True)
        await message_handler.handle_incoming(payload)
        mock_whatsapp.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignora_mensagens_sem_texto(self, message_handler, mock_whatsapp):
        payload = make_empty_payload()
        await message_handler.handle_incoming(payload)
        mock_whatsapp.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignora_mensagens_sem_prefixo(self, message_handler, mock_whatsapp):
        payload = make_payload("Olá, tudo bem?")
        await message_handler.handle_incoming(payload)
        mock_whatsapp.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_processa_comando_bot(self, message_handler, mock_whatsapp, mock_ai):
        payload = make_payload("/bot Qual a capital do Brasil?")
        await message_handler.handle_incoming(payload)
        mock_ai.get_response.assert_called_once()
        mock_whatsapp.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_processa_comando_ajuda(self, message_handler, mock_whatsapp, mock_ai):
        payload = make_payload("/ajuda")
        await message_handler.handle_incoming(payload)
        mock_whatsapp.send_text.assert_called_once_with(
            "5511999999999@s.whatsapp.net", HELP_TEXT
        )
        mock_ai.get_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_processa_comando_limpar(self, message_handler, mock_whatsapp, mock_ai):
        payload = make_payload("/limpar")
        await message_handler.handle_incoming(payload)
        mock_ai.clear_session.assert_called_once()
        mock_whatsapp.send_text.assert_called_once_with(
            "5511999999999@s.whatsapp.net", CLEAR_SUCCESS_TEXT
        )

    @pytest.mark.asyncio
    async def test_envia_indicador_de_digitacao_antes_de_responder(
        self, message_handler, mock_whatsapp
    ):
        payload = make_payload("/bot teste")
        await message_handler.handle_incoming(payload)
        mock_whatsapp.send_typing.assert_called_once()

    @pytest.mark.asyncio
    async def test_envia_erro_amigavel_quando_ai_falha(
        self, message_handler, mock_whatsapp, mock_ai
    ):
        mock_ai.get_response.side_effect = RuntimeError("Gemini offline")
        payload = make_payload("/bot Teste de falha")
        await message_handler.handle_incoming(payload)
        # Deve enviar mensagem de erro ao usuário, não travar
        mock_whatsapp.send_text.assert_called_once()
        call_args = mock_whatsapp.send_text.call_args[0]
        assert "Gemini offline" in call_args[1] or "erro" in call_args[1].lower()
