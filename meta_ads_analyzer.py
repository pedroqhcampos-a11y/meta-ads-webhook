#!/usr/bin/env python3.11
"""
Meta Ads Analyzer - Análise profissional de métricas com IA

✅ Mantém a BASE do seu código original (estrutura, OpenAI client, daily/weekly, ClickUp formatting)
✅ Melhora o DIÁRIO para:
  - entender o objetivo (campo objective + nome da campanha + métricas disponíveis)
  - selecionar KPIs corretos para aquele objetivo (ex.: engajamento sem conversões)
  - sugerir ações com "COMO FAZER" (passo a passo curto)
✅ Suporta 2 modos no DIÁRIO:
  - analyze_daily_metrics(data): 1 campanha -> 1 comentário
  - analyze_daily_metrics_consolidated(payload): várias campanhas -> 1 comentário (blocos por campanha)
✅ Datas:
  - Dados referentes a: report_date (YYYY-MM-DD vindo do Make)
  - Relatório gerado em: timestamp local (America/Sao_Paulo)

Recomendação (Make):
- Enviar "report_date": "YYYY-MM-DD" (ontem)
- Para cada campanha, enviar:
  - campaign_name, spend, impressions, clicks, ctr, cpc, cpm, frequency etc.
  - opcional: objective (ex.: "ENGAGEMENT", "TRAFFIC", "MESSAGES", "CONVERSIONS", "LEADS")
  - opcional: results (dict com métricas específicas do objetivo), ex:
    {
      "messages_started": 18,
      "link_clicks": 42,
      "profile_visits": 120,
      "post_engagements": 980,
      "leads": 7,
      "purchases": 2,
      "purchase_value": 540.00
    }
"""

import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

# Timezone padrão (Brasil/São Paulo)
TZ = ZoneInfo("America/Sao_Paulo")

# Inicializa cliente OpenAI com configuração da Manus
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)


# -------------------------
# Helpers (datas e parsing)
# -------------------------

def resolve_report_dates(data: dict) -> tuple[str, str]:
    """
    - report_date: data dos dados (Meta / Make) esperada como YYYY-MM-DD
    - generated_at: data e hora de geração do relatório (execução do script)
    """
    report_date_raw = data.get("report_date")

    if report_date_raw:
        try:
            report_date = datetime.strptime(report_date_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            report_date = f"Formato inválido: {report_date_raw} (esperado YYYY-MM-DD)"
    else:
        report_date = "Data não informada (envie 'report_date' no Make: YYYY-MM-DD)"

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
    """
    Inferência simples e robusta:
    1) objective_field se vier
    2) tokens no nome da campanha
    3) chaves em results
    """
    if objective_field:
        return str(objective_field).strip().upper()

    name = (campaign_name or "").upper()

    # Pelo naming convention
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

    # Por resultados presentes
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
# PROMPT (Daily inteligente)
# -------------------------

def build_daily_prompt(data: dict) -> str:
    """
    Diário enxuto + IA escolhe KPIs conforme objetivo e métricas disponíveis.
    Também exige "COMO FAZER" nas ações.
    """
    campaign_name = data.get("campaign_name", "")
    ad_name = data.get("ad_name", "")
    adset_name = data.get("adset_name", "")

    spend = _safe_float(data.get("spend", 0))
    impressions = _safe_int(data.get("impressions", 0))
    reach = _safe_int(data.get("reach", 0))  # opcional
    clicks = _safe_int(data.get("clicks", 0))
    unique_clicks = _safe_int(data.get("unique_clicks", 0))
    ctr = _safe_float(data.get("ctr", 0))
    unique_ctr = _safe_float(data.get("unique_ctr", 0))
    cpc = _safe_float(data.get("cpc", 0))
    cpm = _safe_float(data.get("cpm", 0))
    frequency = _safe_float(data.get("frequency", 0))

    # Seus campos clássicos continuam existindo (conversões/valor) — mas não “força” uso se objetivo não for isso
    conversions = _safe_int(data.get("conversions", 0))
    conversion_value = _safe_float(data.get("conversion_value", 0))
    roas = _compute_roas(spend, conversion_value)

    objective_field = (data.get("objective") or "").strip()
    results = data.get("results", {}) or {}

    inferred_obj = _infer_objective(campaign_name, objective_field, results)

    # Mostra results como JSON para IA escolher KPI correto.
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
# DAILY (Single Campaign)
# -------------------------

def analyze_daily_metrics(data: dict) -> dict:
    """
    Analisa métricas diárias (1 campanha) e gera comentário profissional (interno) para ClickUp.
    """
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
            "metrics": {
                "spend": spend,
                "impressions": impressions,
                "clicks": clicks,
                "ctr": ctr,
                "cpc": cpc
            },
            "analysis": analysis_text,
            "formatted_comment": formatted_comment
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "formatted_comment": format_daily_comment_fallback(data)
        }


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
    """
    Formata comentário diário para ClickUp (visual bonito).
    """
    # Mantém o cliente no texto (você pode parametrizar se quiser)
    client_name = data.get("client_name", "Snob Motel LTDA")

    kpis = f"""**KPIs (base)**
• 💰 **Spend:** R$ {spend:.2f}  
• 👁️ **Impressões:** {impressions:,}  
• 📣 **Alcance:** {reach:,}  
• 📢 **CPM:** R$ {cpm:.2f}  
• 🔄 **Frequência:** {frequency:.2f}

**KPIs (clique)**
• 🖱️ **Clicks:** {clicks} (**{unique_clicks}** únicos)  
• 📊 **CTR:** {ctr:.2f}% (**único:** {unique_ctr:.2f}%)  
• 💵 **CPC:** R$ {cpc:.2f}"""

    # Conversão/ROAS só como apoio (não necessariamente KPI principal)
    if conversions > 0 or roas > 0:
        kpis += f"""

**KPIs (conversão)**
• 🎯 **Conversões:** {conversions}  
• 📈 **ROAS:** {roas:.2f}x"""

    comment = f"""📊 **ANÁLISE DIÁRIA – META ADS (INTERNO)**

📅 **Dados referentes a:** {report_date}  
⏱️ **Relatório gerado em:** {generated_at}

---

### 📌 **Campanha:** **{campaign_name}**

{kpis}

---

{analysis_text}"""

    return comment


