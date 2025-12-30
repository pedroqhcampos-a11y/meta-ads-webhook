#!/usr/bin/env python3.11
"""
Meta Ads Analyzer - Relatório Diário (estável)
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
# Função principal (DIÁRIA)
# =========================
def analyze_daily_metrics(data: dict) -> dict:
    """
    Analisa métricas diárias de UMA campanha.
    Versão estável: 1 campanha por request.
    """

    # -------------------------
    # Data (correção mínima)
    # -------------------------
    raw_date = data.get("date_start") or data.get("report_date")
    if raw_date and "T" in str(raw_date):
        raw_date = str(raw_date).split("T")[0]

    report_date = raw_date or datetime.now().strftime("%Y-%m-%d")
    report_date = datetime.strptime(report_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    generated_at = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # -------------------------
    # Identificação
    # -------------------------
    campaign_name = data.get("campaign_name", "Campanha sem nome")

    # -------------------------
    # Métricas (simples e seguras)
    # -------------------------
    spend = float(data.get("spend", 0) or 0)
    impressions = int(data.get("impressions", 0) or 0)
    reach = int(data.get("reach", 0) or 0)
    clicks = int(data.get("clicks", 0) or 0)
    unique_clicks = int(data.get("unique_clicks", 0) or 0)
    ctr = float(data.get("ctr", 0) or 0)
    cpc = float(data.get("cpc", 0) or 0)
    cpm = float(data.get("cpm", 0) or 0)
    frequency = float(data.get("frequency", 0) or 0)
    conversions = int(data.get("conversions", 0) or 0)
    cost_per_conversion = float(data.get("cost_per_conversion", 0) or 0)

    # -------------------------
    # Prompt IA (simples)
    # -------------------------
    prompt = f"""
Você é um gestor de tráfego pago sênior em Meta Ads.

Analise a campanha abaixo e responda de forma objetiva, clara e acionável.

Estrutura obrigatória:

📊 MÉTRICAS DA CAMPANHA
- Resultado principal (defina de acordo com o objetivo)
- Custo por resultado
- Alcance
- Impressões
- CTR
- CPM
- Frequência

🧠 CONSIDERAÇÕES
- Pontos positivos
- Pontos a melhorar
- Ações imediatas (explique COMO FAZER)

Campanha: {campaign_name}

Dados:
- Investimento: R$ {spend:.2f}
- Impressões: {impressions}
- Alcance: {reach}
- Cliques: {clicks} ({unique_clicks} únicos)
- CTR: {ctr:.2f}%
- CPC: R$ {cpc:.2f}
- CPM: R$ {cpm:.2f}
- Frequência: {frequency:.2f}
- Conversões: {conversions}
- Custo por conversão: R$ {cost_per_conversion:.2f}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Você é um gestor de tráfego sênior, direto e estratégico."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=1200
    )

    analysis_text = response.choices[0].message.content

    # -------------------------
    # Formatação FINAL (ClickUp)
    # -------------------------
    formatted_comment = f"""
📊 ANÁLISE DIÁRIA – META ADS (INTERNO)

📅 Dados: {report_date}
⏱️ Gerado em: {generated_at}

━━━━━━━━━━━━━━━━━━━━
🎯 CAMPANHA
{campaign_name}
━━━━━━━━━━━━━━━━━━━━

📌 MÉTRICAS
💰 Investimento: R$ {spend:.2f}
👁️ Impressões: {impressions}
📣 Alcance: {reach}
🖱️ Cliques: {clicks}
📊 CTR: {ctr:.2f}%
💵 CPC: R$ {cpc:.2f}
📢 CPM: R$ {cpm:.2f}
🔄 Frequência: {frequency:.2f}

━━━━━━━━━━━━━━━━━━━━
🧠 CONSIDERAÇÕES
━━━━━━━━━━━━━━━━━━━━

{analysis_text}
"""

    return {
        "success": True,
        "formatted_comment": formatted_comment
    }


# =========================
# Stub semanal (mantém compatibilidade)
# =========================
def analyze_weekly_metrics(data_list: list) -> dict:
    return {
        "success": False,
        "formatted_comment": "Relatório semanal ainda não habilitado."
    }


# =========================
# Teste local
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
        "cpc": "0.06",
        "cpm": "2.50",
        "frequency": "1.10",
        "date_start": "2025-12-29T03:00:00.000Z"
    }

    result = analyze_daily_metrics(test_data)
    print(result["formatted_comment"])
