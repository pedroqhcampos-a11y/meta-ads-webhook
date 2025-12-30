from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import json
from datetime import datetime
import os

app = FastAPI()

# Store received data (in production, use a database)
received_data = {}

@app.post("/webhook/meta-ads/{client_id}")
async def receive_meta_ads_data(client_id: str, request: Request):
    """
    Recebe dados do Meta Ads via webhook do Make
    """
    try:
        data = await request.json()
        
        # Armazena os dados recebidos
        received_data[client_id] = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Log
        print(f"✓ Dados recebidos para cliente {client_id}")
        print(f"  Timestamp: {datetime.now().isoformat()}")
        
        return JSONResponse({
            "status": "success",
            "message": f"Dados recebidos para cliente {client_id}",
            "client_id": client_id
        })
    
    except Exception as e:
        print(f"✗ Erro ao receber dados: {str(e)}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=400)

@app.get("/webhook/status")
async def status():
    """
    Verifica status do servidor
    """
    return JSONResponse({
        "status": "online",
        "received_data_count": len(received_data),
        "clients": list(received_data.keys())
    })

@app.get("/webhook/data/{client_id}")
async def get_data(client_id: str):
    """
    Retorna últimos dados recebidos para um cliente
    """
    if client_id in received_data:
        return JSONResponse(received_data[client_id])
    return JSONResponse({"error": "No data found"}, status_code=404)

@app.get("/")
async def root():
    """
    Health check
    """
    return JSONResponse({
        "status": "online",
        "service": "Meta Ads Webhook Server",
        "version": "1.0"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("🚀 Iniciando servidor webhook...")
    print(f"📡 Servidor rodando em http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
