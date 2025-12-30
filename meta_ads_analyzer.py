#!/usr/bin/env python3.11
"""
Meta Ads Analyzer - Análise profissional de métricas com IA

(Atualização)
✅ Visual ClickUp MUITO melhor (separadores, hierarquia, menos negrito quebrando)
✅ Mantém a base do seu código
✅ Continua inteligente por objetivo (objective + nome + results)
✅ Datas:
  - Dados: report_date (YYYY-MM-DD vindo do Make)
  - Gerado em: agora (America/Sao_Paulo)
"""

import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

TZ = ZoneInfo("America/Sao_Paulo")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)


# -------------------------
# Helpers (datas e parsing)
# -------------------------

def resolve_report_dates(data: dict) -> tuple[str, str]:
    report_date_raw = data.get("report_date")

    if report_date_raw:
        try:
            report_date = datetime.strptime(report_date_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            report_date = f"Formato inválido: {report_date_raw} (esperado YYYY-MM-DD)"
    else:
        report_date = "Data não informada (envie report_date no Make: YYYY-MM-DD)"

    generated_at = datetime.now(TZ).strftime("%d/%m/%Y às %H:%M")
    return report_date, generated_at


def _safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _safe_int(x, default=0) -> int:
    try:
        return int(float(x))
    except Exception:
        return int(default)


def _compute_roas(spend: float, conversion_value: float) -> float:
    return (conversion_value / spend) if spend > 0 and conversion_value > 0 else 0.0


def _infer_objective(campaign_name: str, objective_field: str, results: dict) -> str:
    if objective_field:
        return str(objective_field).strip().upper()

    name = (campaign_name or "").upper()

    if "CONVERS" in name or "VEND" in name or "PURCHASE" in name:
        return "CONVERSIONS"
    if "MENSAG" in name or "MESSAGE" in name or "WHATS" in name or "DIRECT" in name:
        return "MESSAGES"
    if "TRÁFEG" in name or "TRAFE" in name or "CLIQU" in name or "LINK" in name:
        return "TRAFFIC"
    if "LEAD" in name or "CADAST" in name:
        return "LEADS"
    if "ENGAJ" in name or "ENGAGE" in name or "SEGUID" in name or "PERFIL" in name:
        return "ENGAGEMENT"

    rkeys = set((results or {}).keys())
    if {"purchases", "purchase", "orders"}.intersection(rkeys):
        return "CONVERSIONS"
    if {"messages_started", "messaging_conversations_started"}.intersection(rkeys):
        return "MESSAGES"
    if {"link_clicks", "landing_page_views", "outbound_clicks"}.intersection(rkeys):
        return "TRAFFIC"
    if {"leads"}.intersection(rkeys):
        return "LEADS"
    if {"post_engagements", "engagements", "profile_visits", "follows"}.intersection(rkeys):
        return "ENGAGEMENT"

    return "UNKNOWN"


# -------------------------
# Prompt diário inteligente
# -------------------------

def build_daily_prompt(data: dict) -> str:
    campaign_name = data.get("campaign_name", "")
    ad_name = data.get("ad_name", "")
    adset_name = data.get("adset_name", "")

    spend = _safe_float(data.get("spend", 0))
    impressions = _safe_int(data.get("impressions", 0))
    reach = _safe_int(data.get("reach", 0))
    clicks = _safe_int(data.get("clicks", 0))
    unique_clicks = _safe_int(data.get("unique_clicks", 0))
    ctr = _safe_float(data.get("ctr", 0))
    unique_ctr = _safe_float(data.get("unique_ctr", 0))
    cpc = _safe_float(data.get("cpc", 0))
    cpm = _safe_float(data.get("cpm", 0))
    frequency = _safe_float(data.get("frequency", 0))

    conversions = _safe_int(data.get("conversions", 0))
    conversion_value = _safe_float(data.get("conversion_value", 0))
    roas = _compute_roas(spend, conversion_value)

    objective_field = (data.get("objective") or "").strip()
    results = data.get("results", {}) or {}
    inferred_obj = _infer_objective(campaign_name, objective_field, results)
    results_json = json.dumps(results, ensure_ascii=False, indent=2)

    return f"""Você é um gestor de tráfego pago sênior. Gere uma análise DIÁRIA curta e objetiva, para tomada de decisão interna (não é relatório para cliente).

TAREFA (OBRIGATÓRIA):
1) Identifique o OBJETIVO da campanha usando:
   - primeiro: campo objective (se vier)
   - segundo: nome da campanha (ex: [ENGAJAMENTO], [CONVERSÃO], [MENSAGEM], [TRÁFEGO], etc.)
   - terceiro: as métricas disponíveis em results
2) Escolha os KPIs principais ADEQUADOS AO OBJETIVO com base nas métricas disponíveis:
   - Use 3 a 6 KPIs no máximo
   - Se o objetivo for ENGAGEMENT/MESSAGES/TRAFFIC, NÃO use "conversões" como KPI principal (pode ser 0)
   - Use results quando existir (ex.: messages_started, link_clicks, profile_visits, post_engagements, leads, purchases, etc.)
3) Recomende ações com "COMO FAZER" (passo a passo curto) quando houver problema ou oportunidade.
4) Se estiver normal, diga explicitamente que não há ação imediata.

CONTEXTO:
- Campanha: {campaign_name}
- Conjunto: {adset_name}
- Anúncio: {ad_name}
- Objective informado: {objective_field if objective_field else "(não informado)"}
- Objective inferido (pista): {inferred_obj}

MÉTRICAS UNIVERSAIS:
- Spend: R$ {spend:.2f}
- Impressões: {impressions:,}
- Alcance: {reach:,}
- CPM: R$ {cpm:.2f}
- Frequência: {frequency:.2f}

MÉTRICAS DE CLIQUE (se existirem):
- Clicks: {clicks} (únicos: {unique_clicks})
- CTR: {ctr:.2f}% (único: {unique_ctr:.2f}%)
- CPC: R$ {cpc:.2f}

MÉTRICAS DE CONVERSÃO (se existirem, mas NÃO são obrigatórias):
- Conversões: {conversions}
- Valor de conversão: R$ {conversion_value:.2f}
- ROAS: {roas:.2f}x

RESULTADOS (variável por objetivo):
{results_json}

FORMATO OBRIGATÓRIO:

🎯 OBJETIVO IDENTIFICADO:
- (uma linha)

📌 KPIs PRINCIPAIS (3–6):
- (liste apenas os KPIs certos para o objetivo, com números)

🟢 PONTOS POSITIVOS:
- até 3 bullets

🟡 PONTOS A MELHORAR:
- até 3 bullets

🚨 AÇÕES IMEDIATAS (COMO FAZER):
- até 3 ações
- cada ação deve dizer COMO executar (copy/criativo/público/orçamento)
- se estiver tudo normal: "Nenhuma ação imediata necessária."

REGRAS:
- Direto, sem texto longo
- Sem texto para cliente
- Use as métricas certas para o objetivo (não force conversão em engajamento).
""".strip()


# -------------------------
# Formatting ClickUp (bonito)
# -------------------------

def _separator(title: str) -> str:
    # separador visual “grande” (funciona bem no ClickUp)
    line = "━━━━━━━━━━━━━━━━━━━━"
    return f"{line}\n{title}\n{line}"


def format_daily_comment(
    data: dict,
    report_date: str,
    generated_at: str,
    campaign_name: str,
    spend: float,
    impressions: int,
    reach: int,
    clicks: int,
    unique_clicks: int,
    ctr: float,
    unique_ctr: float,
    cpc: float,
    cpm: float,
    frequency: float,
    conversions: int,
    roas: float,
    analysis_text: str
) -> str:
    client_name = data.get("client_name", "Snob Motel LTDA")

    header = (
        "📊 ANÁLISE DIÁRIA – META ADS (INTERNO)\n\n"
        f"📅 Dados: {report_date}\n"
        f"⏱️ Gerado em: {generated_at}\n"
    )

    camp_section = f"{_separator('🎯 CAMPANHA')}\n{campaign_name}\n"

    kpis_base = (
        "📈 KPIs – BASE\n"
        f"💰 Spend: R$ {spend:.2f}\n"
        f"👁️ Impressões: {impressions:,}\n"
        f"📣 Alcance: {reach:,}\n"
        f"📢 CPM: R$ {cpm:.2f}\n"
        f"🔄 Frequência: {frequency:.2f}\n"
    )

    kpis_click = (
        "\n🖱️ KPIs – CLIQUE\n"
        f"🖱️ Clicks: {clicks} ({unique_clicks} únicos)\n"
        f"📊 CTR: {ctr:.2f}% (único {unique_ctr:.2f}%)\n"
        f"💵 CPC: R$ {cpc:.2f}\n"
    )

    kpis_conv = ""
    if conversions > 0 or roas > 0:
        kpis_conv = (
            "\n🎯 KPIs – CONVERSÃO\n"
            f"🎯 Conversões: {conversions}\n"
            f"📈 ROAS: {roas:.2f}x\n"
        )

    analysis_section = f"\n{_separator('🧠 ANÁLISE')}\n{analysis_text}\n"

    return (
        f"{header}\n"
        f"{camp_section}\n"
        f"{_separator('📌 MÉTRICAS')}\n"
        f"{kpis_base}{kpis_click}{kpis_conv}"
        f"{analysis_section}"
    )


def format_daily_comment_fallback(data: dict) -> str:
    report_date, generated_at = resolve_report_dates(data)

    campaign_name = data.get("campaign_name", "Campanha sem nome")
    spend = _safe_float(data.get("spend", 0))
    impressions = _safe_int(data.get("impressions", 0))
    reach = _safe_int(data.get("reach", 0))
    clicks = _safe_int(data.get("clicks", 0))
    ctr = _safe_float(data.get("ctr", 0))
    cpc = _safe_float(data.get("cpc", 0))
    cpm = _safe_float(data.get("cpm", 0))
    frequency = _safe_float(data.get("frequency", 0))

    header = (
        "📊 ANÁLISE DIÁRIA – META ADS (INTERNO)\n\n"
        f"📅 Dados: {report_date}\n"
        f"⏱️ Gerado em: {generated_at}\n"
    )
    camp_section = f"{_separator('🎯 CAMPANHA')}\n{campaign_name}\n"

    metrics = (
        f"{_separator('📌 MÉTRICAS')}\n"
        "📈 KPIs – BASE\n"
        f"💰 Spend: R$ {spend:.2f}\n"
        f"👁️ Impressões: {impressions:,}\n"
        f"📣 Alcance: {reach:,}\n"
        f"📢 CPM: R$ {cpm:.2f}\n"
        f"🔄 Frequência: {frequency:.2f}\n\n"
        "🖱️ KPIs – CLIQUE\n"
        f"🖱️ Clicks: {clicks}\n"
        f"📊 CTR: {ctr:.2f}%\n"
        f"💵 CPC: R$ {cpc:.2f}\n"
    )

    return (
        f"{header}\n{camp_section}\n{metrics}\n"
        f"{_separator('🧠 ANÁLISE')}\n"
        "🟡 IA indisponível.\n"
        "🚨 Nenhuma ação imediata necessária.\n"
    )


# -------------------------
# DAILY (Single Campaign)
# -------------------------

def analyze_daily_metrics(data: dict) -> dict:
    report_date, generated_at = resolve_report_dates(data)

    campaign_name = data.get("campaign_name", "")

    spend = _safe_float(data.get("spend", 0))
    impressions = _safe_int(data.get("impressions", 0))
    reach = _safe_int(data.get("reach", 0))
    clicks = _safe_int(data.get("clicks", 0))
    unique_clicks = _safe_int(data.get("unique_clicks", 0))
    ctr = _safe_float(data.get("ctr", 0))
    unique_ctr = _safe_float(data.get("unique_ctr", 0))
    cpc = _safe_float(data.get("cpc", 0))
    cpm = _safe_float(data.get("cpm", 0))
    frequency = _safe_float(data.get("frequency", 0))

    conversions = _safe_int(data.get("conversions", 0))
    conversion_value = _safe_float(data.get("conversion_value", 0))
    roas = _compute_roas(spend, conversion_value)

    prompt = build_daily_prompt(data)

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um gestor de tráfego pago sênior, direto, técnico e focado em otimização diária."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=900
        )

        analysis_text = (response.choices[0].message.content or "").strip()

        formatted_comment = format_daily_comment(
            data=data,
            report_date=report_date,
            generated_at=generated_at,
            campaign_name=campaign_name,
            spend=spend,
            impressions=impressions,
            reach=reach,
            clicks=clicks,
            unique_clicks=unique_clicks,
            ctr=ctr,
            unique_ctr=unique_ctr,
            cpc=cpc,
            cpm=cpm,
            frequency=frequency,
            conversions=conversions,
            roas=roas,
            analysis_text=analysis_text
        )

        return {
            "success": True,
            "type": "daily_single",
            "analysis": analysis_text,
            "formatted_comment": formatted_comment
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "formatted_comment": format_daily_comment_fallback(data)
        }


