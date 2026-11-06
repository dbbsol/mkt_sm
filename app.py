"""
app.py
─────────────────────────────────────────────────────────────────
INTELIGÊNCIA EDITORIAL — Radar de tendências em alta × parecer
estratégico do Gemini (encaixe no nicho + gatilhos mentais).

Execução:  streamlit run app.py
Chave Gemini: constante GEMINI_API_KEY em core/ai_generator.py

Camadas:
- config/  -> nichos, prompts, guard-rails éticos
- core/    -> motor de tendências (fontes gratuitas) e IA (Gemini)

Interface minimalista, no padrão visual da DBB Soluções Empresariais.
A quantidade de pautas destrinchadas é fixa (QTD_PAUTAS).
─────────────────────────────────────────────────────────────────
"""

import os
import time
import html
import datetime

import streamlit as st
try:
    import streamlit.components.v1 as components
except Exception:  # versões novas do Streamlit podem remover este módulo
    components = None
from dotenv import load_dotenv

from config import niches
from core import ai_generator, trends_engine

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

load_dotenv()


def _chave_gemini():
    """Chave do Gemini fora do código: .streamlit/secrets.toml ou .env."""
    try:
        k = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        k = ""
    return str(k or os.getenv("GEMINI_API_KEY", "")).strip().strip('"').strip("'")


_k = _chave_gemini()
if _k:
    os.environ["GEMINI_API_KEY"] = _k
    if not getattr(ai_generator, "GEMINI_API_KEY", ""):
        ai_generator.GEMINI_API_KEY = _k

# Quantidade fixa de pautas destrinchadas (não é mais uma opção na tela).
QTD_PAUTAS = 6

