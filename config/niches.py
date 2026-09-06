"""
config/niches.py
─────────────────────────────────────────────────────────────────
BANCO DE NICHOS — camada de configuração que torna o sistema
replicável para qualquer profissão sem tocar em core/.

Esta instância está configurada para profissionais de Social Media,
Marketing Digital e Estratégia de Posicionamento (mkt_sm). Para
clonar de volta pro nicho de nutrição (ou qualquer outro), basta
trocar PROFISSIONAL_ATIVO e/ou completar outra entrada abaixo.
─────────────────────────────────────────────────────────────────
"""

PROFISSIONAL_ATIVO = "social_media_marketing"

PROFISSOES = {
    "social_media_marketing": {
        "nome_exibicao": "Social Media & Marketing Digital",
        "artigo": "o(a)",
        "plural": "profissionais de marketing",
        "cta_agendamento": "agendar uma consultoria estratégica",
        "unidade_atendimento": "consultoria",
        # Paleta dark + verde escuro premium
        "cor_marca_primaria": "#0E3B2E",
        "cor_marca_secundaria": "#04120D",
        "cor_destaque": "#4CBE93",
        "sub_nichos": {
            "gestao_de_trafego": {
                "emoji": "📈",
                "dores": [
                    "custo por lead subindo", "fadiga de criativo", "ROAS instável",
                    "cliente não entende o funil", "atribuição de conversão confusa",
                ],
                "publico_tipico": "donos de pequenas e médias empresas investindo em anúncios",
                "linguagem": "técnica, orientada a dado, direta ao ponto",
            },
            "gestao_de_redes_sociais": {
                "emoji": "📱",
                "dores": [
                    "engajamento caindo", "falta de tempo pra postar com consistência",
                    "cliente pedindo resultado de vendas direto de conteúdo orgânico",
                    "algoritmo mudando toda hora",
                ],
                "publico_tipico": "pequenos negócios e criadores de conteúdo",
                "linguagem": "prática, atualizada, sem enrolação",
            },
            "branding_e_posicionamento": {
                "emoji": "🎯",
                "dores": [
                    "marca sem diferenciação clara", "concorrência no preço",
                    "audiência não lembra da marca", "identidade visual inconsistente",
                ],
                "publico_tipico": "empreendedores construindo marca pessoal ou de negócio",
                "linguagem": "estratégica, conceitual, com storytelling",
            },
            "growth_e_funil": {
                "emoji": "🚀",
                "dores": [
                    "topo de funil cheio, fundo vazio", "taxa de conversão baixa",
                    "CAC maior que LTV", "dependência de um único canal de aquisição",
                ],
                "publico_tipico": "founders e times de marketing de startups/negócios digitais",
                "linguagem": "orientada a métricas, testes e experimentação",
            },
            "marca_pessoal": {
                "emoji": "👤",
                "dores": [
                    "medo de aparecer", "não saber por onde começar a criar conteúdo",
                    "audiência pequena mas quer monetizar", "síndrome do impostor pra postar",
                ],
                "publico_tipico": "especialistas, consultores e profissionais liberais",
                "linguagem": "encorajadora, mas sem papo motivacional vazio",
            },
            "conteudo_e_copywriting": {
                "emoji": "✍️",
                "dores": [
                    "bloqueio criativo", "conteúdo genérico que não converte",
                    "dificuldade de encontrar ângulo diferente pra tema saturado",
                ],
                "publico_tipico": "criadores de conteúdo e times de marketing de conteúdo",
                "linguagem": "criativa, tática, cheia de exemplos concretos",
            },
        },
        "objetivos_campanha": {
            "atrair_seguidores": "Crescer alcance e atrair audiência qualificada",
            "gerar_autoridade": "Posicionar como referência técnica no nicho",
            "vender_consultas": "Converter audiência em contratos/consultorias",
            "educar_audiencia": "Nutrir a audiência com educação estratégica de qualidade",
            "fortalecer_marca_pessoal": "Construir identidade de marca reconhecível e memorável",
        },
    },

    # ─── Esqueleto original de nutrição, mantido pra referência de replicação ───
    "nutricionista": {
        "nome_exibicao": "Nutricionista",
        "artigo": "a",
        "plural": "nutricionistas",
        "cta_agendamento": "agendar uma consulta",
        "unidade_atendimento": "consulta",
        "cor_marca_primaria": "#0E3B2E",
        "cor_marca_secundaria": "#04120D",
        "cor_destaque": "#4CBE93",
        "sub_nichos": {
            "emagrecimento": {"emoji": "⚖️", "dores": ["efeito sanfona", "compulsão alimentar", "dietas restritivas"], "publico_tipico": "adultos 25-45 anos", "linguagem": "acolhedora"},
        },
        "objetivos_campanha": {
            "atrair_seguidores": "Crescer alcance",
            "gerar_autoridade": "Posicionar como referência",
            "vender_consultas": "Converter em agendamentos",
            "educar_audiencia": "Educação nutricional",
            "fortalecer_marca_pessoal": "Marca pessoal",
        },
    },
}


def get_profissao_ativa() -> dict:
    return PROFISSOES[PROFISSIONAL_ATIVO]


def get_sub_nichos() -> dict:
    return get_profissao_ativa()["sub_nichos"]


def get_objetivos_campanha() -> dict:
    return get_profissao_ativa()["objetivos_campanha"]