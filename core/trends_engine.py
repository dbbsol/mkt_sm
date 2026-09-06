"""
core/trends_engine.py
─────────────────────────────────────────────────────────────────
Motor de inteligência de tendências multi-fonte. Cada fonte é
opcional e isolada — se uma falhar (rede fora, chave ausente, API
fora do ar), as outras continuam funcionando normalmente.

Fontes:
  🟢 Google Trends       — RSS público, sem chave necessária
  🟢 YouTube Data API    — precisa de YOUTUBE_API_KEY (gratuita)
  🟢 Google News / RSS   — RSS público, sem chave necessária
  🟢 Wikipedia/Wikimedia — API pública (Pageviews), sem chave necessária
  🟢 Hacker News API     — API pública, sem chave necessária
  🟢 Pinterest API       — precisa de PINTEREST_ACCESS_TOKEN (conta
                            de negócios + app aprovado pela Pinterest;
                            se não configurado, a fonte é pulada)

Mapeamento propositalmente PROFUNDO (mais itens por fonte que o
necessário mínimo) — o objetivo é dar à IA volume suficiente de
sinal bruto pra produzir um parecer rico em exemplos e conexões,
não uma lista curta e rasa.

Além da coleta crua, este módulo:
  - pontua cada tendência por MOMENTUM (posição de origem + confirmação
    cruzada entre fontes + relevância semântica com o nicho);
  - classifica o ESTÁGIO DE CICLO DE VIDA (emergente/em alta/pico/saturando);
  - mantém rastro de QUAIS PLATAFORMAS confirmaram cada tendência, pra
    ajudar a IA a sugerir o formato de conteúdo certo.
─────────────────────────────────────────────────────────────────
"""

import os
import re
import time
import datetime
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

import requests
import feedparser

_CACHE = {"timestamp": 0, "data": None, "key": None}
_CACHE_TTL_SECONDS = 60 * 15  # 15 minutos

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, application/json, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
}

FONTE_LABELS = {
    "google_trends": "Google Trends",
    "youtube": "YouTube",
    "google_news": "Google News",
    "wikipedia": "Wikipedia",
    "hackernews": "Hacker News",
    "pinterest": "Pinterest",
}


# ─── 🟢 GOOGLE TRENDS (RSS público) ──────────────────────────────
def fetch_google_trends(geo: str = "BR") -> list[dict]:
    urls = [
        f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo}",
        f"https://trends.google.com/trending/rss?geo={geo}",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            if resp.status_code == 200 and len(resp.content) > 200:
                try:
                    root = ET.fromstring(resp.content)
                    items = []
                    ns = {"ht": "https://trends.google.com/trends/trendingsearches/daily"}
                    for item in root.findall(".//item")[:25]:
                        title_el = item.find("title")
                        traffic_el = (
                            item.find("{https://trends.google.com/trends/trendingsearches/daily}approx_traffic")
                            or item.find("ht:approx_traffic", ns)
                        )
                        if title_el is not None and title_el.text:
                            items.append({
                                "title": title_el.text.strip(),
                                "source": "google_trends",
                                "extra": traffic_el.text if traffic_el is not None else "",
                            })
                    if items:
                        return items
                except ET.ParseError:
                    feed = feedparser.parse(resp.content)
                    return [
                        {"title": e.get("title", ""), "source": "google_trends", "extra": e.get("ht_approx_traffic", "")}
                        for e in feed.entries[:25] if e.get("title")
                    ]
        except Exception:
            continue
    return []