# -------------------------
# DAILY (Consolidated)
# -------------------------

def analyze_daily_metrics_consolidated(payload: dict) -> dict:
    report_date, generated_at = resolve_report_dates(payload)
    campaigns = payload.get("campaigns") or []
    client_name = payload.get("client_name", "Snob Motel LTDA")

    if not isinstance(campaigns, list) or len(campaigns) == 0:
        return {
            "success": False,
            "error": "Payload inválido: envie uma lista em 'campaigns'.",
            "formatted_comment": (
                "📊 ANÁLISE DIÁRIA – META ADS (INTERNO)\n\n"
                f"📅 Dados: {report_date}\n"
                f"⏱️ Gerado em: {generated_at}\n\n"
                "Nenhuma campanha enviada em campaigns."
            )
        }

    total_spend = sum(_safe_float(c.get("spend", 0)) for c in campaigns)
    total_impressions = sum(_safe_int(c.get("impressions", 0)) for c in campaigns)
    total_reach = sum(_safe_int(c.get("reach", 0)) for c in campaigns)
    total_clicks = sum(_safe_int(c.get("clicks", 0)) for c in campaigns)

    total_conversions = sum(_safe_int(c.get("conversions", 0)) for c in campaigns)
    total_value = sum(_safe_float(c.get("conversion_value", 0)) for c in campaigns)
    total_roas = _compute_roas(total_spend, total_value)

    header = (
        "📊 ANÁLISE DIÁRIA – META ADS (INTERNO) — CONSOLIDADO\n\n"
        f"📅 Dados: {report_date}\n"
        f"⏱️ Gerado em: {generated_at}\n\n"
    )

    summary = (
        f"{_separator('📌 RESUMO DO DIA')}\n"
        f"💰 Spend total: R$ {total_spend:.2f}\n"
        f"👁️ Impressões: {total_impressions:,}\n"
        f"📣 Alcance: {total_reach:,}\n"
        f"🖱️ Clicks: {total_clicks}\n"
    )
    if total_conversions > 0 or total_roas > 0:
        summary += f"🎯 Conversões: {total_conversions}\n📈 ROAS total: {total_roas:.2f}x\n"

    blocks = []
    for c in campaigns:
        if "report_date" not in c and payload.get("report_date"):
            c["report_date"] = payload["report_date"]
        if "client_name" not in c and client_name:
            c["client_name"] = client_name

        prompt = build_daily_prompt(c)

        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Você é um gestor de tráfego pago sênior, direto, técnico e focado em otimização diária."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=800
            )
            analysis_text = (response.choices[0].message.content or "").strip()
        except Exception:
            analysis_text = "🟡 IA indisponível.\n🚨 Nenhuma ação imediata necessária."

        name = c.get("campaign_name", "Campanha sem nome")
        spend = _safe_float(c.get("spend", 0))
        impressions = _safe_int(c.get("impressions", 0))
        reach = _safe_int(c.get("reach", 0))
        clicks = _safe_int(c.get("clicks", 0))
        unique_clicks = _safe_int(c.get("unique_clicks", 0))
        ctr = _safe_float(c.get("ctr", 0))
        unique_ctr = _safe_float(c.get("unique_ctr", 0))
        cpc = _safe_float(c.get("cpc", 0))
        cpm = _safe_float(c.get("cpm", 0))
        freq = _safe_float(c.get("frequency", 0))

        conv = _safe_int(c.get("conversions", 0))
        val = _safe_float(c.get("conversion_value", 0))
        roas = _compute_roas(spend, val)

        kpis = (
            "📈 KPIs – BASE\n"
            f"💰 Spend: R$ {spend:.2f}\n"
            f"👁️ Impressões: {impressions:,}\n"
            f"📣 Alcance: {reach:,}\n"
            f"📢 CPM: R$ {cpm:.2f}\n"
            f"🔄 Frequência: {freq:.2f}\n\n"
            "🖱️ KPIs – CLIQUE\n"
            f"🖱️ Clicks: {clicks} ({unique_clicks} únicos)\n"
            f"📊 CTR: {ctr:.2f}% (único {unique_ctr:.2f}%)\n"
            f"💵 CPC: R$ {cpc:.2f}\n"
        )
        if conv > 0 or roas > 0:
            kpis += (
                "\n🎯 KPIs – CONVERSÃO\n"
                f"🎯 Conversões: {conv}\n"
                f"📈 ROAS: {roas:.2f}x\n"
            )

        blocks.append(
            f"{_separator('🎯 CAMPANHA')}\n{name}\n\n"
            f"{_separator('📌 MÉTRICAS')}\n{kpis}\n"
            f"{_separator('🧠 ANÁLISE')}\n{analysis_text}\n"
        )

    final_text = header + summary + "\n\n" + "\n\n".join(blocks)

    return {
        "success": True,
        "type": "daily_consolidated",
        "formatted_comment": final_text
    }


