"""
core/trends_engine.py
─────────────────────────────────────────────────────────────────
Motor de tendências multi-fonte, 100% gratuito (sem chave). Cada
fonte é isolada: se uma falhar, as outras continuam.

Fontes (todas públicas):
  🇧🇷 Google Trends Brasil / 🌍 EUA   — buscas em alta (RSS)
  📚 Wikipédia                         — artigos mais lidos
  🎯 Google News · seu nicho           — busca RSS pelas palavras do nicho
  🔎 Bing News · seu nicho             — busca RSS
  📰 Google News · editoria            — manchetes da editoria do nicho
  🗞️ G1 / Globo                        — RSS geral
  💬 Reddit r/brasil                   — top do dia (RSS)
  🛠️ Hacker News                       — só para nichos de tecnologia
  ⌨️ Google Suggest                    — buscas relacionadas ao nicho
  ▶️ YouTube (opcional, chave gratuita YOUTUBE_API_KEY)

Além da coleta, o módulo cruza as fontes, agrupa o que é a mesma
pauta, ranqueia (relevância pro nicho + confirmação entre fontes +
volume) e busca contexto extra de cada pauta para a IA destrinchar.
─────────────────────────────────────────────────────────────────
"""

import os
import re
import html
import math
import time
import datetime
import unicodedata
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

import requests
import feedparser

from config import niches

CACHE_TTL_SECONDS = 60 * 10
_CACHE: dict = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, application/json, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
}

# chave → (emoji, rótulo, peso no ranking)
FONTES = {
    "gt_br": ("🇧🇷", "Google Trends Brasil", 3.0),
    "gt_us": ("🌍", "Google Trends EUA", 1.5),
    "wiki": ("📚", "Wikipédia · mais lidos", 2.0),
    "gnews_nicho": ("🎯", "Google News · seu nicho", 2.5),
    "bing_nicho": ("🔎", "Bing News · seu nicho", 2.0),
    "gnews_topico": ("📰", "Google News · editoria", 1.5),
    "g1": ("🗞️", "G1 / Globo", 1.5),
    "reddit": ("💬", "Reddit · r/brasil", 1.0),
    "hn": ("🛠️", "Hacker News", 1.0),
    "youtube": ("▶️", "YouTube (opcional)", 1.5),
}

FONTE_LABELS = {k: v[1] for k, v in FONTES.items()}


# ─── utilidades ──────────────────────────────────────────────────
def clean_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def _get(url, timeout=10, headers=None):
    try:
        r = requests.get(url, headers=headers or HEADERS, timeout=timeout)
        if r.status_code == 200 and r.content:
            return r
    except Exception:
        pass
    return None


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _parse_volume(s: str) -> float:
    try:
        m = re.match(r"\s*([\d.,]+)\s*([a-zA-Zãõ]*)", s or "")
        if not m:
            return 0
        num = float(m.group(1).replace(".", "").replace(",", "."))
        suf = m.group(2).lower()
        if suf.startswith("milh") or suf in ("mi", "m"):
            num *= 1_000_000
        elif suf.startswith("mil") or suf == "k":
            num *= 1_000
        return num
    except Exception:
        return 0


# ─── coletores ───────────────────────────────────────────────────
def fetch_google_trends(geo: str = "BR") -> list[dict]:
    for url in (f"https://trends.google.com/trending/rss?geo={geo}",
                f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo}"):
        r = _get(url, 12)
        if not r:
            continue
        try:
            root = ET.fromstring(r.content)
        except ET.ParseError:
            continue
        items = []
        for it in root.iter("item"):
            title, traffic, news = None, "", []
            for ch in it:
                n = _local(ch.tag)
                if n == "title":
                    title = (ch.text or "").strip()
                elif n == "approx_traffic":
                    traffic = (ch.text or "").strip()
                elif n == "news_item":
                    d = {_local(sub.tag): (sub.text or "").strip() for sub in ch}
                    if d.get("news_item_title"):
                        news.append({
                            "titulo": clean_html(d["news_item_title"]),
                            "resumo": clean_html(d.get("news_item_snippet", "")),
                            "fonte": d.get("news_item_source", ""),
                            "link": d.get("news_item_url", ""),
                        })
            if title:
                items.append({"titulo": title, "tipo": "busca", "trafego": traffic,
                              "volume": _parse_volume(traffic), "contexto": news[:3]})
        if items:
            return items[:20]
    return []


