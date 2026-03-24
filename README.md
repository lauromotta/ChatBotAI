# ChatBotAI 🤖

Bot para WhatsApp com Inteligência Artificial (Google Gemini) integrado via **Evolution API**.

## Stack Tecnológica

| Componente | Tecnologia |
|-----------|-----------|
| WhatsApp | [Evolution API](https://github.com/EvolutionAPI/evolution-api) (open-source, gratuito) |
| Inteligência Artificial | Google Gemini 2.0 Flash (tier gratuito) |
| Servidor Web | FastAPI + Uvicorn |
| Linguagem | Python 3.11+ |
| Deploy | Docker Compose |

---

## Comandos disponíveis

| Comando | Descrição |
|---------|-----------|
| `/bot [pergunta]` | Faz uma pergunta para a IA |
| `/ajuda` | Lista os comandos disponíveis |
| `/limpar` | Limpa o histórico da conversa |

---

## Configuração (Passo a Passo)

### 1. Pré-requisitos

- [Python 3.11+](https://python.org)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para a Evolution API)
- Chave gratuita do Gemini → [aistudio.google.com](https://aistudio.google.com)

### 2. Instalar dependências

```powershell
cd f:\teste-ia\whatsapp\ChatBotAI

# Criar ambiente virtual (recomendado)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Instalar pacotes
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

```powershell
# Copiar o template
copy .env.example .env

# Editar o arquivo .env com suas chaves
notepad .env
```

Variáveis obrigatórias no `.env`:
```env
GEMINI_API_KEY=sua_chave_do_gemini_aqui
EVOLUTION_API_KEY=uma_senha_segura_para_a_evolution_api
```

### 4. Subir com Docker Compose (Recomendado)

```powershell
# Sobe a Evolution API e o bot juntos
docker compose up -d

# Ver logs em tempo real
docker compose logs -f chatbot
```

### 5. Configurar o WhatsApp na Evolution API

1. Acesse o painel: **http://localhost:8080/manager**
2. Faça login com a chave definida em `EVOLUTION_API_KEY`
3. Crie uma nova instância com o nome `meu-bot`
4. Escaneie o QR Code com seu WhatsApp
5. Vá em **Webhook** e configure:
   - URL: `http://chatbot:8000/webhook` (dentro do Docker) ou `http://localhost:8000/webhook` (local)
   - Evento habilitado: `messages.upsert`

---

## Rodando Localmente (Desenvolvimento)

```powershell
# Ativar ambiente virtual
.venv\Scripts\Activate.ps1

# Iniciar o servidor de desenvolvimento
uvicorn app.main:app --reload --port 8000
```

O servidor estará disponível em:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Simular uma mensagem (para testar sem WhatsApp)

```powershell
$body = '{"event":"messages.upsert","instance":"meu-bot","data":{"key":{"remoteJid":"5511999999999@s.whatsapp.net","fromMe":false},"message":{"conversation":"/bot Qual a capital do Brasil?"},"messageType":"conversation","pushName":"Teste"}}'

Invoke-WebRequest -Uri http://localhost:8000/webhook -Method POST -ContentType "application/json" -Body $body
```

---

## Testes

```powershell
# Rodar todos os testes
pytest tests/ -v

# Com relatório de cobertura
pytest tests/ -v --tb=short
```

---

## Personalizar o Bot

Edite o `BOT_SYSTEM_PROMPT` no arquivo `.env` para mudar a personalidade e o comportamento:

```env
BOT_SYSTEM_PROMPT=Você é a Assistente Virtual da Loja XYZ. Responda sobre nossos produtos, preços e horários. Seja sempre simpática e use emojis com moderação.
```

---

## Arquitetura

```
ChatBotAI/
├── app/
│   ├── main.py              # FastAPI — entry point
│   ├── config.py            # Configurações centralizadas
│   ├── models/
│   │   └── message.py       # Modelos Pydantic (webhook)
│   ├── services/
│   │   ├── ai_service.py    # Google Gemini (IA + memória)
│   │   └── whatsapp_service.py  # Evolution API (cliente REST)
│   └── handlers/
│       ├── message_handler.py   # Roteador de mensagens
│       └── command_handler.py   # Lógica dos comandos
└── tests/
    ├── test_ai_service.py
    └── test_message_handler.py
```