# -------------------------
# WEEKLY (mantido no arquivo; se você usa, chama essa função no Make semanal)
# -------------------------

def resolve_week_range(data_list: list[dict]) -> str:
    dates = []
    for d in data_list or []:
        raw = d.get("report_date")
        if not raw:
            continue
        try:
            dates.append(datetime.strptime(raw, "%Y-%m-%d").date())
        except ValueError:
            continue

    if not dates:
        return "Período não informado (envie report_date em cada item)"

    start = min(dates).strftime("%d/%m/%Y")
    end = max(dates).strftime("%d/%m/%Y")
    return f"{start} a {end}"


def analyze_weekly_metrics(data_list: list) -> dict:
    total_spend = sum(_safe_float(d.get("spend", 0)) for d in data_list)
    total_impressions = sum(_safe_int(d.get("impressions", 0)) for d in data_list)
    total_clicks = sum(_safe_int(d.get("clicks", 0)) for d in data_list)
    total_conversions = sum(_safe_int(d.get("conversions", 0)) for d in data_list)

    avg_ctr = (sum(_safe_float(d.get("ctr", 0)) for d in data_list) / len(data_list)) if data_list else 0
    avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0

    week_range = resolve_week_range(data_list)
    generated_at = datetime.now(TZ).strftime("%d/%m/%Y às %H:%M")

    prompt = f"""Você é um gestor de tráfego pago sênior II. Crie um relatório semanal profissional.

PERÍODO DOS DADOS: {week_range}

MÉTRICAS DA SEMANA:
- Investimento total: R$ {total_spend:.2f}
- Impressões: {total_impressions:,}
- Clicks: {total_clicks}
- CTR médio: {avg_ctr:.2f}%
- CPC médio: R$ {avg_cpc:.2f}
- Conversões: {total_conversions}

FORNEÇA:
1. RESUMO EXECUTIVO (para o cliente)
2. MÉTRICAS FORMATADAS (visual)
3. ANÁLISE E RECOMENDAÇÕES (técnico e acessível)
4. ROTEIRO DE ÁUDIO (1-2 minutos)"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um gestor de tráfego que se comunica de forma clara e profissional."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=2500
        )

        analysis_text = (response.choices[0].message.content or "").strip()

        formatted_comment = (
            "📊 RELATÓRIO SEMANAL – META ADS\n\n"
            f"📅 Dados: {week_range}\n"
            f"⏱️ Gerado em: {generated_at}\n\n"
            f"{_separator('📌 RESUMO DA SEMANA')}\n"
            f"💰 Investimento total: R$ {total_spend:.2f}\n"
            f"👁️ Impressões: {total_impressions:,}\n"
            f"🖱️ Clicks: {total_clicks}\n"
            f"📊 CTR médio: {avg_ctr:.2f}%\n"
            f"💵 CPC médio: R$ {avg_cpc:.2f}\n"
            f"🎯 Conversões: {total_conversions}\n\n"
            f"{_separator('🧠 ANÁLISE')}\n{analysis_text}\n"
        )

        return {"success": True, "type": "weekly", "formatted_comment": formatted_comment}

    except Exception as e:
        return {"success": False, "error": str(e), "formatted_comment": "Erro ao gerar relatório semanal."}


# -------------------------
# Main (testes)
# -------------------------
if __name__ == "__main__":
    test_data = {
        "client_name": "Snob Motel LTDA",
        "report_date": "2025-12-29",
        "campaign_name": "[ENGAJAMENTO] [PERFIL]",
        "objective": "ENGAGEMENT",
        "ad_name": "Reels 01",
        "adset_name": "Público Amplo",
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
        "conversions": "0",
        "conversion_value": "0",
        "results": {"profile_visits": 84, "post_engagements": 430, "link_clicks": 19}
    }

    print(analyze_daily_metrics(test_data)["formatted_comment"])
