#!/usr/bin/env python3.11
"""
Meta Ads Webhook Server - Diário e Semanal (Ativos)
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

# Mapeamento de clientes e IDs das tarefas
CLIENT_TASK_MAPPING = {
    "snob-motel": {
        "daily_task_id": "86ae5nt15", 
        "weekly_task_id": "86ae5nt1d",
        "account_name": "CA - Snob Motel"
    },
    "maria-cristina": {
        "daily_task_id": "86ae6dudq", # ID que você me passou
        "weekly_task_id": "86ae6dudf", # ID que você me passou
        "account_name": "CA - Dra. Maria Cristina Bordoni"
    }
}

@app.get("/")
async def root():
    return {"status": "online", "service": "Meta Ads Webhook V3"}

# ==========================================
# ROTA DIÁRIA
# ==========================================
@app.post("/webhook/meta-ads/{client_slug}")
async def receive_meta_ads_data(client_slug: str, request: Request):
    try:
        logger.info(f"Recebendo DIÁRIO para: {client_slug}")
        
        if client_slug not in CLIENT_TASK_MAPPING:
            return JSONResponse(status_code=400, content={"error": "Cliente não configurado"})
            
        client_config = CLIENT_TASK_MAPPING[client_slug]
        
        try:
            data = await request.json()
        except Exception:
            return JSONResponse(status_code=400, content={"error": "JSON inválido"})

        # Análise Diária
        analysis_result = analyze_daily_metrics(data)
        
        # Envio para ClickUp (Task Diária)
        task_id = client_config["daily_task_id"]
        comment_text = analysis_result.get("formatted_comment", "Erro ao gerar comentário.")
        
        clickup_result = send_clickup_comment_api(task_id, comment_text)
        
        if clickup_result["success"]:
            return {"status": "success", "message": "Relatório Diário enviado"}
        else:
            return JSONResponse(status_code=502, content={"error": clickup_result.get("error")})

    except Exception as e:
        logger.exception("Erro Crítico Diário:")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ==========================================
# ROTA SEMANAL (AGORA ATIVADA)
# ==========================================
@app.post("/webhook/meta-ads-weekly/{client_slug}")
async def receive_weekly_data(client_slug: str, request: Request):
    """
    Recebe lista de campanhas, gera relatório semanal e envia para a task específica.
    """
    try:
        logger.info(f"Recebendo SEMANAL para: {client_slug}")
        
        if client_slug not in CLIENT_TASK_MAPPING:
            return JSONResponse(status_code=400, content={"error": "Cliente não configurado"})
            
        client_config = CLIENT_TASK_MAPPING[client_slug]
        
        try:
            data_list = await request.json()
            # Garante que seja uma lista (Array do Make)
            if not isinstance(data_list, list):
                # Se veio um item só sem lista, transforma em lista
                data_list = [data_list]
        except Exception:
            return JSONResponse(status_code=400, content={"error": "JSON inválido (esperado Array)"})

        # Análise Semanal (Chama a função nova focada no cliente)
        logger.info("Processando IA Semanal...")
        analysis_result = analyze_weekly_metrics(data_list)
        
        # Envio para ClickUp (Task SEMANAL)
        task_id = client_config["weekly_task_id"] # <--- Pega o ID 86ae5nt1d
        comment_text = analysis_result.get("formatted_comment", "Erro ao gerar relatório semanal.")
        
        logger.info(f"Enviando para ClickUp Task ID: {task_id}")
        clickup_result = send_clickup_comment_api(task_id, comment_text)
        
        if clickup_result["success"]:
            return {"status": "success", "message": "Relatório Semanal enviado"}
        else:
            logger.error(f"Erro ClickUp Semanal: {clickup_result.get('error')}")
            return JSONResponse(status_code=502, content={"error": clickup_result.get("error")})

    except Exception as e:
        logger.exception("Erro Crítico Semanal:")
        return JSONResponse(status_code=500, content={"error": str(e)})


# Função Auxiliar de Envio
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
            return {"success": False, "error": response.text}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
