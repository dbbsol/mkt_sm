"""
app.py
─────────────────────────────────────────────────────────────────
MKT_SM — Radar de Tendências & Parecer Aprofundado

Mapeia tendências em 6 fontes (com coleta propositalmente profunda —
mais itens por fonte) e usa o Gemini para produzir um PARECER ULTRA
APROFUNDADO: macro-temas, múltiplos exemplos táticos por tema, ideias
de conteúdo e leitura estratégica do momento, cruzando tudo com o
algoritmo do Instagram 2026 e os insights reais do(a) profissional.

Camadas:
- config/     -> nichos, prompts, base estratégica
- core/       -> IA (Gemini) e motor de tendências
- knowledge/  -> documento do algoritmo do Instagram (texto puro)
- database/   -> persistência SQLite (insights + histórico)
─────────────────────────────────────────────────────────────────
"""

import os

import streamlit as st
from dotenv import load_dotenv

from config import niches
from core import ai_generator, trends_engine
from database import db

load_dotenv()
db.init_db()

PROFISSAO = niches.get_profissao_ativa()
SUB_NICHOS = niches.get_sub_nichos()
OBJETIVOS = niches.get_objetivos_campanha()

st.set_page_config(
    page_title=f"Radar de Tendências · {PROFISSAO['nome_exibicao']}",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

COR_PRIM = PROFISSAO["cor_marca_primaria"]
COR_SEC = PROFISSAO["cor_marca_secundaria"]
COR_DEST = PROFISSAO["cor_destaque"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

:root {{
    --bg: #06100C; --card: #0D1A15; --card2: #0F1E18; --border: #1C2E27;
    --prim: {COR_PRIM}; --sec: {COR_SEC}; --gold: {COR_DEST};
    --text: #F1F3EF; --muted: #8CA096;
}}

html, body, [class*="st-"] {{ font-family: 'Inter', sans-serif !important; }}
[data-testid="stAppViewContainer"] {{
    background: radial-gradient(ellipse 120% 60% at 50% -10%, #0B2018 0%, var(--bg) 55%) !important;
}}
[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #05100B 0%, #030A07 100%) !important;
    border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] * {{ color: var(--text) !important; }}
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding: 1rem 2.2rem 4rem 2.2rem !important; max-width: 1440px !important; }}

[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] strong {{
    color: var(--text) !important;
}}
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"], [data-testid="stCaptionContainer"] p {{
    color: var(--text) !important;
}}
[data-testid="stCaptionContainer"] p {{ color: var(--muted) !important; }}

.mkt-hero {{
    background: linear-gradient(135deg, #0A1F17 0%, #030906 65%);
    border-radius: 22px; padding: 2.4rem 2.2rem; margin-bottom: 1.6rem;
    border: 1px solid var(--border);
    box-shadow: 0 20px 60px -20px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.03);
}}
.mkt-logo {{ font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2.5rem; color: var(--text) !important; margin: 0; letter-spacing: -0.01em; }}
.mkt-tagline {{ font-family: 'Space Mono', monospace; font-size: 0.72rem; color: var(--gold) !important; letter-spacing: 0.22em; text-transform: uppercase; }}

.nx-card {{
    background: linear-gradient(160deg, var(--card2) 0%, var(--card) 100%);
    border: 1px solid var(--border); border-radius: 16px; padding: 1.4rem;
    margin-bottom: 0.9rem; box-shadow: 0 8px 24px -12px rgba(0,0,0,0.5);
}}
.nx-card * {{ color: var(--text) !important; }}
.nx-card-accent {{ border-color: var(--gold); }}
.section-label {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; letter-spacing: 0.22em; text-transform: uppercase; color: var(--muted) !important; }}
.section-title {{ font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.3rem; margin: 0.15rem 0 1.1rem; color: var(--text) !important; }}

/* Inputs + selects — cobre BaseWeb (versões antigas do Streamlit) e React Aria
   ComboBox (Streamlit 1.60+), já que a estrutura interna mudou entre versões */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
