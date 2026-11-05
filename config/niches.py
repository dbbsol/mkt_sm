"""
config/niches.py
─────────────────────────────────────────────────────────────────
Nichos macro do mercado + opções de tom de voz e rede social.

Para ADICIONAR um nicho, basta incluir uma linha em _NICHOS_RAW:
    (nome, emoji, [palavras-chave], editoria_google_news)

editoria_google_news: BUSINESS | TECHNOLOGY | HEALTH | SCIENCE |
                      ENTERTAINMENT | SPORTS | NATION | WORLD
─────────────────────────────────────────────────────────────────
"""

_NICHOS_RAW = [
    ("Negócios & Empreendedorismo", "🏢", ["negócios", "empreendedorismo", "startups", "liderança", "gestão", "pequenas empresas"], "BUSINESS"),
    ("Marketing & Vendas", "📣", ["marketing", "vendas", "tráfego pago", "redes sociais", "publicidade", "branding"], "BUSINESS"),
    ("Finanças & Investimentos", "📈", ["finanças", "investimentos", "bolsa de valores", "juros", "dólar", "criptomoedas"], "BUSINESS"),
    ("Tecnologia & IA", "🤖", ["tecnologia", "inteligência artificial", "software", "aplicativos", "automação", "big tech"], "TECHNOLOGY"),
    ("Saúde & Medicina", "🩺", ["saúde", "medicina", "médicos", "hospital", "tratamento", "doenças"], "HEALTH"),
    ("Bem-estar, Nutrição & Fitness", "💪", ["fitness", "treino", "academia", "nutrição", "emagrecimento", "bem-estar"], "HEALTH"),
    ("Saúde Mental & Psicologia", "🧠", ["psicologia", "terapia", "saúde mental", "ansiedade", "autoconhecimento", "psicanálise"], "HEALTH"),
    ("Beleza & Estética", "💄", ["beleza", "estética", "skincare", "cabelo", "maquiagem", "cosméticos"], "ENTERTAINMENT"),
    ("Moda & Lifestyle", "👗", ["moda", "estilo", "lifestyle", "tendências fashion", "look", "luxo"], "ENTERTAINMENT"),
    ("Gastronomia & Alimentação", "🍽️", ["gastronomia", "receitas", "restaurantes", "culinária", "chef", "alimentação"], "ENTERTAINMENT"),
    ("Educação & Carreira", "🎓", ["educação", "carreira", "concursos", "enem", "faculdade", "mercado de trabalho"], "NATION"),
    ("Direito & Jurídico", "⚖️", ["direito", "justiça", "STF", "advocacia", "legislação", "LGPD"], "NATION"),
    ("Imóveis & Construção", "🏠", ["imóveis", "construção civil", "financiamento imobiliário", "aluguel", "incorporadoras"], "BUSINESS"),
    ("Arquitetura, Decoração & Casa", "🛋️", ["decoração", "arquitetura", "design de interiores", "reforma", "casa"], "ENTERTAINMENT"),
    ("Automotivo & Mobilidade", "🚗", ["carros", "automóveis", "carros elétricos", "motos", "mobilidade", "combustível"], "BUSINESS"),
    ("Pets & Animais", "🐾", ["pets", "animais", "cachorro", "gato", "veterinário", "adoção"], "ENTERTAINMENT"),
    ("Viagem & Turismo", "✈️", ["viagem", "turismo", "destinos", "passagens aéreas", "hotéis", "férias"], "ENTERTAINMENT"),
    ("Arte, Design & Criatividade", "🎨", ["arte", "design", "fotografia", "ilustração", "criatividade", "exposição"], "ENTERTAINMENT"),
    ("Esportes", "⚽", ["esporte", "futebol", "atletas", "campeonato", "olimpíadas", "treino"], "SPORTS"),
    ("Games & Cultura Geek", "🎮", ["games", "jogos", "streaming", "esports", "cultura geek", "anime"], "TECHNOLOGY"),
    ("Música, Cinema & Entretenimento", "🎬", ["música", "cinema", "séries", "celebridades", "shows", "streaming"], "ENTERTAINMENT"),
    ("Agro, Clima & Sustentabilidade", "🌱", ["agronegócio", "sustentabilidade", "clima", "meio ambiente", "energia renovável", "agricultura"], "SCIENCE"),
    ("Maternidade, Família & Infância", "👶", ["maternidade", "família", "filhos", "gravidez", "educação infantil", "parentalidade"], "HEALTH"),
    ("Espiritualidade & Religião", "🕊️", ["espiritualidade", "religião", "fé", "meditação", "igreja", "astrologia"], "NATION"),
    ("Eventos, Casamentos & Festas", "💍", ["eventos", "casamento", "festas", "formatura", "cerimonial", "buffet"], "ENTERTAINMENT"),
    ("Indústria, Logística & Comércio Exterior", "🏭", ["indústria", "logística", "exportação", "importação", "transporte", "cadeia de suprimentos"], "BUSINESS"),
    ("Varejo & E-commerce", "🛒", ["varejo", "e-commerce", "lojas", "consumo", "marketplace", "black friday"], "BUSINESS"),
    ("Serviços Locais & Autônomos", "🛠️", ["serviços", "autônomos", "MEI", "prestador de serviços", "freelancer", "pequeno negócio"], "BUSINESS"),
    ("Causas Sociais & Terceiro Setor", "🤝", ["ONG", "voluntariado", "causas sociais", "impacto social", "solidariedade", "inclusão"], "NATION"),
    ("Geral / Outro nicho", "🌐", ["tendências", "viral", "novidades", "comportamento", "consumo", "cultura"], "NATION"),
]

NICHOS = {
    nome: {"emoji": emoji, "tags": tags, "topic": topic, "query": " OR ".join(tags[:4])}
    for nome, emoji, tags, topic in _NICHOS_RAW
}

TONS = ["Autoridade", "Inspiracional", "Educativo", "Provocador", "Descontraído", "Premium / Luxo", "Viral / Humor"]

REDES = ["Qualquer rede", "Instagram", "TikTok", "YouTube", "LinkedIn", "X (Twitter)", "Pinterest", "Blog / Newsletter"]
