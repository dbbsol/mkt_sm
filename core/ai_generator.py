"""
core/ai_generator.py
─────────────────────────────────────────────────────────────────
Camada de integração com a API do Gemini + geração do parecer
aprofundado de tendências (leitura de tendências + algoritmo do
Instagram + insights reais, tudo correlacionado pela IA em
profundidade). A chave de API é sempre lida de variável de
ambiente — nunca hard-coded.
─────────────────────────────────────────────────────────────────
"""

import os
import re
import json
import time

import requests

from config import prompts, references

GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")
INSTAGRAM_ALGO_PATH = os.path.join(KNOWLEDGE_DIR, "instagram_algoritmo_2026.md")


class GeminiError(Exception):
    pass


def _get_api_key(explicit_key: str | None = None) -> str:
    """
    Sempre limpa a chave antes de usar: espaços, quebras de linha e aspas
    coladas por acidente (muito comum ao copiar/colar de PDF, Word, ou de um
    .env editado manualmente) são a causa mais comum do erro 401
    "credenciais inválidas" mesmo com uma chave real — o Google não recusa
    por ser inválida, recusa porque a chave chegou corrompida.
    """
    raw = explicit_key or os.environ.get("GEMINI_API_KEY", "")
    limpo = raw.strip().strip('"').strip("'").replace("\n", "").replace("\r", "").replace(" ", "")
    if limpo.upper().startswith("GEMINI_API_KEY="):
        limpo = limpo.split("=", 1)[1]
    return limpo


def _validar_formato_chave(key: str) -> str | None:
    """Validação leve e só de formato (não garante que a chave é válida no
    Google, só evita mandar algo obviamente quebrado e receber um erro
    genérico e confuso de volta)."""
    if len(key) < 30:
        return (
            "A chave do Gemini parece incompleta (muito curta). Confira se copiou "
            "ela inteira, sem cortar nenhum caractere, e sem espaços extras no .env."
        )
    if any(c.isspace() for c in key):
        return "A chave do Gemini contém espaços/quebras de linha no meio — copie ela novamente, sem formatação."
    return None


