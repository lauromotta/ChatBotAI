"""
Modelos Pydantic para o payload do webhook da Evolution API.

Estrutura do evento `messages.upsert`:
{
  "event": "messages.upsert",
  "instance": "meu-bot",
  "data": {
    "key": {
      "remoteJid": "5511999999999@s.whatsapp.net",  # ou ...@g.us para grupos
      "fromMe": false,
      "id": "ABCD1234",
      "participant": "..."  # apenas em grupos
    },
    "message": {
      "conversation": "Olá!",                      # texto simples
      "extendedTextMessage": {"text": "Resposta"}  # resposta/link preview
    },
    "messageType": "conversation",
    "pushName": "Carlos"
  }
}
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class MessageKey(BaseModel):
    """Identificadores únicos da mensagem no WhatsApp."""

    remoteJid: str
    fromMe: bool = False
    id: Optional[str] = None
    # Preenchido apenas em mensagens de grupo (JID do remetente real)
    participant: Optional[str] = None


class ExtendedTextMessage(BaseModel):
    """Mensagens com reply, link preview ou menção."""

    text: Optional[str] = None


class MessageContent(BaseModel):
    """Conteúdo da mensagem — pode ser de vários tipos."""

    # Texto puro
    conversation: Optional[str] = None
    # Texto com preview de link ou reply
    extendedTextMessage: Optional[ExtendedTextMessage] = None

    def extract_text(self) -> Optional[str]:
        """Extrai o texto em texto plano de qualquer tipo de mensagem."""
        if self.conversation:
            return self.conversation
        if self.extendedTextMessage and self.extendedTextMessage.text:
            return self.extendedTextMessage.text
        return None


class MessageData(BaseModel):
    """Dados principais do evento de mensagem."""

    key: MessageKey
    message: Optional[MessageContent] = None
    messageType: Optional[str] = None
    pushName: Optional[str] = None  # Nome de exibição do remetente


class WebhookPayload(BaseModel):
    """Payload completo recebido no webhook da Evolution API."""

    event: str
    instance: str
    data: MessageData

    # ──────────────────────────────────────────────────────
    # Métodos auxiliares para simplificar o acesso aos dados
    # ──────────────────────────────────────────────────────

    def get_text(self) -> Optional[str]:
        """Retorna o texto da mensagem, ou None se não houver texto."""
        if not self.data.message:
            return None
        return self.data.message.extract_text()

    def get_sender_jid(self) -> str:
        """
        Retorna o JID do remetente.
        Em grupos, usa `participant` (remetente real) para a sessão de IA,
        mas envia a resposta para `remoteJid` (o grupo).
        """
        return self.data.key.remoteJid

    def get_session_id(self) -> str:
        """
        Chave de sessão para a memória de conversa.
        Em grupos, usa o JID do participante para que cada membro
        tenha sua própria sessão de IA.
        """
        if self.data.key.participant:
            return self.data.key.participant
        return self.data.key.remoteJid

    def is_from_me(self) -> bool:
        """Retorna True se a mensagem foi enviada pelo próprio bot."""
        return self.data.key.fromMe

    def is_group(self) -> bool:
        """Retorna True se a mensagem foi enviada em um grupo."""
        return self.data.key.remoteJid.endswith("@g.us")

    def get_push_name(self) -> str:
        """Nome de exibição do remetente, ou 'usuário' se não disponível."""
        return self.data.pushName or "usuário"
