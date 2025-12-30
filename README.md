# Meta Ads Webhook Server

Servidor webhook para receber dados do Meta Ads via Make e enviar para análise com IA.

## Arquivos inclusos

- `webhook_server.py` - Servidor FastAPI principal
- `requirements.txt` - Dependências Python
- `Procfile` - Configuração para Render/Heroku
- `runtime.txt` - Versão Python

## Como fazer o deploy no Render.com

1. Acesse https://render.com
2. Crie uma conta (grátis)
3. Clique em **"New +"** → **"Web Service"**
4. Escolha **"Public Git Repository"**
5. Cole este repositório (ou faça upload dos arquivos)
6. Configure:
   - **Name**: `meta-ads-webhook`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn webhook_server:app --host 0.0.0.0 --port $PORT`
7. Clique em **"Create Web Service"**
8. Aguarde o deploy (2-3 minutos)
9. Você receberá uma URL como: `https://meta-ads-webhook.onrender.com`

## Endpoints

- `POST /webhook/meta-ads/{client_id}` - Recebe dados do Meta Ads
- `GET /webhook/status` - Status do servidor
- `GET /webhook/data/{client_id}` - Retorna últimos dados recebidos
- `GET /` - Health check

## Uso no Make

Após fazer o deploy, use esta URL no Make:

```
https://meta-ads-webhook.onrender.com/webhook/meta-ads/snob-motel
```

Substitua `snob-motel` pelo ID do seu cliente.

## Suporte

Para dúvidas, entre em contato.