def carregar_algoritmo_instagram() -> str:
    """
    Lê o documento de conhecimento do algoritmo do Instagram (knowledge/).
    Mantido como arquivo .md separado (e não hard-coded no prompt) para
    que possa ser atualizado sem tocar em código.
    """
    try:
        with open(INSTAGRAM_ALGO_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "(Documento do algoritmo não encontrado em knowledge/instagram_algoritmo_2026.md)"


def call_gemini(prompt: str, api_key: str | None = None, max_tokens: int = 8192) -> str:
    key = _get_api_key(api_key)
    if not key:
        raise GeminiError(
            "API Key do Gemini não configurada. Defina GEMINI_API_KEY no .env "
            "ou insira-a na barra lateral. Obtenha gratuitamente em https://aistudio.google.com"
        )
    erro_formato = _validar_formato_chave(key)
    if erro_formato:
        raise GeminiError(erro_formato)

    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        # Os modelos Gemini 3.x descontinuaram temperature/top_p/top_k — passar esses
        # parâmetros hoje causa erro. maxOutputTokens é o único controle necessário aqui.
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    # IMPORTANTE: a chave vai em `params`, nunca concatenada manualmente na URL —
    # concatenar string pode corromper a query se a chave tiver qualquer caractere
    # que precise de URL-encoding, e o Google devolve um erro genérico e confuso
    # nesse caso (parece "chave errada" quando na verdade é a URL que quebrou).
    last_error = None
    for attempt in range(3):
        try:
            resp = requests.post(GEMINI_URL, headers=headers, params={"key": key}, json=body, timeout=120)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            if resp.status_code == 429:
                time.sleep(3 * (attempt + 1))
                continue

            motivo_google = ""
            try:
                err_json = resp.json().get("error", {})
                motivo_google = f' Motivo retornado pelo Google: "{err_json.get("message", "")}" (status: {err_json.get("status", "")}).'
            except Exception:
                motivo_google = f" Resposta bruta: {resp.text[:300]}"

            if resp.status_code == 400:
                raise GeminiError(f"Chave inválida/expirada ou requisição malformada (erro 400).{motivo_google}")
            if resp.status_code in (401, 403):
                raise GeminiError(
                    "Google recusou a chave do Gemini."
                    f"{motivo_google}\n\n"
                    "Checklist pra resolver:\n"
                    "1. Gere uma chave NOVA direto em https://aistudio.google.com (botão "
                    '"Get API key" → "Create API key") — não use uma chave criada no '
                    "Google Cloud Console pra outra API (ex: a do YouTube), são coisas diferentes.\n"
                    "2. Cole a chave nova no .env substituindo a antiga, salve, e reinicie o "
                    "streamlit (Ctrl+C no terminal e rode `streamlit run app.py` de novo).\n"
                    "3. Se persistir, verifique em https://aistudio.google.com se a chave "
                    "aparece como ativa e sem restrições de API."
                )
            last_error = f"Erro API Gemini [{resp.status_code}]:{motivo_google}"
        except requests.RequestException as e:
            last_error = f"Erro de conexão: {e}"
            time.sleep(2)
    raise GeminiError(last_error or "Não foi possível obter resposta da IA após múltiplas tentativas.")


def _repair_truncated_json(text: str) -> str | None:
    """Recupera JSON cortado por limite de tokens, fechando chaves/colchetes
    no último ponto em que a estrutura estava balanceada."""
    start = min((i for i in (text.find("{"), text.find("[")) if i != -1), default=-1)
    if start == -1:
        return None
    in_string, escape = False, False
    stack = []
    last_safe_end = None
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c in "{[":
                stack.append(c)
            elif c in "}]":
                if stack:
                    stack.pop()
                if not stack:
                    last_safe_end = i + 1
                    break
        i += 1
    if not stack and last_safe_end:
        return text[start:last_safe_end]
    if stack:
        closing = "".join("}" if ch == "{" else "]" for ch in reversed(stack))
        candidate = text[start:].rstrip()
        if candidate.endswith(","):
            candidate = candidate[:-1]
        return candidate + closing
    return None


def _extract_json(raw_text: str):
    text = raw_text.strip()
    text = re.sub(r"^```(json)?", "", text.strip())
    text = re.sub(r"```$", "", text.strip())
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        candidate = match.group(1) if match else text
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            repaired = _repair_truncated_json(candidate)
            if repaired:
                return json.loads(repaired)
            raise


def gerar_parecer_aprofundado(
    *,
    profissao: dict,
    sub_nichos_selecionados: list[str],
    publico: str,
    objetivo_campanha: str,
    insights: list[str],
    tendencias_texto: str,
    api_key: str | None = None,
) -> dict:
    """
    Gera o parecer ULTRA APROFUNDADO: agrupa tendências em macro-temas,
    dá múltiplos exemplos táticos por tema, e produz ideias de conteúdo
    ricas — tudo cruzado com o algoritmo do Instagram 2026 e os insights
    reais do(a) profissional. max_tokens elevado (16k) porque a resposta
    é intencionalmente longa e densa — pedimos isso explicitamente no
    prompt, então o teto de tokens precisa acompanhar.
    """
    algoritmo_instagram = carregar_algoritmo_instagram()

    prompt = prompts.PROMPT_PARECER_APROFUNDADO.format(
        persona=prompts.SYSTEM_PERSONA,
        base_estrategica=references.build_scientific_grounding_block(),
        algoritmo_instagram=algoritmo_instagram,
        profissao_nome=profissao["nome_exibicao"],
        sub_nichos=", ".join(sub_nichos_selecionados) or "Geral",
        publico=publico or "Público geral do nicho",
        objetivo_campanha=objetivo_campanha,
        insights="\n".join(f"- {i}" for i in insights) if insights else "Nenhum insight específico fornecido — baseie-se em dores comuns do sub-nicho.",
        tendencias=tendencias_texto,
    )
    raw = call_gemini(prompt, api_key=api_key, max_tokens=16384)
    resultado = _extract_json(raw)
    if not isinstance(resultado, dict):
        raise GeminiError("A IA não retornou o formato esperado de parecer aprofundado.")
    return resultado