div[data-baseweb="select"], div[data-baseweb="select"] > div,
div[data-baseweb="select"] div, div[data-baseweb="input"], div[data-baseweb="base-input"],
.react-aria-ComboBox input, .react-aria-ComboBox button, [role="combobox"] {{
    background: #081410 !important; border-color: var(--border) !important;
    color: var(--text) !important; border-radius: 10px !important;
}}
div[data-baseweb="select"] svg, .react-aria-ComboBox svg {{ fill: var(--muted) !important; }}
[data-testid="stSelectboxVirtualDropdown"] {{ background: var(--card) !important; border: 1px solid var(--border) !important; }}
div[data-baseweb="popover"] ul, div[data-baseweb="menu"] {{ background: var(--card) !important; }}
[role="listbox"] {{ background: var(--card) !important; }}
[role="option"] {{ background: var(--card) !important; color: var(--text) !important; }}
[role="option"]:hover, [role="option"][aria-selected="true"], [role="option"][data-focused="true"] {{ background: var(--prim) !important; }}
li[role="option"] {{ background: var(--card) !important; color: var(--text) !important; }}
li[role="option"]:hover, li[aria-selected="true"] {{ background: var(--prim) !important; }}
span[data-baseweb="tag"] {{ background: var(--prim) !important; color: var(--text) !important; }}

[data-testid="stMetric"] {{ background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; padding: 0.8rem 1rem !important; }}
[data-testid="stMetricValue"] {{ color: var(--gold) !important; font-family: 'Syne', sans-serif !important; }}
[data-testid="stMetricLabel"] {{ color: var(--muted) !important; }}

