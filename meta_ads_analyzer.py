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


def _get_current_date() -> str:
    """Retorna data atual formatada (SP)"""
    return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")


def _parse_report_date(data: dict) -> str:
    """Tenta extrair a data do relatório, se falhar, usa data atual"""
    raw = data.get("date_start") or data.get("report_date")
    if raw and "T" in str(raw):
        raw = str(raw).split("T")[0]
    try:
        return datetime.strptime(raw, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return _get_current_date()


def analyze_daily_metrics(data: dict) -> dict:
    """
    Relatório DIÁRIO - Detalhado
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

    # ===== Lógica de Objetivo =====
    objective_note = "Objetivo: Vendas/Leads. Foque em Conversão e CPA."
    name_lower = campaign_name.lower()
    
    if "tráfego" in name_lower or "trafego" in name_lower or "clique" in name_lower or "visita" in name_lower:
        objective_note = "Objetivo: Tráfego/Cliques. NÃO analise conversões. Foque em CPC, CTR e Volume de Cliques."
    elif "engajamento" in name_lower or "msg" in name_lower or "mensagem" in name_lower:
        objective_note = "Objetivo: Mensagens. Conversão aqui significa 'Mensagem Iniciada'."

    # ===== Prompt Diário =====
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
        analysis_text = response.choices[0].message.content.replace("*", "").replace("#", "")
    except Exception as e:
        analysis_text = f"Análise indisponível. Erro: {str(e)}"

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
    Relatório SEMANAL - Executivo para Cliente
    """
    # 1. Preparação dos Totais
    total_spend = 0.0
    total_conversions = 0
    total_clicks = 0
    
    campaign_cards = [] 
    ai_summary_data = []

    # Datas
    report_date = _get_current_date()
    if data_list and len(data_list) > 0:
        try:
            parsed = _parse_report_date(data_list[0])
            if parsed:
                report_date = parsed
        except Exception:
            pass

    # 2. Loop principal
    for item in data_list:
        name = item.get("campaign_name") or item.get("Campaign Name") or "Sem Nome"
        spend = float(item.get("spend", 0) or 0)
        clicks = int(item.get("clicks", 0) or 0)
        impr = int(item.get("impressions", 0) or 0)
        
        conv = 0
        if "conversions" in item and item["conversions"]:
            try:
                conv = int(item["conversions"])
            except:
                conv = 0
        
        total_spend += spend
        total_conversions += conv
        total_clicks += clicks

        # Cálculos Individuais
        cpc_camp = (spend / clicks) if clicks > 0 else 0
        cpa_camp = (spend / conv) if conv > 0 else 0
        ctr_camp = (clicks / impr * 100) if impr > 0 else 0

        # Lógica Visual
        name_lower = name.lower()
        is_traffic = "tráfego" in name_lower or "trafego" in name_lower or "clique" in name_lower or "perfil" in name_lower
        
        if is_traffic:
            details_line = f"🖱️ Cliques: {clicks} (Visitas)\n📉 Custo p/ Clique: R$ {cpc_camp:.2f}\n📊 CTR: {ctr_camp:.2f}%"
            ai_note = f"Campanha TRÁFEGO. {clicks} cliques, CPC R$ {cpc_camp:.2f}. Ignore conversões."
        else:
            details_line = f"🚀 Conversões: {conv} (Resultados)\n📉 Custo p/ Resultado: R$ {cpa_camp:.2f}\n🖱️ Cliques: {clicks}"
            ai_note = f"Campanha CONVERSÃO. {conv} resultados, CPA R$ {cpa_camp:.2f}."

        card = f"""
📍 CAMPANHA: {name}
💰 Investimento: R$ {spend:.2f}
{details_line}
"""
        campaign_cards.append(card)
        ai_summary_data.append(f"- {name}: Investiu R$ {spend:.2f}. {ai_note}")

    # 3. Formatação Final
    formatted_cards_text = "\n".join(campaign_cards)
    ai_data_text = "\n".join(ai_summary_data)

    # 4. Prompt IA
    prompt = f"""
Você é um consultor. Escreva relatório semanal para WhatsApp do cliente.
Sem markdown (* ou #).

DADOS:
Investimento: R$ {total_spend:.2f}
Resultados: {total_conversions}
Cliques: {total_clicks}

DETALHE:
{ai_data_text}

TAREFA 1 (TEXTO WHATSAPP):
Resumo curto e direto. Respeite o objetivo (se for tráfego, elogie cliques; se for conversão, fale de CPA).
Termine com "Próximos passos".

TAREFA 2 (TÓPICOS ÁUDIO):
3 a 4 bullet points para eu gravar áudio.

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
            whatsapp_text = whatsapp_text.replace("###", "").strip()
            audio_topics = audio_topics.replace("###", "").strip()
        else:
            whatsapp_text = full_content
            audio_topics = "Não foi possível gerar tópicos."

    except Exception as e:
        whatsapp_text = f"Análise indisponível: {e}"
        audio_topics = "Erro na geração."

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