def format_daily_comment_fallback(data: dict) -> str:
    """
    Formato fallback caso a IA falhe (visual bonito e com datas corretas)
    """
    report_date, generated_at = resolve_report_dates(data)

    campaign_name = data.get("campaign_name", "Campanha sem nome")
    spend = _safe_float(data.get("spend", 0))
    impressions = _safe_int(data.get("impressions", 0))
    clicks = _safe_int(data.get("clicks", 0))
    ctr = _safe_float(data.get("ctr", 0))
    cpc = _safe_float(data.get("cpc", 0))
    cpm = _safe_float(data.get("cpm", 0))
    frequency = _safe_float(data.get("frequency", 0))

    return f"""📊 **ANÁLISE DIÁRIA – META ADS (INTERNO)**

📅 **Dados referentes a:** {report_date}  
⏱️ **Relatório gerado em:** {generated_at}

---

### 📌 **Campanha:** **{campaign_name}**

**KPIs (base)**
• 💰 **Spend:** R$ {spend:.2f}  
• 👁️ **Impressões:** {impressions:,}  
• 📢 **CPM:** R$ {cpm:.2f}  
• 🔄 **Frequência:** {frequency:.2f}

**KPIs (clique)**
• 🖱️ **Clicks:** {clicks}  
• 📊 **CTR:** {ctr:.2f}%  
• 💵 **CPC:** R$ {cpc:.2f}

---

_Análise IA indisponível. Métricas coletadas com sucesso._"""


# -------------------------
# DAILY (Consolidated)
# -------------------------

