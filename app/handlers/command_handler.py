"""
Handler de comandos do bot.

Centraliza a lógica de cada comando disponível:
  /bot [pergunta]  → resposta da IA (Gemini)
  /ajuda           → lista de comandos
  /limpar          → limpa histórico da conversa
"""

from __future__ import annotations

from app.services.ai_service import GeminiService

# ──────────────────────────────────────────────────────────────────────────
# Mensagens estáticas do bot
# ──────────────────────────────────────────────────────────────────────────

HELP_TEXT = """🤖 *Comandos disponíveis:*

*/bot [pergunta]* — Faz uma pergunta para a IA
*/ajuda* — Mostra esta mensagem de ajuda
*/limpar* — Limpa o histórico da conversa

*Exemplos:*
/bot Qual é a capital do Brasil?
/bot Explique o que é uma API REST
/bot Me dê uma receita de bolo de cenoura""".strip()

NO_QUERY_TEXT = (
    "❓ Por favor, envie uma pergunta após o comando.\n\n"
    "*Exemplo:* /bot Qual é a capital do Brasil?"
)

CLEAR_SUCCESS_TEXT = "🗑️ Histórico de conversa limpo! Podemos começar do zero. 😊"


class CommandHandler:
    """
    Processa cada comando disponível do bot e retorna a resposta em texto.

    Recebe os serviços como dependência (injeção) para facilitar testes.
    """

    def __init__(self, ai_service: GeminiService) -> None:
        self._ai = ai_service

    async def handle_bot(self, query: str, session_id: str) -> str:
        """
        Processa o comando /bot: envia a consulta para o Gemini e retorna a resposta.

        Args:
            query: Texto após o prefixo do comando (já sanitizado).
            session_id: Identificador da sessão do usuário.

        Returns:
            Resposta da IA ou mensagem de erro amigável.
        """
        if not query.strip():
            return NO_QUERY_TEXT

        try:
            return await self._ai.get_response(session_id, query)
        except RuntimeError as exc:
            # RuntimeError já tem mensagem amigável do ai_service
            return f"⚠️ {exc}"

    def handle_help(self) -> str:
        """Retorna o texto de ajuda com a lista de comandos."""
        return HELP_TEXT

    def handle_clear(self, session_id: str) -> str:
        """Limpa o histórico de conversa do usuário e confirma a ação."""
        self._ai.clear_session(session_id)
        return CLEAR_SUCCESS_TEXT
