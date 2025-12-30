#!/usr/bin/env python3.11
"""
Meta Ads Analyzer - Analisa métricas do Meta Ads e gera insights com IA
"""

import json
import os
from datetime import datetime
from openai import OpenAI

# Inicializa cliente OpenAI
client = OpenAI()

def analyze_daily_metrics(data: dict) -> dict:
    """
    Analisa métricas diárias e gera insights com IA
    
    Args:
        data: Dados do Meta Ads recebidos do webhook
        
    Returns:
        dict com análise formatada
    """
    
    # Extrai métricas principais
    metrics = {
        "account_name": data.get("account_name", "N/A"),
        "clicks": int(data.get("clicks", 0)),
        "impressions": int(data.get("impressions", 0)),
        "spend": float(data.get("spend", 0)),
        "cpc": float(data.get("cpc", 0)),
        "cpm": float(data.get("cpm", 0)),
        "ctr": float(data.get("ctr", 0)),
        "frequency": float(data.get("frequency", 0)),
        "unique_clicks": int(data.get("unique_clicks", 0)),
        "unique_ctr": float(data.get("unique_ctr", 0)),
        "objective": data.get("objective", "N/A"),
        "date_start": data.get("date_start", ""),
        "date_stop": data.get("date_stop", "")
    }
    
    # Prompt para análise diária
    prompt = f"""Você é um especialista em Meta Ads e análise de performance de campanhas. 

Analise as seguintes métricas de uma campanha do Meta Ads e forneça insights acionáveis:

**Métricas do dia:**
- Conta: {metrics['account_name']}
- Investimento: R$ {metrics['spend']:.2f}
- Impressões: {metrics['impressions']:,}
- Clicks: {metrics['clicks']}
- Clicks únicos: {metrics['unique_clicks']}
- CTR: {metrics['ctr']:.2f}%
- CTR único: {metrics['unique_ctr']:.2f}%
- CPC: R$ {metrics['cpc']:.2f}
- CPM: R$ {metrics['cpm']:.2f}
- Frequência: {metrics['frequency']:.2f}
- Objetivo: {metrics['objective']}

**Sua análise deve incluir:**

1. **Resumo de Performance**: Como está a campanha hoje? (Boa, Regular, Precisa melhorar)

2. **Análise de Métricas**:
   - O CTR está bom para o objetivo da campanha?
   - O CPC está competitivo?
   - A frequência está adequada ou há saturação?
   - As impressões estão gerando engajamento suficiente?

3. **Pontos de Atenção**:
   - Identifique métricas que precisam de atenção imediata
   - Sinalize possíveis problemas (ex: CTR baixo, CPC alto, frequência alta)

4. **Sugestões de Otimização**:
   - O que deve ser testado/mudado hoje?
   - Sugestões para criativos, copys, segmentação, orçamento
   - Ações prioritárias para melhorar resultado e reduzir custo

5. **Próximos Passos**:
   - O que fazer nas próximas horas/dia?

**Formato da resposta:**
Use markdown com emojis para facilitar leitura. Seja direto e acionável.
Foque em RESULTADOS e FATURAMENTO do cliente, não apenas em métricas de vaidade.
"""

    # Chama GPT-4 para análise
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Você é um especialista em Meta Ads focado em resultados e ROI."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    
    analysis = response.choices[0].message.content
    
    # Formata resultado
    result = {
        "type": "daily",
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "metrics": metrics,
        "analysis": analysis,
        "formatted_comment": format_daily_comment(metrics, analysis)
    }
    
    return result


def format_daily_comment(metrics: dict, analysis: str) -> str:
    """
    Formata comentário para o ClickUp (análise diária)
    """
    comment = f"""# 📊 Análise Diária - Meta Ads

**Data**: {datetime.now().strftime("%d/%m/%Y às %H:%M")}
**Cliente**: {metrics['account_name']}

---

## 📈 Métricas do Dia

💵 **Investimento**: R$ {metrics['spend']:.2f}
👁️ **Impressões**: {metrics['impressions']:,}
🖱️ **Clicks**: {metrics['clicks']} ({metrics['unique_clicks']} únicos)
📊 **CTR**: {metrics['ctr']:.2f}% (único: {metrics['unique_ctr']:.2f}%)
💰 **CPC**: R$ {metrics['cpc']:.2f}
📢 **CPM**: R$ {metrics['cpm']:.2f}
🔄 **Frequência**: {metrics['frequency']:.2f}

---

## 🤖 Análise com IA

{analysis}

---

*Análise gerada automaticamente por IA*
"""
    return comment


