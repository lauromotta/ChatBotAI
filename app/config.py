"""
Configuração centralizada da aplicação.

Todas as variáveis de ambiente são carregadas aqui via python-dotenv.
O objeto `settings` é um singleton importado pelos demais módulos.
"""

import os
from dotenv import load_dotenv

# Carrega o arquivo .env se existir
load_dotenv()


class Settings:
    """
    Configurações da aplicação carregadas das variáveis de ambiente.
    Falha explicitamente na inicialização se variáveis obrigatórias estiverem ausentes.
    """

    def __init__(self) -> None:
        # ── IA (Gemini) ──────────────────────────────────────────────
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

        # ── Evolution API (WhatsApp) ─────────────────────────────────
        self.evolution_api_url: str = os.getenv(
            "EVOLUTION_API_URL", "http://localhost:8080"
        )
        self.evolution_api_key: str = os.getenv("EVOLUTION_API_KEY", "")
        self.evolution_instance: str = os.getenv("EVOLUTION_INSTANCE", "meu-bot")

        # ── Comportamento do Bot ─────────────────────────────────────
        self.bot_command_prefix: str = os.getenv(
            "BOT_COMMAND_PREFIX", "/bot"
        ).lower().strip()

        self.bot_system_prompt: str = os.getenv(
            "BOT_SYSTEM_PROMPT",
            (
                "Você é um assistente inteligente chamado BotAI. "
                "Responda sempre em português brasileiro, de forma clara, "
                "objetiva e amigável. Seja conciso (máximo 3 parágrafos). "
                "Se não souber a resposta, diga honestamente que não sabe."
            ),
        )

        self.session_ttl_minutes: int = int(
            os.getenv("SESSION_TTL_MINUTES", "30")
        )

        # Valida presença das variáveis obrigatórias
        self._validate()

    def _validate(self) -> None:
        """Valida variáveis obrigatórias e falha cedo com mensagem clara."""
        missing: list[str] = []

        if not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")
        if not self.evolution_api_key:
            missing.append("EVOLUTION_API_KEY")

        if missing:
            raise ValueError(
                f"❌ Variáveis de ambiente obrigatórias ausentes: {', '.join(missing)}\n"
                "💡 Copie o arquivo .env.example para .env e preencha os valores."
            )


# Singleton — importado pelos demais módulos
settings = Settings()
