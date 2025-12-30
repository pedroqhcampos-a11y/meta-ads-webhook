#!/usr/bin/env python3.11
"""
Meta Ads Analyzer - Relatório Diário e Semanal (Otimizado para Cliente)
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
    Relatório DIÁRIO - Foco técnico/operacional
    """
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

    # ===== Prompt Diário =====
    prompt = f"""
Você é um gestor de tráfego pago sênior.
Analise as métricas abaixo considerando o OBJETIVO da campanha.

Entregue:
- OBJETIVO IDENTIFICADO
- KPIs PRINCIPAIS
- PONTOS POSITIVOS
- PONTOS A MELHORAR
- AÇÕES IMEDIATAS

Campanha: {campaign_name}

Métricas:
- Investimento: R$ {spend:.2f}
- Impressões: {impressions}
- Alcance: {reach}
- Clicks: {clicks} ({unique_clicks} únicos)
- CTR: {ctr:.2f}%
- CPC: R$ {cpc:.2f}
- CPM: R$ {cpm:.2f}
- Frequência: {frequency:.2f}
- Conversões: {conversions}
- Custo/Conversão: R$ {cost_per_conversion:.2f}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é direto, técnico e acionável."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=1500
        )
        analysis_text = response.choices[0].message.content
    except Exception as e:
        analysis_text = f"⚠️ Não foi possível gerar a análise da IA. Erro: {str(e)}"

    # ===== Formatação Diária =====
    formatted_comment = f"""
📊 ANÁLISE DIÁRIA – META ADS

📅 Dados: {report_date}
⏱️ Gerado em: {generated_at}

━━━━━━━━━━━━━━━━━━━━
🎯 CAMPANHA
{campaign_name}
━━━━━━━━━━━━━━━━━━━━

📌 MÉTRICAS

📈 KPIs – BASE
💰 Investimento: R$ {spend:.2f}
👁️ Impressões: {impressions}
📣 Alcance: {reach}
📢 CPM: R$ {cpm:.2f}
🔄 Frequência: {frequency:.2f}

🖱️ KPIs – CLIQUE
🖱️ Clicks: {clicks} ({unique_clicks} únicos)
📊 CTR: {ctr:.2f}% (único {unique_ctr:.2f}%)
💵 CPC: R$ {cpc:.2f}

━━━━━━━━━━━━━━━━━━━━
🧠 ANÁLISE TÉCNICA
━━━━━━━━━━━━━━━━━━━━

{analysis_text}
"""

    return {
        "success": True,
        "formatted_comment": formatted_comment
    }


def analyze_weekly_metrics(data_list: list) -> dict:
    """
    Gera relatório SEMANAL para CLIENTE (WhatsApp).
    Inclui Roteiro de Áudio em Tópicos.
    """
    # 1. Preparação dos Totais
    total_spend = 0.0
    total_conversions = 0
    total_clicks = 0
    total_impressions = 0
    
    campaign_cards = [] 
    ai_summary_data = []

    # Datas
    try:
        if data_list and len(data_list) > 0:
            report_date = _parse_report_date(data_list[0])
        else:
            report_date = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")
    except:
        report_date = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")

    # 2. Loop principal
    for item in data_list:
        name = item.get("campaign_name") or item.get("Campaign Name") or "Sem Nome"
        spend = float(item.get("spend", 0) or 0)
        impr = int(item.get("impressions", 0) or 0)
        reach = int(item.get("reach", 0) or 0)
        clicks = int(item.get("clicks", 0) or 0)
        
        # Conversões
        conv = 0
        if "conversions" in item and item["conversions"]:
            try:
                conv = int(item["conversions"])
            except:
                conv = 0
        
        # Totais
        total_spend += spend
        total_conversions += conv
        total_clicks += clicks
        total_impressions += impr

        # Cálculos Individuais para o Card (Mais informação de custo)
        cpa_camp = (spend / conv) if conv > 0 else 0
        cpc_camp = (spend / clicks) if clicks > 0 else 0

        # Card Visual (Focado em Investimento e Retorno)
        card = f"""
🔸 *{name}*
💰 Investimento: R$ {spend:.2f}
📉 Custo/Res: R$ {cpa_camp:.2f} | CPC: R$ {cpc_camp:.2f}
🚀 Resultados: {conv} conversões
🖱️ Cliques: {clicks}
"""
        campaign_cards.append(card)

        # Dados para a IA
        ai_summary_data.append(f"- {name}: Investiu R$ {spend:.0f}, gerou {conv} conversões (CPA R$ {cpa_camp:.2f}).")

    # 3. Cálculos Gerais
    cpa_geral = (total_spend / total_conversions) if total_conversions > 0 else 0
    formatted_cards_text = "\n".join(campaign_cards)
    ai_data_text = "\n".join(ai_summary_data)

    # 4. Prompt IA (Ajustado para Tópicos de Áudio)
    prompt = f"""
Você é um consultor de tráfego pago experiente.
Seu objetivo: Preparar um material para eu enviar no WhatsApp do meu CLIENTE (Dono da empresa).

DADOS DA SEMANA:
- Investimento Total: R$ {total_spend:.2f}
- Conversões (Leads/Msgs/Vendas): {total_conversions}
- Custo por Lead/Msg (CPA): R$ {cpa_geral:.2f}

DETALHE DAS CAMPANHAS:
{ai_data_text}

TAREFA 1 (TEXTO DO WHATSAPP):
Escreva um resumo curto, direto e otimista sobre a semana.
- Fale sobre o volume de oportunidades e o custo.
- Cite a melhor campanha.
- Diga o próximo passo.

TAREFA 2 (TÓPICOS PARA ÁUDIO):
Liste de 3 a 5 pontos-chave (bullet points) que eu devo mencionar no áudio.
- Não escreva o roteiro completo.
- Dê apenas os tópicos do que é importante salientar (ex: "Reforçar que o custo caiu...", "Avisar que vamos aumentar a verba em X...").

SAÍDA ESPERADA:
Separe as tarefas com o divisor "###AUDIO###".
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um estrategista de negócios focado em ROI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        full_content = response.choices[0].message.content
        
        if "###AUDIO###" in full_content:
            whatsapp_text, audio_topics = full_content.split("###AUDIO###")
        else:
            whatsapp_text = full_content
            audio_topics = "Não foi possível gerar os tópicos."

    except Exception as e:
        whatsapp_text = "Análise indisponível."
        audio_topics = f"Erro: {e}"

    # 5. Formatação Final (Semanal)
    formatted_comment = f"""
📅 *RELATÓRIO SEMANAL*
*(Dados dos últimos 7 dias)*

💰 *Investimento Total:* R$ {total_spend:.2f}
🚀 *Oportunidades:* {total_conversions}
📉 *Custo por Oportunidade:* R$ {cpa_geral:.2f}

━━━━━━━━━━━━━━━━━━━━
📊 *RESUMO ESTRATÉGICO*
{whatsapp_text.strip()}

━━━━━━━━━━━━━━━━━━━━
🔎 *DETALHE POR CAMPANHA*
{formatted_cards_text}

━━━━━━━━━━━━━━━━━━━━
🎙️ *O QUE FALAR NO ÁUDIO (TÓPICOS)*
_Use estes pontos para gravar seu áudio:_

{audio_topics.strip()}
"""

    return {
        "success": True,
        "formatted_comment": formatted_comment
    }