def analyze_weekly_metrics(data_list: list) -> dict:
    """
    Analisa métricas semanais e gera relatório completo
    
    Args:
        data_list: Lista de dados dos últimos 7 dias
        
    Returns:
        dict com análise semanal formatada
    """
    
    # Agrega métricas da semana
    total_spend = sum(float(d.get("spend", 0)) for d in data_list)
    total_impressions = sum(int(d.get("impressions", 0)) for d in data_list)
    total_clicks = sum(int(d.get("clicks", 0)) for d in data_list)
    avg_ctr = sum(float(d.get("ctr", 0)) for d in data_list) / len(data_list) if data_list else 0
    avg_cpc = sum(float(d.get("cpc", 0)) for d in data_list) / len(data_list) if data_list else 0
    
    # Prompt para análise semanal
    prompt = f"""Você é um especialista em Meta Ads e precisa criar um relatório semanal para enviar ao cliente.

**Métricas da Semana:**
- Investimento Total: R$ {total_spend:.2f}
- Impressões: {total_impressions:,}
- Clicks: {total_clicks}
- CTR Médio: {avg_ctr:.2f}%
- CPC Médio: R$ {avg_cpc:.2f}

**Crie um relatório que inclua:**

1. **Resumo Executivo**: Como foi a semana em termos de resultados?

2. **Métricas Formatadas**: Organize as métricas de forma clara para o cliente (use o formato que já foi definido)

3. **Roteiro de Áudio**: Escreva um roteiro de 1-2 minutos para gravar um áudio explicando os resultados da semana de forma natural e consultiva

4. **Análise e Insights**: O que funcionou bem? O que precisa melhorar?

5. **Recomendações**: Sugestões de mudanças e otimizações para a próxima semana

**Formato:**
Use markdown, seja claro e consultivo. Foque em RESULTADOS para o negócio do cliente.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Você é um consultor de marketing digital especializado em Meta Ads."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    analysis = response.choices[0].message.content
    
    result = {
        "type": "weekly",
        "period": f"{data_list[0].get('date_start', '')} a {data_list[-1].get('date_stop', '')}",
        "total_spend": total_spend,
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "avg_ctr": avg_ctr,
        "avg_cpc": avg_cpc,
        "analysis": analysis,
        "formatted_comment": format_weekly_comment(total_spend, total_impressions, total_clicks, avg_ctr, avg_cpc, analysis)
    }
    
    return result


def format_weekly_comment(spend, impressions, clicks, ctr, cpc, analysis):
    """
    Formata comentário semanal para o ClickUp
    """
    comment = f"""# 📊 Relatório Semanal - Meta Ads

**Período**: Última semana
**Data do Relatório**: {datetime.now().strftime("%d/%m/%Y")}

---

## 📈 Métricas da Semana

💵 **Investimento Total**: R$ {spend:.2f}
👁️ **Impressões**: {impressions:,}
🖱️ **Clicks**: {clicks}
📊 **CTR Médio**: {ctr:.2f}%
💰 **CPC Médio**: R$ {cpc:.2f}

---

## 🤖 Análise Completa

{analysis}

---

*Relatório gerado automaticamente por IA*
"""
    return comment


if __name__ == "__main__":
    # Teste com dados de exemplo
    test_data = {
        "account_name": "CA - Snob Motel",
        "clicks": "185",
        "cpc": "0.055297",
        "cpm": "2.498169",
        "ctr": "4.517705",
        "frequency": "1.098444",
        "impressions": "4095",
        "objective": "MULTIPLE",
        "spend": "10.23",
        "unique_clicks": "173",
        "unique_ctr": "4.640558"
    }
    
    print("Testando análise diária...")
    result = analyze_daily_metrics(test_data)
    print(result["formatted_comment"])
