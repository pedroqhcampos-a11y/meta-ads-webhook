#!/usr/bin/env python3.11
"""
Meta Ads Analyzer - Análise profissional de métricas com IA
"""

import os
from datetime import datetime
from openai import OpenAI

# Inicializa cliente OpenAI com configuração da Manus
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)


def analyze_daily_metrics(data: dict) -> dict:
    """
    Analisa métricas diárias do Meta Ads e gera relatório profissional
    """
    
    # Extrai métricas principais
    campaign_name = data.get("campaign_name", "")
    ad_name = data.get("ad_name", "")
    adset_name = data.get("adset_name", "")
    
    spend = float(data.get("spend", 0))
    impressions = int(data.get("impressions", 0))
    clicks = int(data.get("clicks", 0))
    unique_clicks = int(data.get("unique_clicks", 0))
    ctr = float(data.get("ctr", 0))
    unique_ctr = float(data.get("unique_ctr", 0))
    cpc = float(data.get("cpc", 0))
    cpm = float(data.get("cpm", 0))
    frequency = float(data.get("frequency", 0))
    conversions = int(data.get("conversions", 0))
    cost_per_conversion = float(data.get("cost_per_conversion", 0)) if conversions > 0 else 0
    conversion_value = float(data.get("conversion_value", 0))
    
    # Calcula ROAS se houver conversões
    roas = conversion_value / spend if spend > 0 and conversion_value > 0 else 0
    
    # Monta prompt para IA
    prompt = f"""Você é um gestor de tráfego pago sênior especializado em Meta Ads. Analise as métricas de acordo com o tipo de campanha (entenda do que se trata os anúncios, campanha, conjunto de anúncios e nicho do cliente antes de dar opinião) abaixo e forneça um relatório profissional e acionável.

MÉTRICAS DA CAMPANHA:
- Campanha: {campaign_name}
- Conjunto de anúncios: {adset_name}
- Anúncio: {ad_name}
- Investimento: R$ {spend:.2f}
- Impressões: {impressions:,}
- Clicks: {clicks} ({unique_clicks} únicos)
- CTR: {ctr:.2f}% (único: {unique_ctr:.2f}%)
- CPC: R$ {cpc:.2f}
- CPM: R$ {cpm:.2f}
- Frequência: {frequency:.2f}
- Conversões: {conversions}
- Custo por conversão: R$ {cost_per_conversion:.2f}
- Valor de conversão: R$ {conversion_value:.2f}
- ROAS: {roas:.2f}x

FORNEÇA UMA ANÁLISE COMPLETA E PROFISSIONAL SEGUINDO ESTA ESTRUTURA:

1. STATUS GERAL: (nessa mesma linha, seja direto e claro, objetivo)

2. ANÁLISE DE PERFORMANCE (visão sobre o desempenho geral)

3. PONTOS POSITIVOS (liste 2-4 pontos específicos com emoji de números, contexto e comparando o mercado de tráfego para o nicho do cliente e o histórico de gastos e retorno da conta do cliente)

4. PONTOS DE ATENÇÃO (liste 2-4 problemas ou riscos identificados, como solucionar de forma prática ou ação que deve ser feita (sugestão) e como pode influenciar o resultado)

5. ANÁLISE DE CRIATIVOS E COPY (baseado no CTR, frequência e engajamento):
   - Avalie se os criativos estão performando bem
   - Sugira melhorias específicas no criativo e/ou copy, se ver necessidade (formato, cor, CTA visual)
   - Sugira melhorias na copy se necess[ario (tom, urgência, benefícios)
   - Indique se precisa de teste A/B e como deve ser feito

6. ANÁLISE DE SEGMENTAÇÃO (baseado no CPM, CPC e frequência):
   - Avalie se o público está correto, quando foi usado um parecido na conta e teve o resultado que você espera, ou como pode ser criado esse público de acordo com essa conta de anuncios e resultados.
   - Sugira ajustes de segmentação se achar viável, sendo claro o que deve ser feito e qual resultado esperado.
   - Indique se há saturação ou oportunidades

7. ANÁLISE DE ORÇAMENTO E ESCALA:
   - Avalie se o orçamento está adequado para a verba mensal do cliente
   - Sugira como escalar (se aplicável)
   - Indique riscos de escala

8. AÇÕES IMEDIATAS (liste 3-5 ações específicas e acionáveis, e como fazer, e quais resultados esperados)

9. AÇÕES DE MÉDIO PRAZO (liste 2-3 ações para os próximos 7 dias, como fazer e quais resultados esperados)

Seja ESPECÍFICO, TÉCNICO e ACIONÁVEL. Use números e dados para embasar suas recomendações. Pense como um gestor que precisa entregar resultados. Deixe esse relatório enxuto, falando somente o necessário, claro e sem rodeios. Deixe de fácil visualização também, use emojis, fala simples, organizado."""

    try:
        # Chama GPT-4 para análise
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um gestor de tráfego pago sênior com 10+ anos de experiência em Meta Ads. Suas análises são diretas, técnicas e focadas em resultados."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        analysis_text = response.choices[0].message.content
        
        # Formata para ClickUp
        formatted_comment = format_daily_comment(
            campaign_name=campaign_name,
            spend=spend,
            impressions=impressions,
            clicks=clicks,
            unique_clicks=unique_clicks,
            ctr=ctr,
            unique_ctr=unique_ctr,
            cpc=cpc,
            cpm=cpm,
            frequency=frequency,
            conversions=conversions,
            cost_per_conversion=cost_per_conversion,
            roas=roas,
            analysis_text=analysis_text
        )
        
        return {
            "success": True,
            "type": "daily",
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
        # Fallback se a IA falhar
        return {
            "success": False,
            "error": str(e),
            "formatted_comment": format_daily_comment_fallback(data)
        }


def format_daily_comment(campaign_name, spend, impressions, clicks, unique_clicks, 
                         ctr, unique_ctr, cpc, cpm, frequency, conversions, 
                         cost_per_conversion, roas, analysis_text):
    """
    Formata comentário diário para ClickUp com análise da IA
    """
    
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    
    # Monta métricas
    metrics_section = f"""Campanha: {campaign_name}

💰 Investimento: R$ {spend:.2f}
👁️ Impressões: {impressions:,}
🖱️ Clicks: {clicks} ({unique_clicks} únicos)
📊 CTR: {ctr:.2f}% (único: {unique_ctr:.2f}%)
💵 CPC: R$ {cpc:.2f}
📢 CPM: R$ {cpm:.2f}
🔄 *Frequência:* {frequency:.2f}"""
    
    if conversions > 0:
        metrics_section += f"""
🎯 *Conversões:* {conversions}
💸 *Custo/Conversão:* R$ {cost_per_conversion:.2f}"""
        if roas > 0:
            metrics_section += f"""
📈 *ROAS:* {roas:.2f}x"""
    
    # Monta comentário completo
    comment = f"""📊 Análise Diária - Meta Ads

*Cliente:* Snob Motel LTDA
*Data:* {date_str}

---

{metrics_section}

---

{analysis_text}"""
    
    return comment


def format_daily_comment_fallback(data):
    """
    Formato fallback caso a IA falhe
    """
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y às %H:%M")
    
    campaign_name = data.get("campaign_name", "0")
    spend = float(data.get("spend", 0))
    impressions = int(data.get("impressions", 0))
    clicks = int(data.get("clicks", 0))
    ctr = float(data.get("ctr", 0))
    cpc = float(data.get("cpc", 0))
    
    return f"""📊 Análise Diária - Meta Ads

*Cliente:* Snob Motel LTDA
*Data:* {date_str}

---

Campanha: {campaign_name}

💰 Investimento: R$ {spend:.2f}
👁️ Impressões: {impressions:,}
🖱️ Clicks: {clicks}
📊 CTR: {ctr:.2f}%
💵 CPC: R$ {cpc:.2f}

---

_Análise detalhada temporariamente indisponível. Métricas coletadas com sucesso._"""


def analyze_weekly_metrics(data_list: list) -> dict:
    """
    Analisa métricas semanais e gera relatório + roteiro de áudio
    """
    
    # Soma métricas da semana
    total_spend = sum(float(d.get("spend", 0)) for d in data_list)
    total_impressions = sum(int(d.get("impressions", 0)) for d in data_list)
    total_clicks = sum(int(d.get("clicks", 0)) for d in data_list)
    total_conversions = sum(int(d.get("conversions", 0)) for d in data_list)
    
    avg_ctr = sum(float(d.get("ctr", 0)) for d in data_list) / len(data_list) if data_list else 0
    avg_cpc = total_spend / total_clicks if total_clicks > 0 else 0
    
    # Monta prompt para IA (relatório semanal)
    prompt = f"""Você é um gestor de tráfego pago sênior II. Crie um relatório semanal profissional para o gestor senior III da conta verificar a sua análise e decidir com base na sua análise e sugestão, o que fazer com as métricas.

MÉTRICAS DA SEMANA:
- Investimento total: R$ {total_spend:.2f}
- Impressões: {total_impressions:,}
- Clicks: {total_clicks}
- CTR médio: {avg_ctr:.2f}%
- CPC médio: R$ {avg_cpc:.2f}
- Conversões: {total_conversions}

FORNEÇA:
1. RESUMO EXECUTIVO (2-3 parágrafos para o cliente)
2. MÉTRICAS FORMATADAS (no estilo que o cliente espera, simples e visual)
3. ANÁLISE E RECOMENDAÇÕES (técnico mas acessível)
4. ROTEIRO DE ÁUDIO (texto que o gestor vai gravar e enviar para o cliente, tom conversacional, 1-2 minutos)"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um gestor de tráfego que se comunica de forma clara e profissional com clientes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        
        analysis_text = response.choices[0].message.content
        
        # Formata para ClickUp
        formatted_comment = format_weekly_comment(
            total_spend=total_spend,
            total_impressions=total_impressions,
            total_clicks=total_clicks,
            avg_ctr=avg_ctr,
            avg_cpc=avg_cpc,
            total_conversions=total_conversions,
            analysis_text=analysis_text
        )
        
        return {
            "success": True,
            "type": "weekly",
            "formatted_comment": formatted_comment
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "formatted_comment": "Erro ao gerar relatório semanal."
        }


def format_weekly_comment(total_spend, total_impressions, total_clicks, 
                          avg_ctr, avg_cpc, total_conversions, analysis_text):
    """
    Formata comentário semanal para ClickUp
    """
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    
    comment = f"""📊 Relatório Semanal - Meta Ads

*Cliente:* Snob Motel LTDA
*Data:* {date_str}

---

*Resumo da Semana*

💰 *Investimento Total:* R$ {total_spend:.2f}
👁️ *Impressões:* {total_impressions:,}
🖱️ *Clicks:* {total_clicks}
📊 *CTR Médio:* {avg_ctr:.2f}%
💵 *CPC Médio:* R$ {avg_cpc:.2f}
🎯 *Conversões:* {total_conversions}

---

{analysis_text}"""
    
    return comment


if __name__ == "__main__":
    # Teste
    test_data = {
        "campaign_name": "Engajamento de vídeos",
        "ad_name": "Vídeo 1",
        "adset_name": "Público Amplo",
        "spend": "10.23",
        "impressions": "4095",
        "clicks": "185",
        "unique_clicks": "173",
        "ctr": "4.52",
        "unique_ctr": "4.64",
        "cpc": "0.055",
        "cpm": "2.50",
        "frequency": "1.10",
        "conversions": "0",
        "cost_per_conversion": "0",
        "conversion_value": "0"
    }
    
    result = analyze_daily_metrics(test_data)
    print(result["formatted_comment"])
