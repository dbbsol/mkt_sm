"""
config/references.py
─────────────────────────────────────────────────────────────────
Base de conhecimento/guard-rails éticos injetados no prompt da IA.
Para o nicho de marketing/social media, o equivalente ao "rigor
científico" da versão nutricionista é o rigor estratégico + ético:
nada de promessa de resultado garantido, growth hacking antiético,
ou manipulação psicológica agressiva.
─────────────────────────────────────────────────────────────────
"""

BASE_ESTRATEGICA_MARKETING = {
    "areas_dominio": [
        "Marketing digital e mídia paga (funil, atribuição, otimização de campanhas)",
        "Gestão de redes sociais e algoritmos de distribuição de conteúdo",
        "Branding, posicionamento e arquitetura de marca",
        "Growth marketing e experimentação (testes A/B, funis, retenção)",
        "Copywriting e storytelling de marca",
        "Comportamento do consumidor e economia comportamental aplicada a marketing",
    ],
    "referencias_consolidadas": [
        "Frameworks consolidados de funil (AARRR, funil de conteúdo, jornada do cliente)",
        "Boas práticas documentadas por cada plataforma (Meta, Google, TikTok, LinkedIn) para anunciantes e criadores",
        "Literatura consolidada de branding e posicionamento (diferenciação, arquitetura de marca)",
        "Metodologias de growth amplamente documentadas (North Star Metric, funil pirata, testes controlados)",
    ],
    "guardrails": [
        "Nunca prometer resultado garantido (ex: 'triplique seu faturamento em 30 dias').",
        "Nunca sugerir growth hacking antiético (bots, engajamento falso, manipulação de métricas).",
        "Nunca recomendar dark patterns manipulativos (falsa urgência/escassez fabricada, cobrança disfarçada).",
        "Diferenciar claramente estratégia validada de tendência passageira sem lastro.",
        "Sempre contextualizar que resultados variam conforme orçamento, nicho e execução.",
        "Basear-se em sinais e frameworks reconhecidos do mercado, não em achismo ou opinião isolada.",
        "Evitar sensacionalismo de 'fórmula mágica' — marketing eficaz é estratégia + consistência, não truque único.",
    ],
}


def build_scientific_grounding_block() -> str:
    """
    Monta o bloco de texto injetado no prompt da IA para ancorar a
    resposta em prática de mercado consolidada, sem citações forjadas.
    """
    areas = "\n".join(f"- {a}" for a in BASE_ESTRATEGICA_MARKETING["areas_dominio"])
    guardrails = "\n".join(f"- {g}" for g in BASE_ESTRATEGICA_MARKETING["guardrails"])
    return f"""BASE ESTRATÉGICA A RESPEITAR (não cite fontes específicas, apenas fundamente-se nelas):
Domínios de conhecimento aplicáveis:
{areas}

Regras inegociáveis de rigor estratégico e ética de marketing:
{guardrails}
"""