def fetch_rss(url, label="", max_items=12, tipo="noticia", strip_source=False) -> list[dict]:
    r = _get(url, 10)
    if not r:
        return []
    feed = feedparser.parse(r.content)
    out = []
    for e in feed.entries[:max_items]:
        title = clean_html(e.get("title", ""))
        fonte = label
        src = e.get("source")
        if isinstance(src, dict) and src.get("title"):
            fonte = src["title"]
        if strip_source and " - " in title:
            title, _, tail = title.rpartition(" - ")
            fonte = fonte or tail
        resumo = clean_html(e.get("summary", "") or e.get("description", ""))[:240]
        if title:
            out.append({"titulo": title, "resumo": resumo, "fonte": fonte or label,
                        "link": e.get("link", ""), "tipo": tipo})
    return out


def fetch_gnews_search(query: str, limit: int = 10) -> list[dict]:
    q = quote_plus(f"{query} when:2d")
    return fetch_rss(f"https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419",
                     "Google News", limit, strip_source=True)


def fetch_gnews_topic(topic: str) -> list[dict]:
    return fetch_rss(f"https://news.google.com/rss/headlines/section/topic/{topic}?hl=pt-BR&gl=BR&ceid=BR:pt-419",
                     "Google News", 10, strip_source=True)


def fetch_bing(query: str) -> list[dict]:
    return fetch_rss(f"https://www.bing.com/news/search?q={quote_plus(query)}&format=rss&setmkt=pt-BR",
                     "Bing News", 10)


def fetch_wikipedia() -> list[dict]:
    base = datetime.datetime.utcnow()
    for back in (1, 2, 3):
        d = base - datetime.timedelta(days=back)
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/pt.wikipedia/all-access/{d.year}/{d.month:02d}/{d.day:02d}"
        r = _get(url, 10, {"User-Agent": "InteligenciaEditorial/1.0 (streamlit app)", "Accept": "application/json"})
        if not r:
            continue
        try:
            arts = r.json()["items"][0]["articles"]
        except Exception:
            continue
        out = []
        for a in arts:
            t = a.get("article", "").replace("_", " ")
            if not t or ":" in t or t.lower() in ("página principal", "wikipédia"):
                continue
            v = a.get("views", 0)
            out.append({"titulo": t, "tipo": "busca", "volume": v,
                        "trafego": f"{v:,} leituras".replace(",", "."), "contexto": []})
            if len(out) >= 12:
                break
        if out:
            return out
    return []


def fetch_reddit() -> list[dict]:
    r = _get("https://www.reddit.com/r/brasil/top/.rss?t=day", 10,
             {"User-Agent": "InteligenciaEditorial/1.0 (streamlit app)"})
    if not r:
        return []
    feed = feedparser.parse(r.content)
    out = []
    for e in feed.entries[:10]:
        t = clean_html(e.get("title", ""))
        if t:
            out.append({"titulo": t, "resumo": "", "fonte": "Reddit r/brasil", "link": e.get("link", ""), "tipo": "noticia"})
    return out


def fetch_hackernews(limit: int = 8) -> list[dict]:
    r = _get("https://hacker-news.firebaseio.com/v0/topstories.json", 8)
    if not r:
        return []
    out = []
    try:
        for i in r.json()[:limit]:
            rr = _get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json", 6)
            if rr:
                d = rr.json()
                if d and d.get("title"):
                    out.append({"titulo": d["title"], "resumo": "", "fonte": "Hacker News",
                                "link": d.get("url") or f"https://news.ycombinator.com/item?id={i}", "tipo": "noticia"})
    except Exception:
        pass
    return out