def analyze_daily_metrics_consolidated(payload: dict) -> dict:
    """
    Analisa VÁRIAS campanhas e devolve UMA mensagem consolidada.

    Espera payload no formato:
    {
      "report_date": "YYYY-MM-DD",
      "client_name": "Snob Motel LTDA" (opcional),
      "campaigns": [ {campanha1}, {campanha2}, ... ]
    }

    Cada item em campaigns é o mesmo "data" do analyze_daily_metrics.
    """
    report_date, generated_at = resolve_report_dates(payload)
    campaigns = payload.get("campaigns") or []
    client_name = payload.get("client_name", "Snob Motel LTDA")

    if not isinstance(campaigns, list) or len(campaigns) == 0:
        return {
            "success": False,
            "error": "Payload inválido: envie uma lista em 'campaigns'.",
            "formatted_comment": f"""📊 **ANÁLISE DIÁRIA – META ADS (INTERNO)**

📅 **Dados referentes a:** {report_date}  
⏱️ **Relatório gerado em:** {generated_at}

---

Nenhuma campanha enviada em **campaigns**."""
        }

    # Resumo macro do dia (numérico)
    total_spend = sum(_safe_float(c.get("spend", 0)) for c in campaigns)
    total_impressions = sum(_safe_int(c.get("impressions", 0)) for c in campaigns)
    total_reach = sum(_safe_int(c.get("reach", 0)) for c in campaigns)
    total_clicks = sum(_safe_int(c.get("clicks", 0)) for c in campaigns)

    # Conversões/valor podem ser irrelevantes em ENGAGEMENT/MESSAGES; aqui é só macro se existirem
    total_conversions = sum(_safe_int(c.get("conversions", 0)) for c in campaigns)
    total_value = sum(_safe_float(c.get("conversion_value", 0)) for c in campaigns)
    total_roas = _compute_roas(total_spend, total_value)

    blocks = []
    for c in campaigns:
        # herda report_date no item se não existir
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
            analysis_text = """🟡 PONTOS A MELHORAR:
- IA indisponível.

🚨 AÇÕES IMEDIATAS (COMO FAZER):
- Nenhuma ação imediata necessária."""

        name = c.get("campaign_name", "Campanha sem nome")
        spend = _safe_float(c.get("spend", 0))
        impressions = _safe_int(c.get("impressions", 0))
        reach = _safe_int(c.get("reach", 0))
        clicks = _safe_int(c.get("clicks", 0))
        ctr = _safe_float(c.get("ctr", 0))
        cpc = _safe_float(c.get("cpc", 0))
        cpm = _safe_float(c.get("cpm", 0))
        freq = _safe_float(c.get("frequency", 0))

        conv = _safe_int(c.get("conversions", 0))
        val = _safe_float(c.get("conversion_value", 0))
        roas = _compute_roas(spend, val)

        block_kpis = f"""**KPIs (base)**
• 💰 **Spend:** R$ {spend:.2f}  
• 👁️ **Impressões:** {impressions:,}  
• 📣 **Alcance:** {reach:,}  
• 📢 **CPM:** R$ {cpm:.2f}  
• 🔄 **Frequência:** {freq:.2f}

**KPIs (clique)**
• 🖱️ **Clicks:** {clicks}  
• 📊 **CTR:** {ctr:.2f}%  
• 💵 **CPC:** R$ {cpc:.2f}"""

        if conv > 0 or roas > 0:
            block_kpis += f"""

**KPIs (conversão)**
• 🎯 **Conversões:** {conv}  
• 📈 **ROAS:** {roas:.2f}x"""

        blocks.append(f"""### 🔹 **{name}**

{block_kpis}

{analysis_text}""")

    macro = f"""## 📌 **RESUMO DO DIA**
• 💰 **Spend total:** R$ {total_spend:.2f}  
• 👁️ **Impressões:** {total_impressions:,}  
• 📣 **Alcance:** {total_reach:,}  
• 🖱️ **Clicks:** {total_clicks}"""

    if total_conversions > 0 or total_roas > 0:
        macro += f"""  
• 🎯 **Conversões:** {total_conversions}  
• 📈 **ROAS total:** {total_roas:.2f}x"""

    consolidated_comment = f"""📊 **ANÁLISE DIÁRIA – META ADS (INTERNO) — CONSOLIDADO**

📅 **Dados referentes a:** {report_date}  
⏱️ **Relatório gerado em:** {generated_at}

---

{macro}

---

## 🎯 **CAMPANHAS**
""" + "\n\n---\n\n".join(blocks)

    return {
        "success": True,
        "type": "daily_consolidated",
        "formatted_comment": consolidated_comment
    }


# -------------------------
# WEEKLY (mantido do original, com datas melhores)
# -------------------------

def resolve_week_range(data_list: list[dict]) -> str:
    """
    Usa 'report_date' (YYYY-MM-DD) em cada item para descobrir intervalo.
    """
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
        return "Período não informado (envie 'report_date' em cada item)"

    start = min(dates).strftime("%d/%m/%Y")
    end = max(dates).strftime("%d/%m/%Y")
    return f"{start} a {end}"


