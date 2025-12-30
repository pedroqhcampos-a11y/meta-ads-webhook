#!/usr/bin/env python3.11
"""
Meta Ads Analyzer - Relatório Diário (Otimizado)
"""

import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

# Configuração básica de logs para aparecer no Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)

def _safe_float(value, default=0.0):
    """Converte para float com segurança, evitando quebras."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def _safe_int(value, default=0):
    """Converte para int com segurança."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def _parse_report_date(data: dict) -> str:
    raw = data.get("date_start") or data.get("report_date")
    if raw and "T" in str(raw):
        raw = str(raw).split("T")[0]
    try:
        return datetime.strptime(raw, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")

def analyze_daily_metrics(data: dict) -> dict:
    logger.info(">>> Iniciando análise de métricas diárias...")
    
    try:
        # ===== Datas =====
        report_date = _parse_report_date(data)
        generated_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M")

        # ===== Nomes =====
        campaign_name = (
            data.get("Campaign Name")
            or data.get("campaign_name")
            or "Campanha sem nome"
        )

        # ===== Métricas (Com conversão segura) =====
        spend = _safe_float(data.get("spend"))
        impressions = _safe_int(data.get("impressions"))
        reach = _safe_int(data.get("reach"))
        clicks = _safe_int(data.get("clicks"))
        unique_clicks = _safe_int(data.get("unique_clicks"))
        ctr = _safe_float(data.get("ctr"))
        unique_ctr = _safe_float(data.get("unique_ctr"))
        cpc = _safe_float(data.get("cpc"))
        cpm = _safe_float(data.get("cpm"))
        frequency = _safe_float(data.get("frequency"))
        conversions = _safe_int(data.get("conversions"))
        cost_per_conversion = _safe_float(data.get("cost_per_conversion"))

        # ===== Prompt =====
        prompt = f"""
        Você é um gestor de tráfego pago sênior especializado em Meta Ads.
        Seja extremamente direto. Use bullet points.
        
        Analise as métricas abaixo para a campanha: "{campaign_name}"
        
        Métricas:
        - Spend: R$ {spend:.2f}
        - CPM: R$ {cpm:.2f} | CPC: R$ {cpc:.2f}
        - CTR: {ctr:.2f}%
        - Frequência: {frequency:.2f}
        - Conversões: {conversions} (Custo/Conv: R$ {cost_per_conversion:.2f})
        
        Entregue APENAS:
        1. Resumo do desempenho em 1 frase.
        2. 3 Pontos principais (Positivos ou Negativos).
        3. Ação recomendada para hoje (Otimização).
        """

        # ===== Chamada OpenAI =====
        analysis_text = "Análise de IA indisponível no momento."
        
        try:
            logger.info("Chamando OpenAI (gpt-4o-mini)...")
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # <--- CORRIGIDO AQUI (Era gpt-4.1-mini)
                messages=[
                    {"role": "system", "content": "Você é um analista de dados de marketing direto e técnico."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=600
            )
            analysis_text = response.choices[0].message.content
            logger.info("Resposta da OpenAI recebida com sucesso.")
            
        except Exception as e_openai:
            # Se a OpenAI falhar, loga o erro mas NÃO QUEBRA o fluxo.
            # Isso impede o erro 500 no Make e o loop de retentativas.
            logger.error(f"Erro ao chamar OpenAI: {e_openai}")
            analysis_text = f"⚠️ Não foi possível gerar a análise da IA.\nErro técnico: {str(e_openai)}"

        # ===== Formatação Final =====
        formatted_comment = f"""
📊 ANÁLISE DIÁRIA – META ADS

📅 Data: {report_date} | ⏱️ {generated_at}

━━━━━━━━━━━━━━━━━━━━
🎯 {campaign_name}
━━━━━━━━━━━━━━━━━━━━

📌 RESUMO DAS MÉTRICAS
💰 Investido: R$ {spend:.2f}
🔄 Conversões: {conversions} (CPA: R$ {cost_per_conversion:.2f})
🖱️ Cliques: {clicks} (CTR: {ctr:.2f}%)
📢 CPM: R$ {cpm:.2f} | Freq: {frequency:.2f}

━━━━━━━━━━━━━━━━━━━━
🧠 ANÁLISE DA IA
━━━━━━━━━━━━━━━━━━━━
{analysis_text}
"""

        logger.info("Processamento concluído com sucesso.")
        return {
            "success": True,
            "formatted_comment": formatted_comment
        }

    except Exception as e:
        # Captura erros gerais de lógica para não retornar 500 cru
        logger.error(f"Erro fatal no processamento: {e}")
        return {
            "success": False,
            "error": str(e),
            "formatted_comment": "Erro interno ao processar relatório."
        }

# Função Placeholder (Mantida)
def analyze_weekly_metrics(data_list: list) -> dict:
    return {
        "success": False,
        "formatted_comment": "Relatório semanal ainda não habilitado."
    }