def fetch_youtube(keywords: list[str]) -> list[dict]:
    """Opcional. Chave gratuita do YouTube Data API em YOUTUBE_API_KEY."""
    key = os.environ.get("YOUTUBE_API_KEY", "")
    if not key or not keywords:
        return []
    after = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        r = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "part": "snippet", "q": " | ".join(keywords[:4]), "type": "video", "order": "viewCount",
            "publishedAfter": after, "maxResults": 10, "regionCode": "BR", "relevanceLanguage": "pt", "key": key,
        }, timeout=12)
        if r.status_code == 200:
            return [{"titulo": it["snippet"]["title"], "resumo": "", "fonte": it["snippet"].get("channelTitle", "YouTube"),
                     "link": f"https://www.youtube.com/watch?v={it['id']['videoId']}", "tipo": "noticia"}
                    for it in r.json().get("items", []) if it.get("id", {}).get("videoId")]
    except Exception:
        pass
    return []


def fetch_suggest(terms: list[str]) -> list[str]:
    out: list[str] = []
    for t in terms[:3]:
        r = _get(f"https://suggestqueries.google.com/complete/search?client=firefox&hl=pt-BR&gl=br&q={quote_plus(t)}", 6)
        if r:
            try:
                for s in r.json()[1][:6]:
                    if s and s.lower() != t.lower() and s not in out:
                        out.append(s)
            except Exception:
                pass
    return out[:14]


# ─── coleta consolidada (paralela, com cache) ────────────────────
def collect_all(nicho_nome: str, force_refresh: bool = False) -> dict:
    now = time.time()
    hit = _CACHE.get(nicho_nome)
    if hit and not force_refresh and now - hit["t"] < CACHE_TTL_SECONDS:
        return hit["data"]

    nicho = niches.NICHOS[nicho_nome]
    jobs = {
        "gt_br": lambda: fetch_google_trends("BR"),
        "gt_us": lambda: fetch_google_trends("US"),
        "wiki": fetch_wikipedia,
        "gnews_nicho": lambda: fetch_gnews_search(nicho["query"], 12),
        "bing_nicho": lambda: fetch_bing(nicho["tags"][0] + " " + nicho["tags"][1]),
        "gnews_topico": lambda: fetch_gnews_topic(nicho["topic"]),
        "g1": lambda: fetch_rss("https://g1.globo.com/rss/g1/", "G1 Globo", 10),
        "reddit": fetch_reddit,
        "suggest": lambda: fetch_suggest(nicho["tags"]),
    }
    if nicho["topic"] == "TECHNOLOGY":
        jobs["hn"] = fetch_hackernews
    if os.environ.get("YOUTUBE_API_KEY"):
        jobs["youtube"] = lambda: fetch_youtube(nicho["tags"])

    results = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {k: ex.submit(fn) for k, fn in jobs.items()}
        for k, f in futs.items():
            try:
                results[k] = f.result(timeout=40)
            except Exception:
                results[k] = []
    _CACHE[nicho_nome] = {"t": now, "data": results}
    return results


def status_fontes(data: dict) -> dict:
    return {k: ("ok" if data.get(k) else "off") for k in list(FONTES) + ["suggest"] if k in data}


# ─── cruzamento, deduplicação e ranking ──────────────────────────
_STOP = set("para como sobre mais esta esse esses essas apos entre quando onde pela pelo pelos pelas dele dela seus suas isso essa este "
            "numa nesta neste desta deste ainda tambem depois antes contra sem com uma uns umas que por dos das nos nas aos foi sao ser tem ter "
            "vai vem mas the and for with from after about into over".split())


def _toks(s: str) -> set[str]:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return {w for w in re.findall(r"[a-z0-9]{3,}", s) if w not in _STOP}


