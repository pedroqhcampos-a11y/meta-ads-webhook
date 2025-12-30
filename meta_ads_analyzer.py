#!/usr/bin/env python3.11
"""
Meta Ads Analyzer – Relatório Diário Profissional (ClickUp)
Compatível com webhook_server.py
"""

import os
from datetime import datetime
from openai import OpenAI


# =========================
# OpenAI Client
# =========================
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)


# =========================
# Utilidades
# =========================
def resolve_report_date(data: dict) -> str:
    """
    Resolve a data do relatório a partir dos dados recebidos.
    Aceita:
    - YYYY-MM-DD
    - ISO datetime (YYYY-MM-DDTHH:MM:SS.sssZ)
    """
    raw_date = (
        data.get("report_date")
        or data.get("date_start")
        or data.get("start_date")
    )

    if not raw_date:
        return "Data não informada"

    raw_date = str(raw_date)

    # Remove hora se vier em ISO
    if "T" in raw_date:
        raw_date = raw_date.split("T")[0]

    try:
        parsed = datetime.strptime(raw_date, "%Y-%m-%d")
        return parsed.strftime("%d/%m/%Y")
    except ValueError:
        return f"Data inválida: {raw_date}"


# =========================
# Análise diária (1 campanha)
# =========================
def analyze_daily_metrics(data: dict) -> dict:
    """
    Analisa métricas de UMA campanha
    """

    campaign_name = data.get("campaign_name") or "Campanha sem nome"

    # métricas base
    spend = float(data.get("spend", 0) or 0)
    impressions = int(data.get("impressions", 0) or 0)
    reach = int(data.get("reach", 0) or 0)
    clicks = int(data.get("clicks", 0) or 0)
    unique_clicks = int(data.get("unique_clicks", 0) or 0)
    ctr = float(data.get("ctr", 0) or 0)
    unique_ctr = float(data.get("unique_ctr", 0) or 0)
    cpc = float(data.get("cpc", 0) or 0)
    cpm = float(data.get("cpm", 0) or 0)
    frequency = float(data.get("frequency", 0) or 0)

    # métricas de resultado (podem não existir)
    conversions = int(data.get("conversions", 0) or 0)
    cost_per_conversion = float(data.get("cost_per_conversion", 0) or 0)
    messages = int(data.get("messages", 0) or 0)
    link_clicks = int(data.get("link_clicks", clicks) or 0)

    report_date = resolve_report_date(data)
    generated_at = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # =========================
    # Prompt IA
    # =========================
    prompt = f"""
Você é um gestor de tráfego pago sênior especializado em Meta Ads.

Analise a campanha abaixo e siga OBRIGATORIAMENTE esta estrutura:

1. MÉTRICAS DA CAMPANHA
- Defina qual é o RESULTADO principal de acordo com o objetivo da campanha
  (ex: cliques, mensagens, conversões, engajamento)
- Mostre:
  • Resultado
  • Custo por resultado
  • Alcance
  • Impressões
  • CTR (se aplicável)
  • CPM
  • Frequência

2. CONSIDERAÇÕES
- Pontos positivos
- Pontos de atenção
- Ações recomendadas explicando COMO FAZER

Campanha: {campaign_name}

Dados:
- Investimento: R$ {spend:.2f}
- Impressões: {impressions}
- Alcance: {reach}
- Clicks: {clicks} ({unique_clicks} únicos)
- CTR: {ctr:.2f}% (único {unique_ctr:.2f}%)
- CPC: R$ {cpc:.2f}
- CPM: R$ {cpm:.2f}
- Frequência: {frequency:.2f}
- Conversões: {conversions}
- Custo por conversão: R$ {cost_per_conversion:.2f}
- Mensagens: {messages}
- Cliques no link: {link_clicks}

Seja direto, técnico e focado em decisão.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Você é um gestor de tráfego sênior, direto e orientado a resultado."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.6,
        max_tokens=1200
    )

    analysis_text = response.choices[0].message.content

    comment = f"""
📊 ANÁLISE DIÁRIA – META ADS (INTERNO)

📅 Dados: {report_date}
⏱️ Gerado em: {generated_at}

━━━━━━━━━━━━━━━━━━━━
🎯 CAMPANHA
{campaign_name}
━━━━━━━━━━━━━━━━━━━━

{analysis_text}
"""

    return {
        "success": True,
        "formatted_comment": comment
    }


# =========================
# Stub semanal (compatibilidade)
# =========================
def analyze_weekly_metrics(data_list: list) -> dict:
    """
    Stub temporário para manter compatibilidade com o webhook_server.
    """
    return {
        "success": False,
        "formatted_comment": "Relatório semanal ainda não habilitado."
    }


# =========================
# Execução de teste local
# =========================
if __name__ == "__main__":
    test_data = {
        "campaign_name": "[ENGAJAMENTO] [PERFIL]",
        "spend": "10.23",
        "impressions": "4100",
        "reach": "3734",
        "clicks": "185",
        "unique_clicks": "173",
        "ctr": "4.51",
        "unique_ctr": "4.63",
        "cpc": "0.06",
        "cpm": "2.50",
        "frequency": "1.10",
        "date_start": "2025-12-29T03:00:00.000Z"
    }

    result = analyze_daily_metrics(test_data)
    print(result["formatted_comment"])