def analyze_weekly_metrics(data_list: list) -> dict:
    """
    Analisa métricas semanais e gera relatório + roteiro de áudio
    (mantém base do seu original; ajustes só de data e visual)
    """
    total_spend = sum(_safe_float(d.get("spend", 0)) for d in data_list)
    total_impressions = sum(_safe_int(d.get("impressions", 0)) for d in data_list)
    total_clicks = sum(_safe_int(d.get("clicks", 0)) for d in data_list)
    total_conversions = sum(_safe_int(d.get("conversions", 0)) for d in data_list)

    avg_ctr = (sum(_safe_float(d.get("ctr", 0)) for d in data_list) / len(data_list)) if data_list else 0
    avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0

    week_range = resolve_week_range(data_list)
    generated_at = datetime.now(TZ).strftime("%d/%m/%Y às %H:%M")

    prompt = f"""Você é um gestor de tráfego pago sênior II. Crie um relatório semanal profissional para o gestor senior III verificar e decidir.

PERÍODO DOS DADOS: {week_range}

MÉTRICAS DA SEMANA:
- Investimento total: R$ {total_spend:.2f}
- Impressões: {total_impressions:,}
- Clicks: {total_clicks}
- CTR médio: {avg_ctr:.2f}%
- CPC médio: R$ {avg_cpc:.2f}
- Conversões: {total_conversions}

FORNEÇA:
1. RESUMO EXECUTIVO (2-3 parágrafos para o cliente)
2. MÉTRICAS FORMATADAS (simples e visual)
3. ANÁLISE E RECOMENDAÇÕES (técnico mas acessível)
4. ROTEIRO DE ÁUDIO (tom conversacional, 1-2 minutos)"""

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

        formatted_comment = format_weekly_comment(
            week_range=week_range,
            generated_at=generated_at,
            total_spend=total_spend,
            total_impressions=total_impressions,
            total_clicks=total_clicks,
            avg_ctr=avg_ctr,
            avg_cpc=avg_cpc,
            total_conversions=total_conversions,
            analysis_text=analysis_text
        )

        return {"success": True, "type": "weekly", "formatted_comment": formatted_comment}

    except Exception as e:
        return {"success": False, "error": str(e), "formatted_comment": "Erro ao gerar relatório semanal."}


def format_weekly_comment(
    week_range: str,
    generated_at: str,
    total_spend: float,
    total_impressions: int,
    total_clicks: int,
    avg_ctr: float,
    avg_cpc: float,
    total_conversions: int,
    analysis_text: str
) -> str:
    return f"""📊 **RELATÓRIO SEMANAL – META ADS**

📅 **Dados referentes a:** {week_range}  
⏱️ **Relatório gerado em:** {generated_at}

---

## 📌 **RESUMO DA SEMANA**
• 💰 **Investimento total:** R$ {total_spend:.2f}  
• 👁️ **Impressões:** {total_impressions:,}  
• 🖱️ **Clicks:** {total_clicks}  
• 📊 **CTR médio:** {avg_ctr:.2f}%  
• 💵 **CPC médio:** R$ {avg_cpc:.2f}  
• 🎯 **Conversões:** {total_conversions}

---

{analysis_text}"""


# -------------------------
# Main (testes)
# -------------------------

if __name__ == "__main__":
    # Teste: diário single (engajamento, sem conversões, com resultados úteis)
    test_data = {
        "client_name": "Snob Motel LTDA",
        "report_date": "2025-12-29",
        "campaign_name": "[ENGAJAMENTO] [PERFIL]",
        "objective": "ENGAGEMENT",
        "ad_name": "Reels 01",
        "adset_name": "Público Amplo",
        "spend": "10.23",
        "impressions": "4095",
        "reach": "3200",
        "clicks": "185",
        "unique_clicks": "173",
        "ctr": "4.52",
        "unique_ctr": "4.64",
        "cpc": "0.055",
        "cpm": "2.50",
        "frequency": "1.10",
        "conversions": "0",
        "conversion_value": "0",
        "results": {
            "profile_visits": 84,
            "post_engagements": 430,
            "link_clicks": 19
        }
    }

    result = analyze_daily_metrics(test_data)
    print(result["formatted_comment"])

    # Teste: diário consolidado (2 campanhas)
    payload = {
        "client_name": "Snob Motel LTDA",
        "report_date": "2025-12-29",
        "campaigns": [
            test_data,
            {
                "campaign_name": "[MENSAGEM] [WHATSAPP]",
                "objective": "MESSAGES",
                "spend": "30.00",
                "impressions": "9000",
                "reach": "6500",
                "clicks": "210",
                "unique_clicks": "190",
                "ctr": "2.33",
                "unique_ctr": "2.11",
                "cpc": "0.14",
                "cpm": "3.33",
                "frequency": "1.45",
                "conversions": "0",
                "conversion_value": "0",
                "results": {
                    "messages_started": 18,
                    "link_clicks": 42
                }
            }
        ]
    }

    result2 = analyze_daily_metrics_consolidated(payload)
    print(result2["formatted_comment"])
