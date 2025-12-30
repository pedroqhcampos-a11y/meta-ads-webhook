#!/usr/bin/env python3.11
"""
Meta Ads Analyzer - Relatório Diário (Original Restaurado + Fix)
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
    # ===== Datas =====
    report_date = _parse_report_date(data)
    generated_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M")

    # ===== Nomes =====
    campaign_name = (
        data.get("Campaign Name")
        or data.get("campaign_name")
        or "Campanha sem nome"
    )

    # ===== Métricas =====
    # Mantive sua lógica original de conversão
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
    conversions = int(data.get("conversions", 0) or 0)
    cost_per_conversion = float(data.get("cost_per_conversion", 0) or 0)

    # ===== Prompt (O ORIGINAL DETALHADO) =====
    prompt = f"""
Você é um gestor de tráfego pago sênior especializado em Meta Ads.

Analise as métricas abaixo considerando o OBJETIVO da campanha.
Se não houver conversões, use CTR, CPC, CPM, frequência e volume de cliques.

Entregue:
- OBJETIVO IDENTIFICADO
- KPIs PRINCIPAIS (3–6)
- PONTOS POSITIVOS
- PONTOS A MELHORAR
- AÇÕES IMEDIATAS (COMO FAZER)

Campanha: {campaign_name}

Métricas:
- Spend: R$ {spend:.2f}
- Impressões: {impressions}
- Alcance: {reach}
- Clicks: {clicks} ({unique_clicks} únicos)
- CTR: {ctr:.2f}% (único {unique_ctr:.2f}%)
- CPC: R$ {cpc:.2f}
- CPM: R$ {cpm:.2f}
- Frequência: {frequency:.2f}
- Conversões: {conversions}
- Custo/Conversão: R$ {cost_per_conversion:.2f}
"""

    # ===== Chamada OpenAI (COM A CORREÇÃO DO MODELO) =====
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # <--- AQUI ESTAVA O ERRO (Era gpt-4.1)
            messages=[
                {"role": "system", "content": "Você é direto, técnico e acionável."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=1500
        )
        analysis_text = response.choices[0].message.content
    except Exception as e:
        # Se
