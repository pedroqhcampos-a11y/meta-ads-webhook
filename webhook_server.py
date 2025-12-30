#!/usr/bin/env python3.11
"""
Meta Ads Webhook Server - Otimizado e Blindado
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import os
import requests
import logging
from meta_ads_analyzer import analyze_daily_metrics, analyze_weekly_metrics

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Meta Ads Webhook")

# ClickUp API Configuration
CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN", "pk_112009602_D4JNOWDEPVWUTPEBHVPKILZPLAJC8QHZ")
CLICKUP_API_BASE = "https://api.clickup.com/api/v2"

# Mapeamento de clientes
CLIENT_TASK_MAPPING = {
    "snob-motel": {
        "daily_task_id": "86ae5nt15", 
        "weekly_task_id": "86ae5nt1d", 
        "account_name": "CA - Snob Motel"
    }
}

@app.get("/")
async def root():
    return {"status": "online", "service": "Meta Ads Webhook V2"}

@app.post("/webhook/meta-ads/{client_slug}")
async def receive_meta_ads_data(client_slug: str, request: Request):
    """
    Recebe dados, gera análise e envia para ClickUp.
    """
    try:
        logger.info(f"Recebendo webhook para: {client_slug}")
        
        # 1. Validação do Cliente
        if client_slug not in CLIENT_TASK_MAPPING:
            logger.warning(f"Cliente não encontrado: {client_slug}")
            return JSONResponse(status_code=400, content={"error": "Cliente não configurado"})
            
        client_config = CLIENT_TASK_MAPPING[client_slug]
        
        # 2. Recebimento dos Dados
        try:
            data = await request.json()
        except Exception:
            logger.error("Payload inválido recebido")
            return JSONResponse(status_code=400, content={"error": "JSON inválido"})

        # 3. Análise IA
        logger.info("Iniciando análise de IA...")
        analysis_result = analyze_daily_metrics(data)
        
        if not analysis_result.get("success"):
            logger.error(f"Falha na análise: {analysis_result.get('error')}")

        # 4. Envio para ClickUp
        task_id = client_config["daily_task_id"]
        comment_text = analysis_result.get("formatted_comment", "Erro ao gerar comentário.")
        
        logger.info(f"Enviando para ClickUp Task: {task_id}")
        clickup_result = send_clickup_comment_api(task_id, comment_text)
        
        # 5. Resposta para o Make (Correção do Loop)
        if clickup_result["success"]:
            logger.info("Sucesso total. Ciclo finalizado.")
            return {
                "status": "success",
                "message": "Processado e enviado ao ClickUp com sucesso",
                "client": client_slug,
                "comment_id": clickup_result.get("comment_id")
            }
        else:
            logger.error(f"Erro no ClickUp: {clickup_result.get('error')}")
            return JSONResponse(
                status_code=502,
                content={
                    "status": "error",
                    "step": "clickup_api",
                    "details": clickup_result.get("error")
                }
            )

    except Exception as e:
        logger.exception("Erro CRÍTICO não tratado no servidor:")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "message": "Internal Server Error"}
        )

def send_clickup_comment_api(task_id: str, comment_text: str) -> dict:
    try:
        url = f"{CLICKUP_API_BASE}/task/{task_id}/comment"
        headers = {
            "Authorization": CLICKUP_API_TOKEN,
            "Content-Type": "application/json"
        }
        payload = {
            "comment_text": comment_text,
            "notify_all": False
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            return {"success": True, "comment_id": response.json().get("id")}
        else:
            logger.error(f"ClickUp recusou: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        # AQUI ESTAVA O ERRO NO COPY-PASTE ANTERIOR
        logger.error(f"Erro de conexão com ClickUp: {e}")
        return {"success": False, "error": str(e)}

@app.post("/webhook/meta-ads-weekly/{client_slug}")
async def receive_weekly_data(client_slug: str, request: Request):
    return {"status": "ignored", "message": "Relatório semanal em manutenção"}