st.set_page_config(
    page_title="Inteligência Editorial",
    page_icon="🔶",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── ESTILO (identidade visual DBB, versão minimalista) ─────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@300;400;500;600&family=Manrope:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root{
  --bg:#06040a; --bg2:#0c0812;
  --surface:rgba(255,255,255,.035); --surface-2:rgba(255,255,255,.06);
  --line:rgba(255,255,255,.09); --line-2:rgba(255,255,255,.16);
  --text:#ece7f1; --muted:#9a91a7; --dim:#625a70;
  --red:#ff3d5a; --wine:#8a2332; --gold:#f2c96b; --ok:#4ade9a; --warn:#ffb547;
  --grad:linear-gradient(120deg,#ff3d5a 0%,#f2c96b 100%);
  --display:'Unbounded',sans-serif; --body:'Manrope',sans-serif; --mono:'JetBrains Mono',monospace;
}

html, body, .stApp, .stMarkdown, p, label, input, textarea, button, li,
[data-baseweb="select"] div { font-family: var(--body) !important; }
.stApp { background: var(--bg) !important; color: var(--text) !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"], .main { background: transparent !important; position: relative; z-index: 1; }

/* fundo: grade + aurora (igual à LP) */
.stApp::before{
  content:''; position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:linear-gradient(rgba(255,255,255,.028) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.028) 1px,transparent 1px);
  background-size:64px 64px;
  -webkit-mask-image:radial-gradient(ellipse 80% 60% at 50% 0%,#000 30%,transparent 80%);
  mask-image:radial-gradient(ellipse 80% 60% at 50% 0%,#000 30%,transparent 80%);
}
.stApp::after{
  content:''; position:fixed; inset:-10%; z-index:0; pointer-events:none;
  background:
    radial-gradient(circle 420px at 88% 2%, rgba(255,61,90,.30), transparent 70%),
    radial-gradient(circle 380px at 0% 55%, rgba(242,201,107,.12), transparent 70%),
    radial-gradient(circle 380px at 85% 100%, rgba(138,35,50,.38), transparent 70%);
  animation: drift 24s ease-in-out infinite alternate;
}
@keyframes drift { to { transform: translate(-40px, 30px) scale(1.08); } }

/* limpa o que é do Streamlit */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
.stDeployButton, [data-testid="stAppDeployButton"] { display: none !important; visibility: hidden !important; }
header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding: 0 32px 4rem 32px !important; max-width: 1060px !important; margin: 0 auto !important; }
::selection { background: rgba(255,61,90,.35); color:#fff; }
a { color: var(--gold) !important; text-decoration: none !important; }
a:hover { color: var(--red) !important; }

/* luz que segue o cursor */
#nx-cursor {
  position: fixed; width: 520px; height: 520px; pointer-events: none; z-index: 0; border-radius: 50%; left: 0; top: 0;
  transform: translate(-999px,-999px); transition: transform .16s ease-out;
  background: radial-gradient(circle, rgba(255,61,90,.12), rgba(242,201,107,.04) 45%, transparent 70%);
}

/* NAV */
.nav { position: relative; display:flex; align-items:center; justify-content:space-between; height: 68px; }
.nav::after { content:''; position:absolute; left:-32px; right:-32px; bottom:0; height:1px;
  background: linear-gradient(90deg, transparent, rgba(255,61,90,.55), rgba(242,201,107,.55), transparent); }
.logo { font-family: var(--display) !important; font-weight: 500; font-size: .95rem; color:#fff; display:flex; align-items:center; gap:10px; letter-spacing:.02em; }
.logo i { width:10px; height:10px; border-radius:3px; background: var(--grad); transform: rotate(45deg); box-shadow: 0 0 14px rgba(255,61,90,.7); animation: spinD 8s linear infinite; }
@keyframes spinD { to { transform: rotate(405deg); } }
.nav-pill { display:inline-flex; align-items:center; gap:8px; font-size:.85rem; font-weight:600; color:#fff; padding:9px 18px;
  border:1px solid var(--line-2); border-radius:999px; background: var(--surface); }
.dot { width:6px; height:6px; border-radius:50%; background: var(--dim); }
.dot.ok { background: var(--ok); box-shadow: 0 0 10px var(--ok); animation: pulse 2s infinite; }
.dot.bad { background: var(--red); }
@keyframes pulse { 50% { opacity:.25; } }

/* HERO */
.hero { padding: 78px 0 36px; }
.chip { display:inline-flex; align-items:center; gap:8px; font-family: var(--mono) !important; font-size:.74rem; color: var(--gold);
  border:1px solid rgba(242,201,107,.28); background: rgba(242,201,107,.06); padding:6px 14px; border-radius:999px; margin-bottom:22px; }
.chip .dot { background: var(--ok); box-shadow: 0 0 10px var(--ok); animation: pulse 2s infinite; }
.hero-title { font-family: var(--display) !important; font-weight: 400; color:#fff; letter-spacing:-.02em; line-height:1.14;
  font-size: clamp(1.9rem, 4.2vw, 3.3rem); margin: 0 0 22px; }
.grad { background: linear-gradient(110deg,#ff3d5a 0%,#f2c96b 35%,#ff7a8c 60%,#f2c96b 85%,#ff3d5a 100%); background-size: 220% 100%;
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; animation: shimmer 7s linear infinite; }
@keyframes shimmer { to { background-position: -220% 0; } }
.hero-sub { font-size: 1.05rem; line-height: 1.65; color: var(--muted); max-width: 520px; font-weight: 400; }

/* VIDRO */
.glass, .nx-card, [data-testid="stVerticalBlockBorderWrapper"] {
  --mx: 50%; --my: 50%;
  position: relative; overflow: hidden;
  background: linear-gradient(160deg, rgba(255,255,255,.07), rgba(255,255,255,.02)) !important;
  border: 1px solid var(--line) !important; border-radius: 18px !important;
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
}
.glass::before, .nx-card::before, [data-testid="stVerticalBlockBorderWrapper"]::before {
  content:''; position:absolute; top:0; left:12%; right:12%; height:1px; z-index:3;
  background: linear-gradient(90deg, transparent, var(--gold), var(--red), transparent); opacity:.8;
}
.nx-card::after { content:''; position:absolute; inset:0; pointer-events:none; opacity:0; transition: opacity .4s;
  background: radial-gradient(420px circle at var(--mx) var(--my), rgba(255,61,90,.14), transparent 60%); }
.nx-card { padding: 30px 32px; margin-bottom: 20px; transition: transform .5s cubic-bezier(.16,1,.3,1), border-color .4s, box-shadow .5s; }
.nx-card:hover { transform: translateY(-5px); border-color: rgba(255,61,90,.35) !important;
  box-shadow: 0 30px 80px -30px rgba(255,61,90,.35), 0 0 0 1px rgba(242,201,107,.08) inset; }
.nx-card:hover::after { opacity: 1; }
.nx-card > * { position: relative; z-index: 2; }
[data-testid="stVerticalBlockBorderWrapper"] { padding: 14px 14px 8px; box-shadow: 0 40px 120px -40px rgba(255,61,90,.3); }

.sec-label { font-family: var(--mono) !important; font-size:.72rem; color: var(--red); margin-bottom: 10px; }
.sec-label::before { content:''; display:inline-block; width:6px; height:6px; border-radius:50%; background: var(--red); box-shadow: 0 0 10px var(--red); margin-right:10px; vertical-align:middle; }
.sec-title { font-family: var(--display) !important; font-weight:400; color:#fff; font-size: clamp(1.4rem, 2.6vw, 2rem); letter-spacing:-.02em; line-height:1.15; margin: 0 0 24px; }

/* CAMPOS */
label, .stSelectbox label, .stTextInput label, [data-testid="stWidgetLabel"] p {
  color: var(--text) !important; font-size: .8rem !important; font-weight: 600 !important; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"] {
  background: rgba(255,255,255,.04) !important; border: 1px solid var(--line) !important; border-radius: 12px !important;
  color:#fff !important; min-height: 3rem; transition: border-color .3s, box-shadow .3s, background .3s;
}
[data-baseweb="base-input"] { border: none !important; }
[data-baseweb="select"] > div:hover, [data-baseweb="input"]:hover { border-color: var(--line-2) !important; }
[data-baseweb="select"] > div:focus-within, [data-baseweb="input"]:focus-within {
  border-color: var(--gold) !important; box-shadow: 0 0 0 3px rgba(242,201,107,.12) !important; background: rgba(242,201,107,.04) !important; }
[data-baseweb="select"] *, [data-baseweb="input"] input, .stTextInput input { color: #fff !important; -webkit-text-fill-color: #fff !important; }
[data-baseweb="select"] input { background: transparent !important; }
[data-baseweb="select"] svg { fill: var(--muted) !important; }
.stTextInput input { background: transparent !important; font-size: .95rem !important; padding: .8rem 1rem !important; }
input::placeholder { color: var(--dim) !important; -webkit-text-fill-color: var(--dim) !important; opacity: 1 !important; }

/* lista suspensa (abre fora da página, por isso o seletor é global) */
[data-baseweb="popover"] > div, [data-baseweb="popover"] [data-baseweb="menu"] {
  background: #0c0812 !important; border: 1px solid var(--line-2) !important; border-radius: 12px !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] [role="listbox"] { background: transparent !important; }
[data-baseweb="popover"] li, [data-baseweb="popover"] [role="option"] { background: transparent !important; color: var(--text) !important; }
[data-baseweb="popover"] li *, [data-baseweb="popover"] [role="option"] * { color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] [role="option"]:hover, [data-baseweb="popover"] [aria-selected="true"] {
  background: rgba(255,61,90,.14) !important; }

/* BOTÕES */
.stButton > button {
  position: relative; overflow: hidden; isolation: isolate;
  background: transparent !important; color:#fff !important; font-weight: 700 !important; font-size: .95rem !important;
  border: 1px solid var(--line-2) !important; border-radius: 999px !important; padding: .85rem 1.8rem !important; box-shadow: none !important;
  transition: transform .3s, box-shadow .3s, border-color .3s !important;
}
.stButton > button p { color: inherit !important; font-weight: 700 !important; }
.stButton > button:hover { border-color: var(--gold) !important; box-shadow: 0 0 30px rgba(242,201,107,.15) !important; color:#fff !important; }
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] {
  background: var(--grad) !important; color:#14080c !important; border: none !important; padding: 1rem 2rem !important;
  box-shadow: 0 10px 40px rgba(255,61,90,.28) !important; animation: glowbtn 3.4s ease-in-out infinite;
}
.stButton > button[kind="primary"] p, [data-testid="stBaseButton-primary"] p { color:#14080c !important; }
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {
  color:#14080c !important; transform: translateY(-2px); box-shadow: 0 16px 54px rgba(255,61,90,.42) !important; }
.stButton > button[kind="primary"]::after, [data-testid="stBaseButton-primary"]::after {
  content:''; position:absolute; top:0; bottom:0; left:-60%; width:40%; z-index:-1;
  background: linear-gradient(100deg, transparent, rgba(255,255,255,.55), transparent); transform: skewX(-20deg); transition: left .7s cubic-bezier(.16,1,.3,1); }
.stButton > button[kind="primary"]:hover::after, [data-testid="stBaseButton-primary"]:hover::after { left: 130%; }
@keyframes glowbtn { 50% { box-shadow: 0 12px 56px rgba(255,61,90,.5), 0 0 0 6px rgba(255,61,90,.06); } }

/* PROGRESSO */
.stProgress > div > div > div { background: var(--grad) !important; border-radius: 999px !important; }
.stProgress > div > div { background: var(--line) !important; border-radius: 999px !important; height: 4px !important; }

/* PÍLULAS */
.pill { display:inline-flex; align-items:center; margin: 4px 8px 4px 0; font-family: var(--mono) !important; font-size:.7rem;
  padding: 5px 12px; border-radius: 999px; border: 1px solid var(--line); color: var(--muted); background: var(--surface); }
.pill.gold { color: var(--gold); border-color: rgba(242,201,107,.35); background: rgba(242,201,107,.07); }
.pill.bad { color: var(--red); border-color: rgba(255,61,90,.4); background: rgba(255,61,90,.07); }
.pill.ok { color: var(--ok); border-color: rgba(74,222,154,.35); background: rgba(74,222,154,.07); }

/* PAUTA */
.p-head { display:flex; gap: 22px; align-items:flex-start; }
.p-rank { font-family: var(--display) !important; font-weight:400; font-size: 1.9rem; line-height:1; min-width: 3.1rem;
  background: var(--grad); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color: transparent; }
.p-cat { font-family: var(--mono) !important; font-size:.7rem; color: var(--red); }
.p-cat::before { content:''; display:inline-block; width:6px; height:6px; border-radius:50%; background: var(--red); box-shadow: 0 0 10px var(--red); margin-right:10px; vertical-align:middle; }
.p-title { font-family: var(--display) !important; font-weight:400; color:#fff; font-size: 1.2rem; letter-spacing:-.01em; line-height:1.3; margin: 10px 0 12px; }
.p-meter { display:flex; align-items:center; gap:12px; margin-top: 14px; font-size:.72rem; color: var(--dim); font-family: var(--mono) !important; }
.p-bar { flex:1; max-width: 220px; height: 6px; border-radius: 99px; background: var(--line); overflow:hidden; }
.p-bar > i { display:block; height:100%; border-radius:99px; background: var(--grad); }
.p-sec h5 { font-family: var(--mono) !important; font-size:.68rem; color: var(--gold); margin: 0 0 6px; font-weight:500; letter-spacing:.02em; }
.p-sec p { font-size: .92rem; line-height: 1.7; color: var(--muted); margin: 0; }
.p-sec + .p-sec { margin-top: 16px; }

.insight { margin-top: 22px; display:flex; gap: 14px; align-items:flex-start; background: rgba(242,201,107,.06);
  border: 1px solid rgba(242,201,107,.2); border-radius: 12px; padding: 16px 18px; font-size:.88rem; color: var(--text); line-height:1.6; }
.insight .ai { flex:none; width:26px; height:26px; border-radius:8px; background: var(--grad); display:grid; place-items:center;
  font-family: var(--mono) !important; font-size:.62rem; font-weight:500; color:#14080c; }
.insight-body { flex:1; min-width:0; }
.insight .lab { font-family: var(--mono) !important; font-size:.68rem; color: var(--gold); margin-bottom: 6px; }
.insight p { margin: 0; color: var(--text); font-size:.9rem; line-height:1.65; }
.hook { margin-top: 14px; padding-left: 14px; border-left: 2px solid var(--red); color:#fff; font-size: 1rem; line-height:1.55; font-weight:500; }
.g-row { margin-top: 14px; }

details.more { margin-top: 20px; }
details.more summary { cursor: pointer; font-family: var(--mono) !important; font-size:.76rem; color: var(--muted); list-style: none; transition: color .3s; }
details.more summary::-webkit-details-marker { display:none; }
details.more summary::before { content:'+'; display:inline-block; width: 1.3rem; color: var(--red); font-weight: 700; }
details.more[open] summary::before { content:'–'; }
details.more summary:hover { color: var(--gold); }
details.more .more-body { padding-top: 18px; }
.g-item { padding: 10px 0; border-bottom: 1px solid var(--line); }
.g-item:last-child { border-bottom: none; }
.g-name { font-weight:600; font-size:.88rem; color:#fff; margin-bottom:2px; }
.g-how { font-size:.85rem; color: var(--muted); line-height:1.6; }
.g-eff { font-family: var(--mono) !important; font-size:.68rem; color: var(--dim); margin-top: 4px; }
.src-item { padding: 9px 0; border-bottom: 1px solid var(--line); font-size:.84rem; color: var(--muted); line-height:1.5; }
.src-item small { color: var(--dim); font-family: var(--mono) !important; font-size:.68rem; }
.warn { background: rgba(255,181,71,.07); border:1px solid rgba(255,181,71,.3); border-radius: 12px; padding: 14px 18px;
  font-size:.88rem; color: #f0d9a8; margin: 0 0 18px; line-height:1.6; }
.stamp { font-family: var(--mono) !important; font-size:.66rem; color: var(--dim); margin-top: 8px; }
.foot { display:flex; justify-content:space-between; gap:20px; padding: 32px 0 8px; margin-top: 56px; border-top: 1px solid var(--line);
  font-size:.82rem; color: var(--dim); }

@media (max-width: 620px) {
  .block-container, [data-testid="stMainBlockContainer"] { padding: 0 20px 3rem 20px !important; }
  .hero { padding: 56px 0 24px; } .nx-card { padding: 24px 20px; } .p-head { gap: 14px; } #nx-cursor { display:none; }
}
@media (prefers-reduced-motion: reduce) { *, .stApp::after { animation: none !important; transition-duration: .01ms !important; } }
</style>
""", unsafe_allow_html=True)

# Brilho que segue o cursor + spotlight nos cartões
try:
    if components is None:
        raise RuntimeError
    components.html("""
    <script>
    try {
      const d = window.parent.document;
      if (!d.getElementById('nx-cursor')) {
        const g = d.createElement('div'); g.id = 'nx-cursor'; d.body.appendChild(g);
        d.addEventListener('mousemove', function(e) {
          g.style.transform = 'translate(' + (e.clientX - 260) + 'px,' + (e.clientY - 260) + 'px)';
          const c = e.target.closest ? e.target.closest('.nx-card') : null;
          if (c) {
            const r = c.getBoundingClientRect();
            c.style.setProperty('--mx', (e.clientX - r.left) + 'px');
            c.style.setProperty('--my', (e.clientY - r.top) + 'px');
          }
        });
      }
    } catch (e) {}
    </script>
    """, height=0)
except Exception:
    pass  # o brilho do cursor é só efeito visual

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
FONTES = trends_engine.FONTES


def now_br():
    if ZoneInfo:
        try:
            return datetime.datetime.now(ZoneInfo("America/Sao_Paulo"))
        except Exception:
            pass
    return datetime.datetime.now()


def esc(s):
    """Escapa HTML e o cifrão (evita que o Streamlit interprete LaTeX)."""
    return html.escape(str(s if s is not None else ""), quote=False).replace("$", "&#36;")


def safe_link(u):
    u = (u or "").strip()
    return html.escape(u, quote=True) if u.startswith(("http://", "https://")) else ""


# ─── RENDERIZAÇÃO DA PAUTA ──────────────────────────────────────
def _fontes_html(c):
    out = []
    for x in c["contexto"]:
        lk = safe_link(x.get("link"))
        ttl = esc(x["titulo"])
        ttl = f'<a href="{lk}" target="_blank" rel="noopener">{ttl}</a>' if lk else ttl
        out.append(f'<div class="src-item">{ttl}<br><small>{esc(x.get("fonte", ""))}</small></div>')
    return "".join(out)


def render_pauta(i, c, p, nicho_nome, max_score):
    titulo = (p or {}).get("titulo") or c["titulo"]
    calor = int(min(100, 35 + 65 * (c["score"] / max_score if max_score else 0)))

    parts = ['<div class="nx-card"><div class="p-head">',
             f'<div class="p-rank">{i:02d}</div><div style="flex:1;min-width:0;">']
    if p and p.get("categoria"):
        parts.append(f'<div class="p-cat">{esc(p["categoria"])}</div>')
    parts.append(f'<div class="p-title">{esc(titulo)}</div><div>')
    for s in c["fontes"][:3]:
        parts.append(f'<span class="pill">{esc(FONTES[s][1])}</span>')
    if p and p.get("cuidado"):
        cu = str(p["cuidado"]).lower()
        if cu == "alto":
            parts.append('<span class="pill bad">cuidado alto</span>')
        elif cu == "medio":
            parts.append('<span class="pill gold">cuidado médio</span>')
    parts.append('</div>')
    parts.append(f'<div class="p-meter">calor <div class="p-bar"><i style="width:{calor}%"></i></div> {calor}/100</div>')
    parts.append('</div></div>')

    if p:
        gat = [g for g in (p.get("gatilhos") or []) if isinstance(g, dict)]
        parts.append('<div class="insight"><span class="ai">IA</span><div class="insight-body">')
        parts.append(f'<div class="lab">Como encaixar em {esc(nicho_nome)}</div>')
        parts.append(f'<p>{esc(p.get("encaixe_nicho", ""))}</p>')
        if p.get("hook"):
            parts.append(f'<div class="hook">“{esc(p["hook"])}”</div>')
        if gat:
            parts.append('<div class="g-row">' + "".join(f'<span class="pill gold">{esc(g.get("nome", ""))}</span>' for g in gat[:4]) + '</div>')
        parts.append('</div></div>')

        if str(p.get("cuidado", "")).lower() in ("alto", "medio") and p.get("nota_cuidado"):
            parts.append(f'<div class="warn" style="margin:16px 0 0;">{esc(p["nota_cuidado"])}</div>')

        parts.append('<details class="more"><summary>Ver análise completa</summary><div class="more-body">')
        parts.append(f'<div class="p-sec"><h5>O que é</h5><p>{esc(p.get("o_que_e", ""))}</p></div>')
        parts.append(f'<div class="p-sec"><h5>Por que está em alta</h5><p>{esc(p.get("por_que_em_alta", ""))}</p></div>')
        parts.append(f'<div class="p-sec"><h5>Por que chama a atenção</h5><p>{esc(p.get("por_que_chama_atencao", ""))}</p></div>')
        if p.get("formato"):
            parts.append(f'<div class="p-sec"><h5>Formato sugerido</h5><p>{esc(p["formato"])}</p></div>')
        if gat:
            parts.append('<div class="p-sec"><h5>Gatilhos mentais</h5>')
            for g in gat[:4]:
                parts.append(f'<div class="g-item"><div class="g-name">{esc(g.get("nome", ""))}</div>'
                             f'<div class="g-how">{esc(g.get("como_aplicar", ""))}</div>'
                             f'<div class="g-eff">efeito: {esc(g.get("efeito", ""))}</div></div>')
            parts.append('</div>')
        if c["contexto"]:
            parts.append(f'<div class="p-sec"><h5>Fontes coletadas ({len(c["contexto"])})</h5>{_fontes_html(c)}</div>')
        parts.append('</div></details>')
    elif c["contexto"]:
        parts.append(f'<details class="more"><summary>Ver fontes coletadas ({len(c["contexto"])})</summary><div class="more-body">{_fontes_html(c)}</div></details>')

    parts.append('</div>')
    return "".join(parts)


# ─── ESTADO ─────────────────────────────────────────────────────
if "res" not in st.session_state:
    st.session_state.res = None
res = st.session_state.res
tem_chave = bool(ai_generator.get_api_key())

# ─── BARRA SUPERIOR ─────────────────────────────────────────────
st.markdown(
    '<div class="nav"><div class="logo"><i></i>Inteligência Editorial</div>'
    f'<div class="nav-pill"><span class="dot {"ok" if tem_chave else "bad"}"></span>'
    f'{"Gemini ativo" if tem_chave else "Gemini sem chave"}</div></div>',
    unsafe_allow_html=True)

# ─── HERO ───────────────────────────────────────────────────────
now = now_br()
st.markdown(f"""
<div class="hero">
<span class="chip"><span class="dot"></span>{DIAS[now.weekday()]} · {now.day} de {MESES[now.month - 1]}</span>
<div class="hero-title">O que está em alta, <span class="grad">pronto para o seu nicho.</span></div>
<div class="hero-sub">Escolha o nicho e receba as pautas do momento com um parecer de IA: como encaixar, qual gancho usar e quais gatilhos aplicar.</div>
</div>
""", unsafe_allow_html=True)

if not tem_chave:
    st.markdown('<div class="warn">Chave Gemini não configurada: o radar funciona, mas o parecer da IA fica desativado. '
                'Cole a chave em <b>core/ai_generator.py</b> (constante <b>GEMINI_API_KEY</b>).</div>',
                unsafe_allow_html=True)

# ─── FORMULÁRIO ─────────────────────────────────────────────────
with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        nicho_nome = st.selectbox("Nicho", list(niches.NICHOS.keys()), format_func=lambda x: f"{niches.NICHOS[x]['emoji']}  {x}")
    with c2:
        rede_alvo = st.selectbox("Rede", niches.REDES)
    with c3:
        tom_voz = st.selectbox("Tom de voz", niches.TONS)
    publico = st.text_input("Público-alvo (opcional)", placeholder="Ex: mulheres 25–40, donas de pequenos negócios")
    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
    go = st.button("Gerar pautas", type="primary")

# ─── PIPELINE ───────────────────────────────────────────────────
if go:
    bar = st.progress(0)
    msg = st.empty()

    def say(t, pct):
        msg.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:.74rem;color:#9a91a7;padding:.5rem 0;">{t}</div>', unsafe_allow_html=True)
        bar.progress(pct)

    say("Coletando tendências nas fontes públicas…", 15)
    radar = trends_engine.radar(nicho_nome, QTD_PAUTAS)
    chosen = radar["pautas"]

    say("Gemini montando o parecer…", 65)
    parecer, erro_ia, modelo = {}, None, None
    if chosen:
        try:
            parecer, modelo = ai_generator.gerar_pareceres_pautas(
                pautas_texto=trends_engine.format_pautas_for_ai(chosen),
                nicho=nicho_nome, publico=publico, tom=tom_voz, rede=rede_alvo,
                sugestoes=radar["sugestoes"],
            )
        except ai_generator.GeminiError as e:
            erro_ia = str(e)

    bar.progress(100)
    time.sleep(0.3)
    msg.empty()
    bar.empty()
    st.session_state.res = {
        "nicho": nicho_nome, "chosen": chosen, "parecer": parecer, "status": radar["status"],
        "sugestoes": radar["sugestoes"], "erro_ia": erro_ia, "modelo": modelo,
        "sinais": radar["sinais"], "ts": now_br().strftime("%d/%m/%Y %H:%M"),
    }
    st.rerun()

# ─── RESULTADOS ─────────────────────────────────────────────────
if res:
    chosen, parecer = res["chosen"], res["parecer"]

    st.markdown(
        f'<div style="height:3rem"></div><div class="sec-label">{niches.NICHOS[res["nicho"]]["emoji"]} {esc(res["nicho"])} · {esc(res["ts"])}</div>'
        '<div class="sec-title">Pautas do momento</div>', unsafe_allow_html=True)

    if res["erro_ia"]:
        st.markdown(f'<div class="warn">Parecer da IA indisponível: {esc(res["erro_ia"])}<br>As pautas abaixo foram coletadas normalmente.</div>', unsafe_allow_html=True)

    if not chosen:
        st.markdown('<div class="warn">Nenhuma fonte respondeu agora. Verifique a conexão e tente novamente em instantes.</div>', unsafe_allow_html=True)
    else:
        max_score = max(c["score"] for c in chosen) or 1
        for i, c in enumerate(chosen, 1):
            st.markdown(render_pauta(i, c, parecer.get(i), res["nicho"], max_score), unsafe_allow_html=True)

    if res["sugestoes"]:
        pills = "".join(f'<span class="pill">{esc(s)}</span>' for s in res["sugestoes"])
        st.markdown(f'<div class="nx-card"><div class="sec-label">O que as pessoas estão buscando</div>{pills}</div>', unsafe_allow_html=True)

    if res.get("modelo"):
        st.markdown(f'<div class="stamp">Parecer gerado por {esc(res["modelo"])}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    if st.button("Nova análise"):
        st.session_state.res = None
        st.rerun()

# ─── RODAPÉ ─────────────────────────────────────────────────────
st.markdown('<div class="foot"><span>Inteligência Editorial</span><span>Radar multi-fonte · Parecer Gemini</span></div>', unsafe_allow_html=True)
