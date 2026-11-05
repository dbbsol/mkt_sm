"""
config/references.py
─────────────────────────────────────────────────────────────────
Guard-rails éticos injetados no prompt da IA. Gatilhos mentais são
usados para tornar o conteúdo mais claro e relevante — nunca para
enganar ou manipular o público.
─────────────────────────────────────────────────────────────────
"""

BASE_ESTRATEGICA = {
    "areas_dominio": [
        "Psicologia do consumo e economia comportamental aplicada a conteúdo",
        "Algoritmos de distribuição das principais redes (retenção, compartilhamento, salvamentos)",
        "Storytelling, copywriting e construção de autoridade",
        "Jornalismo e checagem: separar fato confirmado de especulação",
    ],
    "guardrails": [
        "Nunca inventar fatos, números, datas, nomes ou citações sobre a pauta.",
        "Nunca prometer resultado garantido (ex: 'viralize em 7 dias').",
        "Nunca sugerir falsa urgência, falsa escassez, engajamento falso ou manipulação de métricas.",
        "Gatilho mental é recurso de clareza e relevância, não de enganação: a promessa do conteúdo deve ser cumprida.",
        "Tragédias, luto, crimes, doenças graves e política polarizada exigem cuidado: orientar tom respeitoso ou desaconselhar.",
        "Quando o contexto coletado for insuficiente, dizer isso em vez de preencher com suposição.",
    ],
}


def build_scientific_grounding_block() -> str:
    areas = "\n".join(f"- {a}" for a in BASE_ESTRATEGICA["areas_dominio"])
    guardrails = "\n".join(f"- {g}" for g in BASE_ESTRATEGICA["guardrails"])
    return f"""BASE ESTRATÉGICA A RESPEITAR:
Domínios de conhecimento aplicáveis:
{areas}

Regras inegociáveis de rigor e ética:
{guardrails}
"""
