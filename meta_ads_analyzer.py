#!/usr/bin/env python3.11
"""
Meta Ads Analyzer - Relatório Visual Limpo e Contextualizado
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
    Relatório DIÁRIO - Visual Limpo e Explicativo
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

    # ===== Lógica de Objetivo (Para a IA não errar) =====
    objective_note = "Objetivo: Vendas/Leads. Foque em Conversão e CPA."
    name_lower = campaign_name.lower()
    if "tráfego" in name_lower or "trafego" in name_lower or "clique" in name_lower or "visita" in name_lower:
        objective_note = "Objetivo: Tráfego/Cliques. NÃO analise conversões. Foque em CPC, CTR e Volume de Cliques."
    elif "engajamento" in name_lower or "msg" in name_lower or "mensagem" in name_lower:
        objective_note = "Objetivo: Mensagens. Conversão aqui significa 'Mensagem Iniciada'."

    # ===== Prompt Diário =====
    prompt = f"""
Você é um gestor de tráfego. Analise esta campanha diária.
{objective_note}

Métricas do dia:
- Campanha: {campaign_name}
- Investimento: R$ {spend:.2f}
- Cliques: {clicks} (CPC R$ {cpc:.2f})
- Conversões: {conversions} (Custo/Conv R$ {cost_per_conversion:.2f})

Responda em texto corrido curto (3 linhas máx).
Diga se o dia foi bom baseando-se no objetivo identificado.
Não use negrito nem itálico.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=300
        )
        analysis_text = response.choices[0].message.content.replace("*", "").replace("#", "")
    except Exception as e:
        analysis_text = "Análise indisponível."

    # ===== Formatação Diária (Visual Limpo) =====
    formatted_comment = f"""
📅 RELATÓRIO DIÁRIO
Dados de: {report_date} (Gerado às {generated_at})

📍 CAMPANHA: {campaign_name}

💰 MÉTRICAS PRINCIPAIS
💵 Investimento: R$ {spend:.2f} (Valor gasto hoje)
🖱️ Cliques: {clicks} (Interesse no anúncio)
📊 CTR: {ctr:.2f}% (Taxa de clique)

🚀 RESULTADOS
🎯 Conversões: {conversions} (Resultados obtidos)
📉 Custo por Resultado: R$ {cost_per_conversion:.2f}

🧠 ANÁLISE RÁPIDA
{analysis_text}
"""

    return {
        "success": True,
        "formatted_comment": formatted_comment
    }


def analyze_weekly_metrics(data_list: list) -> dict:
    """
    Gera relatório SEMANAL para CLIENTE (WhatsApp).
    Visual limpo, sem markdown complexo, com emojis e explicações.
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
            report_date = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")
    except:
        report_date = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")

    # 2. Loop principal
    for item in data_list:
        name = item.get("campaign_name") or item.get("Campaign Name") or "Sem Nome"
        spend = float(item.get("spend", 0) or 0)
        clicks = int(item.get("clicks", 0) or 0)
        impr = int(item.get("impressions", 0) or 0)
        
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

        # Cálculos Individuais
        cpc_camp = (spend / clicks) if clicks > 0 else 0
        cpa_camp = (spend / conv) if conv > 0 else 0
        ctr_camp = (clicks / impr * 100) if impr > 0 else 0

        # Lógica para determinar o que mostrar no Card
        # Se for TRÁFEGO, mostra CPC e Cliques com destaque. Se for CONVERSÃO, mostra CPA.
        name_lower = name.lower()
        is_traffic = "tráfego" in name_lower or "trafego" in name_lower or "clique" in name_lower or "perfil" in name_lower
        
        if is_traffic:
            # Layout para Tráfego (Esconde conversão zerada se não tiver)
            details_line = f"🖱️ Cliques: {clicks} (Pessoas que acessaram)\n📉 Custo por Clique: R$ {cpc_camp:.2f}\n📊 CTR: {ctr_camp:.2f}% (Atratividade)"
            ai_note = f"Campanha de TRÁFEGO/CLIQUES. Teve {clicks} cliques a CPC R$ {cpc_camp:.2f}. Ignore conversões."
        else:
            # Layout Padrão (Foco em Conversão)
            details_line = f"🚀 Conversões: {conv} (Resultados)\n📉 Custo por Resultado: R$ {cpa_camp:.2f}\n🖱️ Cliques: {clicks}"
            ai_note = f"Campanha de CONVERSÃO. Teve {conv} resultados a CPA R$ {cpa_camp:.2f}."

        # Card Visual Limpo (Sem negrito/markdown que quebra)
        card = f"""
📍 CAMPANHA: {name}
💰 Investimento: R$ {spend:.2f} (Valor investido)
{details_line}
"""
        campaign_cards.append(card)
        ai_summary_data.append(f"- {name}: Investiu R$ {spend:.2f}. {ai_note}")

    # 3. Cálculos Gerais
    formatted_cards_text = "\n".join(campaign_cards)
    ai_data_text = "\n".join(ai_summary_data)

    # 4. Prompt IA (Contextualizado)
    prompt = f"""
Você é um consultor de tráfego. Escreva um relatório semanal para o WhatsApp do cliente.
Não use negrito, itálico ou markdown (sem asteriscos).

DADOS DA SEMANA:
Total Investido: R$ {total_spend:.2f}
Total Conversões: {total_conversions}
Total Cliques: {total_clicks}

DETALHE:
{ai_data_text}

TAREFA 1 (TEXTO DO WHATSAPP):
Escreva um resumo curto e direto.
ATENÇÃO: Respeite o objetivo de cada campanha.
- Se a campanha for de TRÁFEGO/CLIQUE, elogie o volume de cliques e o CPC baixo. Não reclame de falta de vendas nela.
- Se for de CONVERSÃO, analise o CPA.
- Termine com "Próximos passos".

TAREFA 2 (TÓPICOS ÁUDIO):
Liste 3 a 4 tópicos para eu gravar um áudio.
Seja direto.

Separador: ###AUDIO###
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        full_content = response.choices[0].message.content.replace("*", "").replace("#", "")
        
        if "AUDIO" in full_content:
            whatsapp_text, audio_topics = full_content.split("AUDIO")
            # Limpeza extra caso sobrem caracteres do split
            whatsapp_text = whatsapp_text.replace("###", "").strip()
            audio_topics = audio_topics.replace("###", "").strip()
        else:
            whatsapp_text = full_content
            audio_topics = "Não foi possível gerar tópicos."

    except Exception as e:
        whatsapp_text = "Análise indisponível."
        audio_topics = f"Erro: {e}"

    # 5. Formatação Final (Visual Organizado e Educativo)
    formatted_comment = f"""
📅 RELATÓRIO SEMANAL
(Dados dos últimos 7 dias)

💰 RESUMO GERAL
💵 Investimento Total: R$ {total_spend:.2f}
🚀 Total de Resultados: {total_conversions}
🖱️ Total de Cliques: {total_clicks}

━━━━━━━━━━━━━━━━━━━━
📊 DETALHE POR CAMPANHA
{formatted_cards_text}

━━━━━━━━━━━━━━━━━━━━
🧠 ANÁLISE ESTRATÉGICA
{whatsapp_text.strip()}

━━━━━━━━━━━━━━━━━━━━
🎙️ SUGESTÃO DE ÁUDIO
(Tópicos para gravar)

{audio_topics.strip()}
"""

    return {
        "success": True,
        "formatted_comment": formatted_comment
    }