# ─── 🟢 YOUTUBE DATA API (precisa de YOUTUBE_API_KEY) ────────────
def fetch_youtube_trending(keywords: list[str], region: str = "BR") -> list[dict]:
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key or not keywords:
        return []
    query = " | ".join(keywords[:6])
    published_after = (datetime.datetime.utcnow() - datetime.timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet", "q": query, "type": "video", "order": "viewCount",
        "publishedAfter": published_after, "maxResults": 20, "regionCode": region,
        "relevanceLanguage": "pt", "key": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            return [
                {
                    "title": item["snippet"]["title"],
                    "source": "youtube",
                    "extra": item["snippet"].get("channelTitle", ""),
                }
                for item in data.get("items", [])
                if item.get("id", {}).get("videoId")
            ]
    except Exception:
        pass
    return []


# ─── 🟢 GOOGLE NEWS / RSS (público) ──────────────────────────────
def fetch_news_rss(url: str, max_items: int = 20) -> list[dict]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            out = []
            for entry in feed.entries[:max_items]:
                title = (entry.get("title") or "").strip()
                if title:
                    out.append({"title": title, "source": "google_news", "extra": entry.get("source", {}).get("title", "") if isinstance(entry.get("source"), dict) else ""})
            return out
    except Exception:
        pass
    return []


def fetch_google_news(keywords: list[str]) -> list[dict]:
    if not keywords:
        return []
    query = "+OR+".join(re.sub(r"\s+", "%20", kw) for kw in keywords[:6])
    url = f"https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt"
    return fetch_news_rss(url)


# ─── 🟢 WIKIPEDIA / WIKIMEDIA (público) ──────────────────────────
def fetch_wikipedia_top_articles(lang: str = "pt") -> list[dict]:
    """Artigos mais visitados da Wikipedia no dia anterior (Wikimedia Pageviews API)."""
    ontem = datetime.datetime.utcnow() - datetime.timedelta(days=2)  # a API costuma ter 1-2 dias de atraso
    y, m, d = ontem.strftime("%Y"), ontem.strftime("%m"), ontem.strftime("%d")
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{lang}.wikipedia/all-access/{y}/{m}/{d}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            artigos = data.get("items", [{}])[0].get("articles", [])
            ignorar = {"Main_Page", "Special:Search", "Wikipédia:Página_principal"}
            out = []
            for a in artigos:
                titulo = a.get("article", "").replace("_", " ")
                if titulo in ignorar or titulo.startswith(("Special:", "Wikipédia:", "Categoria:")):
                    continue
                out.append({"title": titulo, "source": "wikipedia", "extra": str(a.get("views", ""))})
            return out[:25]
    except Exception:
        pass
    return []


# ─── 🟢 HACKER NEWS API (público) ────────────────────────────────
def fetch_hackernews_top(limit: int = 25) -> list[dict]:
    try:
        resp = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return []
        ids = resp.json()[:limit]
        out = []
        for item_id in ids:
            try:
                r = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", headers=HEADERS, timeout=8)
                if r.status_code == 200:
                    item = r.json()
                    if item and item.get("title"):
                        out.append({"title": item["title"], "source": "hackernews", "extra": str(item.get("score", ""))})
            except Exception:
                continue
        return out
    except Exception:
        return []


# ─── 🟢 PINTEREST API (precisa de PINTEREST_ACCESS_TOKEN + conta aprovada) ─
def fetch_pinterest_trends(region: str = "US", trend_type: str = "growing") -> list[dict]:
    """
    API oficial de Trends do Pinterest (v5). Requer conta de negócios com
    app aprovado pela Pinterest e um Access Token OAuth — não é uma chave
    simples. Se PINTEREST_ACCESS_TOKEN não estiver configurado, esta fonte
    é pulada silenciosamente (ver .env.example para instruções).
    """
    token = os.environ.get("PINTEREST_ACCESS_TOKEN", "")
    if not token:
        return []
    url = f"https://api.pinterest.com/v5/trends/keywords/{region}/top/{trend_type}"
    try:
        resp = requests.get(url, headers={**HEADERS, "Authorization": f"Bearer {token}"}, params={"limit": 25}, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            return [
                {"title": t.get("keyword", ""), "source": "pinterest", "extra": f"+{t.get('pct_growth_wow', 0)}% semana"}
                for t in data.get("trends", []) if t.get("keyword")
            ]
    except Exception:
        pass
    return []


# ─── COLETA CONSOLIDADA ───────────────────────────────────────────
def _collect_raw(niche_keywords: list[str]) -> dict:
    results, status = {}, {}

    results["google_trends"] = fetch_google_trends("BR")
    status["google_trends"] = "online" if results["google_trends"] else "indisponivel"

    results["youtube"] = fetch_youtube_trending(niche_keywords)
    status["youtube"] = "online" if results["youtube"] else ("sem_chave" if not os.environ.get("YOUTUBE_API_KEY") else "indisponivel")

    results["google_news"] = fetch_google_news(niche_keywords)
    status["google_news"] = "online" if results["google_news"] else "indisponivel"

    results["wikipedia"] = fetch_wikipedia_top_articles("pt")
    status["wikipedia"] = "online" if results["wikipedia"] else "indisponivel"

    results["hackernews"] = fetch_hackernews_top()
    status["hackernews"] = "online" if results["hackernews"] else "indisponivel"

    results["pinterest"] = fetch_pinterest_trends()
    status["pinterest"] = "online" if results["pinterest"] else ("sem_chave" if not os.environ.get("PINTEREST_ACCESS_TOKEN") else "indisponivel")

    results["_status"] = status
    results["_coletado_em"] = datetime.datetime.now().isoformat()
    return results


def collect_trends(niche_keywords: list[str], force_refresh: bool = False) -> dict:
    """Coleta com cache TTL (15min) pra não sobrecarregar as fontes externas."""
    now = time.time()
    cache_key = tuple(sorted(niche_keywords))
    if not force_refresh and _CACHE["data"] and _CACHE.get("key") == cache_key and (now - _CACHE["timestamp"] < _CACHE_TTL_SECONDS):
        return _CACHE["data"]
    data = _collect_raw(niche_keywords)
    _CACHE["timestamp"] = now
    _CACHE["key"] = cache_key
    _CACHE["data"] = data
    return data


# ─── MATCHING SEMÂNTICO COM O NICHO ──────────────────────────────
def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zà-ú]{4,}", text.lower()))


def score_semantic_relevance(item_title: str, niche_keywords: list[str]) -> float:
    title_tokens = _tokenize(item_title)
    keyword_tokens = set()
    for kw in niche_keywords:
        keyword_tokens |= _tokenize(kw)
    if not title_tokens or not keyword_tokens:
        return 0.0
    overlap = title_tokens & keyword_tokens
    return round(len(overlap) / max(len(keyword_tokens), 1), 3)


# ─── MOMENTUM + CICLO DE VIDA + PLATAFORMAS ──────────────────────
def _lifecycle_stage(source_count: int, position: int) -> str:
    if source_count >= 3:
        return "PICO"
    if source_count == 2:
        return "EM ALTA"
    if position <= 3:
        return "EMERGENTE"
    return "SATURANDO" if position > 12 else "EM ALTA"


def build_trend_intelligence(raw: dict, niche_keywords: list[str], top_n: int = 25) -> list[dict]:
    """
    Funde todas as fontes coletadas numa lista única ranqueada, com score
    de momentum, estágio de ciclo de vida e as plataformas que confirmaram
    cada tendência. top_n é propositalmente alto (25) pra dar à IA volume
    suficiente de material bruto e ela produzir um parecer rico em exemplos.
    """
    title_counter = Counter()
    title_first_pos = {}
    title_meta = {}
    title_plataformas = defaultdict(set)

    for fonte_key in ["google_trends", "youtube", "google_news", "wikipedia", "hackernews", "pinterest"]:
        lst = raw.get(fonte_key, [])
        for pos, item in enumerate(lst):
            title = item.get("title", "").strip()
            if not title:
                continue
            key = title.lower()
            title_counter[key] += 1
            title_plataformas[key].add(fonte_key)
            if key not in title_first_pos:
                title_first_pos[key] = pos
                title_meta[key] = title

    scored = []
    for key, source_count in title_counter.items():
        title = title_meta[key]
        pos = title_first_pos[key]
        semantic = score_semantic_relevance(title, niche_keywords)
        position_score = max(0, 1 - (pos / 25))
        cross_source_score = min(source_count / 3, 1.0)
        momentum = round((position_score * 0.35 + cross_source_score * 0.35 + semantic * 0.30) * 100, 1)
        plataformas = sorted(title_plataformas[key])
        scored.append({
            "titulo": title,
            "momentum_score": momentum,
            "relevancia_nicho": semantic,
            "fontes_confirmando": source_count,
            "plataformas": [FONTE_LABELS.get(p, p) for p in plataformas],
            "estagio": _lifecycle_stage(source_count, pos),
        })

    scored.sort(key=lambda x: x["momentum_score"], reverse=True)
    return scored[:top_n]


def format_trends_for_ai(trend_intelligence: list[dict]) -> str:
    if not trend_intelligence:
        return "Nenhuma tendência com sinal suficiente no momento — gere leitura evergreen baseada nos insights."
    lines = []
    for t in trend_intelligence:
        plataformas = ", ".join(t["plataformas"])
        lines.append(
            f"- {t['titulo']} | momentum: {t['momentum_score']}/100 | estágio: {t['estagio']} "
            f"| relevância p/ nicho: {t['relevancia_nicho']} | visto em: {plataformas}"
        )
    return "\n".join(lines)