def build_clusters(data: dict, nicho_nome: str) -> list[dict]:
    nicho = niches.NICHOS[nicho_nome]
    items = []
    for key, lst in data.items():
        if key == "suggest" or not isinstance(lst, list):
            continue
        for it in lst:
            it = dict(it)
            it["src"] = key
            items.append(it)
    items.sort(key=lambda x: 0 if x.get("tipo") == "busca" else 1)

    clusters: list[dict] = []
    for it in items:
        tk = _toks(it["titulo"])
        tgt = None
        for c in clusters:
            if not tk or not c["tokens"]:
                if it["titulo"].lower() == c["titulo"].lower():
                    tgt = c
                    break
                continue
            jac = len(tk & c["tokens"]) / len(tk | c["tokens"])
            sub = (c["tipo"] == "busca" and c["tokens"] <= tk and
                   (len(c["tokens"]) >= 2 or max(len(w) for w in c["tokens"]) >= 6))
            if jac >= 0.5 or sub:
                tgt = c
                break
        if tgt is None:
            tgt = {"titulo": it["titulo"], "tokens": tk, "tipo": it.get("tipo"), "fontes": [],
                   "contexto": [], "volume": 0, "trafego": ""}
            clusters.append(tgt)
        if it["src"] not in tgt["fontes"]:
            tgt["fontes"].append(it["src"])
        tgt["volume"] = max(tgt["volume"], it.get("volume", 0) or 0)
        if it.get("trafego") and not tgt["trafego"]:
            tgt["trafego"] = it["trafego"]
        ctxs = it.get("contexto") or []
        if it.get("tipo") == "noticia":
            ctxs = [{"titulo": it["titulo"], "resumo": it.get("resumo", ""),
                     "fonte": it.get("fonte") or FONTE_LABELS.get(it["src"], ""), "link": it.get("link", "")}]
        seen = {x["titulo"] for x in tgt["contexto"]}
        for cx in ctxs:
            if cx["titulo"] not in seen:
                tgt["contexto"].append(cx)
                seen.add(cx["titulo"])

    nicho_tokens: set[str] = set()
    for t in nicho["tags"]:
        nicho_tokens |= _toks(t)

    for c in clusters:
        text = " ".join([c["titulo"]] + [x["titulo"] + " " + x.get("resumo", "") for x in c["contexto"]])
        hits = len(nicho_tokens & _toks(text))
        base = sum(FONTES[s][2] for s in c["fontes"])
        multi = 1.2 * (len(c["fontes"]) - 1)
        vol = math.log10(c["volume"]) * 0.5 if c["volume"] > 1 else 0
        c["score"] = base + multi + min(hits, 4) * 1.5 + vol
    return clusters


def select_top(clusters: list[dict], n: int) -> list[dict]:
    """Top N por score, sem deixar uma única fonte dominar a lista."""
    clusters = sorted(clusters, key=lambda c: c["score"], reverse=True)
    cap = max(2, math.ceil(n / 2))
    count: dict = {}
    chosen = []
    for c in clusters:
        p = c["fontes"][0]
        if count.get(p, 0) >= cap:
            continue
        chosen.append(c)
        count[p] = count.get(p, 0) + 1
        if len(chosen) >= n:
            break
    return chosen


def enrich(chosen: list[dict]) -> None:
    """Busca manchetes extras (Google News) para as pautas com pouco contexto."""
    def job(c):
        if len(c["contexto"]) >= 3:
            return
        seen = {x["titulo"] for x in c["contexto"]}
        for f in fetch_gnews_search(c["titulo"], 4):
            if f["titulo"] not in seen and len(c["contexto"]) < 4:
                c["contexto"].append({"titulo": f["titulo"], "resumo": f.get("resumo", ""),
                                      "fonte": f.get("fonte", ""), "link": f.get("link", "")})
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(job, chosen))


def radar(nicho_nome: str, qtd: int, force_refresh: bool = False) -> dict:
    """Pipeline completo: coleta → cruza → ranqueia → enriquece."""
    data = collect_all(nicho_nome, force_refresh=force_refresh)
    clusters = build_clusters(data, nicho_nome)
    chosen = select_top(clusters, qtd)
    enrich(chosen)
    sinais = sum(len(v) for k, v in data.items() if k != "suggest" and isinstance(v, list))
    return {"pautas": chosen, "status": status_fontes(data), "sugestoes": data.get("suggest", []), "sinais": sinais}


def format_pautas_for_ai(pautas: list[dict]) -> str:
    blocos = []
    for i, c in enumerate(pautas, 1):
        fontes = ", ".join(FONTE_LABELS.get(s, s) for s in c["fontes"])
        linhas = [f'  - {x["titulo"]} ({x.get("fonte", "")}): {x.get("resumo", "")[:220]}' for x in c["contexto"][:4]]
        blocos.append(
            f'[ID {i}] PAUTA: {c["titulo"]}\n'
            f'Sinais em: {fontes} | Volume: {c["trafego"] or "n/d"}\n'
            f'Contexto coletado:\n' + ("\n".join(linhas) if linhas else "  (sem manchetes de apoio)")
        )
    return "\n\n".join(blocos)