button[kind="primary"], button[kind="secondary"], button[kind="primaryFormSubmit"],
button[kind="secondaryFormSubmit"], button[kind="tertiary"] {{
    background: linear-gradient(135deg, var(--gold), var(--prim)) !important;
    color: #051007 !important; font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    border: none !important; border-radius: 10px !important;
    box-shadow: 0 6px 20px -6px rgba(76,190,147,0.35) !important;
}}
button[kind] p {{ color: #051007 !important; }}
button[kind]:hover {{ transform: translateY(-1px) !important; box-shadow: 0 10px 26px -6px rgba(76,190,147,0.5) !important; }}

.stTabs [data-baseweb="tab-list"] {{ background: var(--card) !important; border-radius: 12px !important; border: 1px solid var(--border) !important; padding: 4px !important; gap: 4px !important; }}
.stTabs [data-baseweb="tab"] {{ color: var(--muted) !important; font-family: 'Syne', sans-serif !important; font-weight: 600 !important; border-radius: 8px !important; }}
.stTabs [data-baseweb="tab"] p {{ color: inherit !important; }}
.stTabs [aria-selected="true"] {{ color: #051007 !important; background: var(--gold) !important; }}
.stTabs [aria-selected="true"] p {{ color: #051007 !important; }}
[data-baseweb="tab-highlight"] {{ background-color: var(--gold) !important; }}
[data-baseweb="tab-border"] {{ background-color: var(--border) !important; }}

[data-testid="stExpander"] {{ background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 14px !important; }}
[data-testid="stAlertContainer"] {{ border-radius: 12px !important; border: 1px solid var(--border) !important; }}
[data-testid="stAlertContainer"] p {{ color: var(--text) !important; }}

.pill {{ display:inline-block; background: rgba(76,190,147,0.1); border:1px solid var(--border); border-radius: 999px; padding: 0.25rem 0.75rem; margin: 0.15rem; font-size: 0.78rem; color: var(--text) !important; }}
.pill-hot {{ border-color: var(--gold); color: var(--gold) !important; }}
.pill-urgente-alta {{ border-color: #FF6B6B; color: #FF6B6B !important; }}
.pill-urgente-media {{ border-color: var(--gold); color: var(--gold) !important; }}
.pill-urgente-baixa {{ border-color: var(--muted); color: var(--muted) !important; }}

hr, .nx-divider {{ border-color: var(--border) !important; }}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📡 Radar de Tendências")
    st.caption(f"Instância ativa: **{PROFISSAO['nome_exibicao']}**")
    st.divider()

    st.markdown("**🔑 API Key Gemini**")
    api_key_sidebar = st.text_input(
        "Cole sua chave (ou defina GEMINI_API_KEY no .env)",
        type="password", placeholder="AIza...",
    )
    api_key_ativa = api_key_sidebar or os.environ.get("GEMINI_API_KEY", "")
    st.markdown("✅ Chave ativa" if api_key_ativa else "⚠️ Insira a chave para gerar o parecer aprofundado")

    st.divider()
    st.markdown("**📡 Fontes de tendências**")
    youtube_ok = bool(os.environ.get("YOUTUBE_API_KEY"))
    pinterest_ok = bool(os.environ.get("PINTEREST_ACCESS_TOKEN"))
    st.caption("✅ Google Trends — sem chave necessária")
    st.caption(f"{'✅' if youtube_ok else '⚠️'} YouTube Data API — {'configurada' if youtube_ok else 'defina YOUTUBE_API_KEY no .env'}")
    st.caption("✅ Google News — sem chave necessária")
    st.caption("✅ Wikipedia/Wikimedia — sem chave necessária")
    st.caption("✅ Hacker News — sem chave necessária")
    st.caption(f"{'✅' if pinterest_ok else '⚠️'} Pinterest API — {'configurada' if pinterest_ok else 'defina PINTEREST_ACCESS_TOKEN no .env (opcional)'}")

    st.divider()
    st.markdown("**🎯 Sub-nichos de atuação**")
    sub_nichos_labels = {k: f"{v['emoji']} {k.replace('_', ' ').title()}" for k, v in SUB_NICHOS.items()}
    sub_nichos_selecionados = st.multiselect(
        "Selecione um ou mais",
        options=list(SUB_NICHOS.keys()),
        default=list(SUB_NICHOS.keys())[:1],
        format_func=lambda k: sub_nichos_labels[k],
    )

    st.divider()
    total_insights = len(db.listar_insights())
    total_pareceres = len(db.listar_pareceres_gerados())
    st.metric("💡 Insights registrados", total_insights)
    st.metric("🧠 Pareceres gerados", total_pareceres)

# ─── HERO ─────────────────────────────────────────────────────────
st.markdown(f"""
<div class="mkt-hero">
    <div class="mkt-tagline">Radar de Tendências &amp; Parecer Aprofundado</div>
    <h1 class="mkt-logo">{PROFISSAO['nome_exibicao']} · Marketing OS</h1>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["💡 Insights de Mercado", "📡 Radar de Tendências", "📚 Histórico"])

# ═══════════════════════════════════════════════════════════════
# TAB 1 — INSIGHTS DE MERCADO
# ═══════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="section-label">Matéria-prima da leitura estratégica</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💡 Registre observações reais de mercado</div>', unsafe_allow_html=True)
    st.caption(
        "Padrões que você percebe com clientes, objeções recorrentes, erros comuns de "
        "quem contrata mal, dúvidas frequentes. A IA usa isso pra ancorar o parecer na "
        "sua experiência real — o que também é o que o algoritmo do Instagram favorece "
        "em 2026 (autenticidade humana > conteúdo genérico)."
    )

    with st.form("form_insight", clear_on_submit=True):
        texto_insight = st.text_area(
            "Descreva o insight",
            placeholder='Ex: "Percebo que muitos clientes confundem alcance com engajamento e cobram a métrica errada."',
            height=100,
        )
        sub_nicho_insight = st.selectbox(
            "Sub-nicho relacionado (opcional)",
            options=["Geral"] + list(SUB_NICHOS.keys()),
            format_func=lambda k: sub_nichos_labels.get(k, k),
        )
        enviar_insight = st.form_submit_button("💾 Salvar insight")
        if enviar_insight and texto_insight.strip():
            db.salvar_insight(texto_insight.strip(), sub_nicho=sub_nicho_insight)
            st.success("Insight salvo com sucesso.")
            st.rerun()

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown("**📋 Insights registrados**")
    insights_salvos = db.listar_insights()
    if not insights_salvos:
        st.info("Nenhum insight registrado ainda. Comece adicionando um acima.")
    for ins in insights_salvos:
        col_a, col_b = st.columns([5, 1])
        with col_a:
            usado = f" · usado em {ins['usado_em_geracao']}x parecer(es)" if ins["usado_em_geracao"] else ""
            st.markdown(f'<div class="nx-card">{ins["texto"]}<br><span class="pill">{ins.get("sub_nicho") or "Geral"}{usado}</span></div>', unsafe_allow_html=True)
        with col_b:
            if st.button("🗑️", key=f"del_insight_{ins['id']}"):
                db.excluir_insight(ins["id"])
                st.rerun()

# ═══════════════════════════════════════════════════════════════
# TAB 2 — RADAR DE TENDÊNCIAS + PARECER APROFUNDADO
# ═══════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="section-label">Inteligência em tempo real · 6 fontes · mapeamento profundo</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📡 Radar de Tendências</div>', unsafe_allow_html=True)
    st.caption(
        "Google Trends, YouTube, Google News, Wikipedia, Hacker News e Pinterest, "
        "coletados em profundidade (até 25 itens por fonte) e fundidos num único ranking "
        "por momentum, estágio de ciclo de vida e relevância pro seu nicho."
    )

    col_btn1, _ = st.columns([1, 4])
    with col_btn1:
        atualizar = st.button("🔄 Atualizar tendências")

    niche_keywords = []
    for sn in (sub_nichos_selecionados or list(SUB_NICHOS.keys())):
        niche_keywords.extend(SUB_NICHOS[sn]["dores"])
        niche_keywords.append(sn.replace("_", " "))

    raw_trends = trends_engine.collect_trends(niche_keywords, force_refresh=atualizar)
    intelligence = trends_engine.build_trend_intelligence(raw_trends, niche_keywords)

    status = raw_trends.get("_status", {})
    badge_map = {"online": "🟢", "sem_chave": "⚪", "indisponivel": "🟡"}
    badges = " ".join(
        f'<span class="pill">{badge_map.get(v, "⚪")} {trends_engine.FONTE_LABELS.get(k, k)}</span>'
        for k, v in status.items()
    )
    st.markdown(badges, unsafe_allow_html=True)
    st.markdown(f"<div style='color:var(--muted);font-size:0.8rem;margin-top:0.4rem;'>{len(intelligence)} tendências mapeadas nesta coleta</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    if not intelligence:
        st.warning("Nenhuma tendência com sinal suficiente agora. Tente atualizar novamente em instantes.")
    else:
        with st.expander(f"📋 Ver todas as {len(intelligence)} tendências mapeadas", expanded=True):
            for t in intelligence:
                cor_estagio = {"PICO": "var(--gold)", "EM ALTA": "var(--prim)", "EMERGENTE": "#5CC8FF", "SATURANDO": "var(--muted)"}.get(t["estagio"], "var(--muted)")
                plataformas_html = " ".join(f'<span class="pill">{p}</span>' for p in t["plataformas"])
                st.markdown(f"""
                <div class="nx-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.4rem;">
                        <div style="font-weight:600;">{t['titulo']}</div>
                        <div class="pill" style="border-color:{cor_estagio};color:{cor_estagio} !important;">{t['estagio']}</div>
                    </div>
                    <div style="margin-top:0.5rem;">
                        <span class="pill">⚡ Momentum: {t['momentum_score']}/100</span>
                        <span class="pill">🎯 Relevância nicho: {t['relevancia_nicho']}</span>
                        {plataformas_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div class='nx-divider' style='border-top:1px solid var(--border); margin: 2rem 0;'></div>", unsafe_allow_html=True)

    # ── PARECER ULTRA APROFUNDADO ──
    st.markdown('<div class="section-label">Cruzamento com o algoritmo do Instagram 2026 + seus insights</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🧠 Parecer Ultra Aprofundado</div>', unsafe_allow_html=True)
    st.caption(
        "A IA agrupa as tendências acima em macro-temas, dá múltiplos exemplos táticos "
        "concretos por tema, e entrega uma leitura estratégica densa de como explorar "
        "cada oportunidade agora."
    )

    col1, col2 = st.columns(2)
    with col1:
        publico_ie = st.text_input("Público-alvo específico (opcional)", placeholder="Ex: donos de negócio local, 30-50 anos...")
    with col2:
        objetivo_ie = st.selectbox("Objetivo atual", options=list(OBJETIVOS.keys()), format_func=lambda k: OBJETIVOS[k])

    gerar_btn = st.button("🧠 GERAR PARECER ULTRA APROFUNDADO COM IA")

    if gerar_btn:
        if not sub_nichos_selecionados:
            st.error("Selecione ao menos um sub-nicho na barra lateral.")
        else:
            try:
                with st.spinner("Analisando em profundidade — cruzando tendências, algoritmo e seus insights (pode levar até 1 minuto)..."):
                    insights_disponiveis = db.listar_insights()
                    textos_insights = [i["texto"] for i in insights_disponiveis]
                    tendencias_texto = trends_engine.format_trends_for_ai(intelligence)

                    resultado = ai_generator.gerar_parecer_aprofundado(
                        profissao=PROFISSAO,
                        sub_nichos_selecionados=sub_nichos_selecionados,
                        publico=publico_ie,
                        objetivo_campanha=OBJETIVOS[objetivo_ie],
                        insights=textos_insights,
                        tendencias_texto=tendencias_texto,
                        api_key=api_key_ativa,
                    )
                db.salvar_parecer_gerado(sub_nichos_selecionados, publico_ie, OBJETIVOS[objetivo_ie], resultado)
                db.marcar_insights_usados([i["id"] for i in insights_disponiveis])
                st.session_state["ultimo_parecer"] = resultado
                st.success("Parecer aprofundado gerado!")
            except ai_generator.GeminiError as e:
                st.error(str(e))

    resultado_exibir = st.session_state.get("ultimo_parecer")
    if resultado_exibir:
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        st.markdown("**📖 Resumo geral**")
        resumo = resultado_exibir.get("resumo_geral", "")
        for paragrafo in resumo.split("\n\n"):
            if paragrafo.strip():
                st.markdown(f'<div class="nx-card">{paragrafo.strip()}</div>', unsafe_allow_html=True)

        col_score, col_just = st.columns([1, 3])
        with col_score:
            st.metric("📊 Score de momento", f"{resultado_exibir.get('score_momento', '-')}/100")
        with col_just:
            st.markdown(f'<div class="nx-card">{resultado_exibir.get("score_justificativa", "")}</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("**🗂️ Macro-temas identificados**")
        for tema in resultado_exibir.get("macro_temas", []):
            with st.expander(f"🎯 {tema.get('nome_tema', 'Tema')}"):
                st.markdown(f"**Por que importa agora:** {tema.get('por_que_importa_agora', '')}")
                if tema.get("tendencias_relacionadas"):
                    st.markdown(" ".join(f'<span class="pill pill-hot">{t}</span>' for t in tema["tendencias_relacionadas"]), unsafe_allow_html=True)
                st.markdown("**Exemplos táticos de exploração:**")
                for ex in tema.get("exemplos_de_exploracao", []):
                    st.markdown(f"- {ex}")
                if tema.get("formatos_recomendados"):
                    st.markdown(" ".join(f'<span class="pill">{f}</span>' for f in tema["formatos_recomendados"]), unsafe_allow_html=True)
                st.markdown(f"**Janela temporal:** {tema.get('janela_temporal', '')}")

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("**🎬 Ideias de conteúdo**")
        for ideia in resultado_exibir.get("ideias_conteudo", []):
            with st.expander(f"📌 {ideia.get('titulo_ideia', 'Ideia')} — {ideia.get('formato_sugerido', '')}"):
                st.markdown(f"**Macro-tema relacionado:** {ideia.get('macro_tema_relacionado', '')}")
                st.markdown(f"**Gancho:** {ideia.get('gancho', '')}")
                st.markdown(f"**Ângulo:** {ideia.get('angulo', '')}")
                st.markdown(f"**Sinal mirado:** {ideia.get('sinal_algoritmo_ou_comportamento_otimizado', '')}")
                st.markdown(f"**CTA sugerido:** {ideia.get('cta_sugerido', '')}")

        if resultado_exibir.get("riscos"):
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            st.markdown("**⚠️ Riscos a evitar**")
            for r in resultado_exibir["riscos"]:
                st.markdown(f'<div class="nx-card">{r}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TAB 3 — HISTÓRICO
# ═══════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="section-label">Consultas anteriores</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📚 Histórico de Pareceres</div>', unsafe_allow_html=True)

    historico = db.listar_pareceres_gerados()
    if not historico:
        st.info("Nenhum parecer gerado ainda. Vá na aba 'Radar de Tendências' e gere o primeiro.")
    for h in historico:
        with st.expander(f"🧠 {h['criado_em'][:16].replace('T', ' ')} — {h['sub_nichos']} · {h['objetivo']}"):
            r = h["resultado"]
            st.markdown(f"**Score de momento:** {r.get('score_momento', '-')}/100")
            st.markdown(r.get("score_justificativa", ""))
            st.markdown("---")
            for tema in r.get("macro_temas", []):
                st.markdown(f"- **{tema.get('nome_tema', '')}**: {tema.get('por_que_importa_agora', '')[:150]}")

st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
st.caption("Radar de Tendências & Parecer Aprofundado — arquitetura modular replicável. Ver README.md.")