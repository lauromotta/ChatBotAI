"""
Testes para o GeminiService.

Os testes usam mocks do google.generativeai para não consumir
quota real da API e garantir execução rápida e offline.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ──────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_genai():
    """Mock completo do módulo google.generativeai."""
    with patch("app.services.ai_service.genai") as mock:
        # Simula o objeto ChatSession
        mock_chat = MagicMock()
        mock_chat.send_message.return_value = MagicMock(text="Resposta da IA")
        # Faz start_chat retornar sempre o mesmo mock de chat
        mock.GenerativeModel.return_value.start_chat.return_value = mock_chat
        yield mock, mock_chat


@pytest.fixture
def ai_service(mock_genai):
    """Instância do GeminiService com Gemini completamente mockado."""
    from app.services.ai_service import GeminiService

    return GeminiService(
        api_key="fake-api-key-for-tests",
        system_prompt="Você é um assistente de testes.",
        ttl_minutes=30,
    )


# ──────────────────────────────────────────────────────────────────────────
# Testes
# ──────────────────────────────────────────────────────────────────────────


class TestGeminiService:
    def test_cria_servico_corretamente(self, ai_service, mock_genai):
        """Deve configurar o genai com a api_key fornecida."""
        mock_module, _ = mock_genai
        mock_module.configure.assert_called_once_with(api_key="fake-api-key-for-tests")

    @pytest.mark.asyncio
    async def test_get_response_retorna_texto(self, ai_service, mock_genai):
        """Deve retornar o texto da resposta do Gemini."""
        resultado = await ai_service.get_response("user123", "Olá!")
        assert resultado == "Resposta da IA"

    @pytest.mark.asyncio
    async def test_get_response_cria_nova_sessao(self, ai_service, mock_genai):
        """Deve criar uma nova sessão para um usuário nunca visto antes."""
        assert ai_service.session_count() == 0
        await ai_service.get_response("user_novo", "Primeira mensagem")
        assert ai_service.session_count() == 1

    @pytest.mark.asyncio
    async def test_get_response_reutiliza_sessao_existente(self, ai_service, mock_genai):
        """Dois envios do mesmo usuário devem usar a mesma sessão."""
        await ai_service.get_response("user_abc", "Mensagem 1")
        await ai_service.get_response("user_abc", "Mensagem 2")
        # Ainda uma única sessão para o mesmo usuário
        assert ai_service.session_count() == 1

    @pytest.mark.asyncio
    async def test_sessoes_diferentes_por_usuario(self, ai_service, mock_genai):
        """Usuários distintos devem ter sessões separadas."""
        await ai_service.get_response("user_A", "Olá")
        await ai_service.get_response("user_B", "Oi")
        assert ai_service.session_count() == 2

    def test_clear_session_remove_historico(self, ai_service, mock_genai):
        """Limpar sessão deve remover o histórico do usuário."""
        # Cria sessão manualmente no dict interno
        ai_service._sessions["user_z"] = MagicMock()
        ai_service._last_activity["user_z"] = MagicMock()
        assert ai_service.session_count() == 1

        ai_service.clear_session("user_z")
        assert ai_service.session_count() == 0

    def test_clear_session_inexistente_nao_falha(self, ai_service, mock_genai):
        """Limpar uma sessão que não existe não deve lançar erro."""
        ai_service.clear_session("sessao_que_nao_existe")  # Não deve levantar exceção

    @pytest.mark.asyncio
    async def test_get_response_falha_levanta_runtime_error(self, ai_service, mock_genai):
        """Quando o Gemini falha, deve lançar RuntimeError com mensagem amigável."""
        _, mock_chat = mock_genai
        mock_chat.send_message.side_effect = Exception("API offline")

        with pytest.raises(RuntimeError):
            await ai_service.get_response("user_err", "Teste")
