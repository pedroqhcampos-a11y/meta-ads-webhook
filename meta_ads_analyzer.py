#!/usr/bin/env python3.11
"""
Meta Ads Analyzer - Relatório Diário Detalhado & Semanal Executivo
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)


def _parse_report_date(data: dict) -> str:
    raw = data.get("date_start") or data.get("report_date")
    if raw and "T" in str(raw):
        raw = str(raw).split("T")[0]
    try:
        return datetime.strptime(raw, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")


def analyze_daily_metrics(data: dict) -> dict:
    """
    Relatório DIÁRIO - Detalhado (Positivo, Atenção, Ação)
    """
    # ===== Datas =====
    report_date = _parse_report_date(data)
    generated_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%H:%M")

    # ===== Nomes =====
    campaign_name = (
        data.get("Campaign Name")
        or data.get("campaign_name")
        or "Campanha sem nome"
    )

    # ===== Métricas =====
    spend = float(data.get("spend", 0) or 0)
    clicks = int(data.get("clicks", 0) or 0)
    ctr = float(data.get("ctr", 0) or 0)
    cpc = float(data.get("cpc", 0) or 0)
    cpm = float(data.get("cpm", 0) or 0)
    conversions = int(data.get("conversions", 0) or 0)
    cost_per_conversion = float(data.get("cost_per_conversion", 0) or 0)

    # ===== Lógica de Objetivo (Contexto para IA) =====
    objective_note = "Objetivo: Vendas/Leads. Foque em Conversão e CPA."
    name_lower = campaign_name.lower()
    
    # Se for tráfego, ajusta a expectativa da IA
    if "tráfego" in name_lower or "trafego" in name_lower or "clique" in name_lower or "visita" in name_lower:
        objective_note = "Objetivo: Tráfego/Cliques. NÃO analise conversões. Foque em CPC, CTR e Volume de Cliques."
    elif "engajamento" in name_lower or "msg" in name_lower or "mensagem" in name_lower:
        objective_note = "Objetivo: Mensagens. Conversão aqui significa 'Mensagem Iniciada'."

    # ===== Prompt Diário (Detalhado) =====
    prompt = f"""
Você é um gestor de tráfego sênior. Analise o desempenho diário desta campanha.
{objective_note}

DADOS DO DIA:
- Campanha: {campaign_name}
- Investimento: R$ {spend:.2f}
- Cliques: {clicks} (CPC R$ {cpc:.2f})
- CTR: {ctr:.2f}%
- Conversões: {conversions} (Custo/Conv R$ {cost_per_conversion:.2f})

ESTRUTURA DA RESPOSTA (Seja direto, use bullets, sem negrito/itálico):
1. PONTOS POSITIVOS: (O que está bom?)
2. PONTOS DE ATENÇÃO: (O que preocupa?)
3. AÇÃO RECOMENDADA: (O que fazer amanhã?)

Não use markdown (* ou #). Use apenas hifens (-) para listas.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        # Limpeza de markdown para garantir visual limpo
        analysis_text = response.choices[0].message.content.replace("*", "").replace("#", "")
    except Exception as e:
        analysis_text = "Análise indisponível."

    # ===== Formatação Diária =====
    formatted_comment = f"""
📅 RELATÓRIO DIÁRIO
Dados de: {report_date} (Gerado às {generated_at})

📍 CAMPANHA: {campaign_name}

💰 MÉTRICAS DO DIA
💵 Investimento: R$ {spend:.2f} (Gasto hoje)
🖱️ Cliques: {clicks} (CPC: R$ {cpc:.2f})
📊 CTR: {ctr:.2f}% (Taxa de clique)

🚀 RESULTADOS
🎯 Conversões: {conversions}
📉 Custo por Resultado: R$ {cost_per_conversion:.2f}

━━━━━━━━━━━━━━━━━━━━
🧠 ANÁLISE TÉCNICA
{analysis_text}
"""

    return {
        "success": True,
        "formatted_comment": formatted_comment
    }


def analyze_weekly_metrics(data_list: list) -> dict:
    """
    Relatório SEMANAL - Executivo para Cliente (WhatsApp/Áudio)
    """
    # 1. Preparação dos Totais
    total_spend = 0.0
    total_conversions = 0
    total_clicks = 0
    
    campaign_cards = [] 
    ai_summary_data = []

    # Datas
    try:
        if data_list and len(data_list) > 0:
            report_date = _parse_report_date(data_list[0])
        else:
            report_date
