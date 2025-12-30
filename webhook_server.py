#!/usr/bin/env python3.11
"""
Meta Ads Webhook Server - Integração completa
Recebe dados do Make, analisa com IA e envia para ClickUp automaticamente
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import json
import os
import subprocess
from meta_ads_analyzer import analyze_daily_metrics, analyze_weekly_metrics

app = FastAPI(title="Meta Ads Webhook")

# Armazena dados recebidos (em produção, usar banco de dados)
received_data = {}

# Mapeamento de clientes para task IDs do ClickUp
CLIENT_TASK_MAPPING = {
    "snob-motel": {
        "daily_task_id": "86ae5nt15",  # Otimização diária
        "weekly_task_id": "86ae5nt1d",  # Otimização semanal
        "account_name": "CA - Snob Motel"
    }
    # Adicionar mais clientes aqui conforme necessário
}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Meta Ads Webhook",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/webhook/status")
async def webhook_status():
    """Status do webhook e dados recebidos"""
    return {
        "status": "online",
        "received_data_count": len(received_data),
        "clients": list(received_data.keys())
    }


@app.get("/webhook/data/{client_slug}")
async def get_client_data(client_slug: str):
    """Retorna dados recebidos de um cliente específico"""
    if client_slug not in received_data:
        raise HTTPException(status_code=404, detail="Client data not found")
    
    return received_data[client_slug]


@app.post("/webhook/meta-ads/{client_slug}")
async def receive_meta_ads_data(client_slug: str, request: Request):
    """
    Recebe dados do Meta Ads via Make
    Analisa com IA e envia automaticamente para ClickUp
    """
    try:
        # Recebe dados
        data = await request.json()
        
        # Valida se o cliente está configurado
        if client_slug not in CLIENT_TASK_MAPPING:
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Client '{client_slug}' not configured",
                    "available_clients": list(CLIENT_TASK_MAPPING.keys())
                }
            )
        
        client_config = CLIENT_TASK_MAPPING[client_slug]
        
        # Armazena dados
        received_data[client_slug] = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Analisa com IA
        analysis_result = analyze_daily_metrics(data)
        
        # Envia para ClickUp
        task_id = client_config["daily_task_id"]
        comment_text = analysis_result["formatted_comment"]
        
        # Chama MCP CLI para enviar comentário
        result = send_clickup_comment(task_id, comment_text)
        
        if result["success"]:
            return {
                "status": "success",
                "message": "Data received, analyzed, and posted to ClickUp",
                "client": client_slug,
                "task_id": task_id,
                "comment_id": result.get("comment_id"),
                "analysis_summary": {
                    "metrics": analysis_result["metrics"],
                    "type": analysis_result["type"]
                }
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "partial_success",
                    "message": "Data received and analyzed, but failed to post to ClickUp",
                    "error": result.get("error")
                }
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "message": "Failed to process webhook data"
            }
        )


def send_clickup_comment(task_id: str, comment_text: str) -> dict:
    """
    Envia comentário para o ClickUp usando MCP CLI
    """
    try:
        # Escapa aspas no texto do comentário
        comment_escaped = comment_text.replace('"', '\\"').replace('\n', '\\n')
        
        # Monta comando MCP CLI
        cmd = [
            "manus-mcp-cli",
            "tool",
            "call",
            "clickup_create_task_comment",
            "--server",
            "clickup",
            "--input",
            json.dumps({
                "task_id": task_id,
                "comment_text": comment_text
            })
        ]
        
        # Executa comando
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Parse output para pegar comment_id
            try:
                # O output do MCP CLI geralmente tem o resultado em JSON
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines:
                    if line.startswith('{'):
                        response = json.loads(line)
                        if response.get("success"):
                            return {
                                "success": True,
                                "comment_id": response.get("comment_id")
                            }
            except:
                pass
            
            return {"success": True}
        else:
            return {
                "success": False,
                "error": result.stderr
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/webhook/meta-ads-weekly/{client_slug}")
async def receive_weekly_data(client_slug: str, request: Request):
    """
    Recebe dados semanais do Meta Ads
    Gera relatório semanal com roteiro de áudio
    """
    try:
        data_list = await request.json()
        
        if client_slug not in CLIENT_TASK_MAPPING:
            return JSONResponse(
                status_code=400,
                content={"error": f"Client '{client_slug}' not configured"}
            )
        
        client_config = CLIENT_TASK_MAPPING[client_slug]
        
        # Analisa dados semanais
        analysis_result = analyze_weekly_metrics(data_list)
        
        # Envia para ClickUp (tarefa semanal)
        task_id = client_config["weekly_task_id"]
        comment_text = analysis_result["formatted_comment"]
        
        result = send_clickup_comment(task_id, comment_text)
        
        if result["success"]:
            return {
                "status": "success",
                "message": "Weekly report generated and posted to ClickUp",
                "client": client_slug,
                "task_id": task_id,
                "comment_id": result.get("comment_id")
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Failed to post weekly report to ClickUp",
                    "error": result.get("error")
                }
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
