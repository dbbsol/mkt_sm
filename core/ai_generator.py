"""
core/ai_generator.py
─────────────────────────────────────────────────────────────────
Integração com a API do Gemini + geração do parecer de cada pauta
(o que é, encaixe no nicho, gatilhos mentais, por que chama atenção).

ONDE COLAR A CHAVE GEMINI:
  → logo abaixo, na constante GEMINI_API_KEY (pedido: chave direto
    no código). Alternativas mais seguras, usadas só se a constante
    estiver vazia: .streamlit/secrets.toml, variável de ambiente
    GEMINI_API_KEY ou arquivo .env.

⚠️ Se este projeto for para o GitHub, NÃO suba a chave dentro do
   código (o Google desativa chaves expostas). Prefira o secrets.
─────────────────────────────────────────────────────────────────
"""

import os
import re
import json
import time

import requests

from config import prompts, references

GEMINI_API_KEY = ""   # ← cole sua chave Gemini aqui: GEMINI_API_KEY = "AIza..."

# Tenta na ordem; se um modelo não existir/estiver indisponível, usa o próximo.
GEMINI_MODELS = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-3.8-flash"]
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")
INSTAGRAM_ALGO_PATH = os.path.join(KNOWLEDGE_DIR, "instagram_algoritmo_2026.md")


class GeminiError(Exception):
    pass


def _clean_key(raw: str) -> str:
    """Remove espaços, quebras de linha e aspas colados por acidente na chave."""
    limpo = (raw or "").strip().strip('"').strip("'").replace("\n", "").replace("\r", "").replace(" ", "")
    if limpo.upper().startswith("GEMINI_API_KEY="):
        limpo = limpo.split("=", 1)[1].strip('"').strip("'")
    return limpo


def get_api_key() -> str:
    """Ordem: constante no código → st.secrets → variável de ambiente/.env."""
    k = _clean_key(GEMINI_API_KEY)
    if k:
        return k
    try:
        import streamlit as st
        k = _clean_key(str(st.secrets.get("GEMINI_API_KEY", "")))
        if k:
            return k
    except Exception:
        pass
    return _clean_key(os.environ.get("GEMINI_API_KEY", ""))


def carregar_algoritmo_instagram() -> str:
    """Documento opcional em knowledge/ (se estiver vazio, é simplesmente ignorado)."""
    try:
        with open(INSTAGRAM_ALGO_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def call_gemini(prompt: str, max_tokens: int = 16384) -> tuple[str, str]:
    """Retorna (texto, modelo_usado). Levanta GeminiError com mensagem clara."""
    key = get_api_key()
    if not key:
        raise GeminiError(
            "Chave do Gemini não configurada. Cole a chave na constante GEMINI_API_KEY "
            "em core/ai_generator.py (gratuita em https://aistudio.google.com)."
        )
    if len(key) < 30:
        raise GeminiError("A chave do Gemini parece incompleta (muito curta). Copie-a inteira, sem cortar caracteres.")

    last_error = "Não foi possível obter resposta da IA."
    for model in GEMINI_MODELS:
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            # Modelos Gemini 3.x não aceitam temperature/top_p: só maxOutputTokens e o mime type.
            "generationConfig": {"maxOutputTokens": max_tokens, "responseMimeType": "application/json"},
        }
        if "2.5" in model:
            body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}

        for attempt in range(3):
            try:
                # chave em `params` (nunca concatenada na URL)
                resp = requests.post(GEMINI_BASE.format(model=model), params={"key": key}, json=body, timeout=120)
            except requests.RequestException as e:
                last_error = f"Erro de conexão: {e}"
                time.sleep(2)
                continue

            if resp.status_code == 200:
                try:
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"], model
                except Exception:
                    last_error = "A IA devolveu uma resposta vazia."
                    break
            if resp.status_code == 429:
                last_error = "Limite de uso da API Gemini atingido (429). Aguarde um minuto e tente de novo."
                time.sleep(4 * (attempt + 1))
                continue

            try:
                err = resp.json().get("error", {})
                motivo = f' Motivo do Google: "{err.get("message", "")}" ({err.get("status", "")}).'
            except Exception:
                motivo = f" Resposta bruta: {resp.text[:300]}"

            if resp.status_code in (400, 401, 403) and ("API key" in resp.text or "API_KEY" in resp.text or resp.status_code in (401, 403)):
                raise GeminiError(
                    "O Google recusou a chave do Gemini." + motivo +
                    "\nGere uma chave NOVA em https://aistudio.google.com (Get API key → Create API key) "
                    "e cole em GEMINI_API_KEY."
                )
            last_error = f"Erro Gemini [{resp.status_code}] no modelo {model}.{motivo}"
            break  # tenta o próximo modelo
    raise GeminiError(last_error)


# ─── JSON tolerante (inclui resposta cortada por limite de tokens) ───
def _repair_truncated_json(text: str):
    start = min((i for i in (text.find("{"), text.find("[")) if i != -1), default=-1)
    if start == -1:
        return None
    in_string, escape, stack = False, False, []
    for c in text[start:]:
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_string = False
        elif c == '"':
            in_string = True
        elif c in "{[":
            stack.append(c)
        elif c in "}]" and stack:
            stack.pop()
    candidate = text[start:].rstrip()
    if in_string:
        candidate += '"'
    candidate = candidate.rstrip().rstrip(",")
    return candidate + "".join("}" if ch == "{" else "]" for ch in reversed(stack))


def _extract_json(raw: str):
    text = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    s = text.find("[")
    o = text.find("{")
    if s != -1 and (o == -1 or s < o):  # esperamos um array de pautas
        e = text.rfind("]")
        if e > s:
            try:
                return json.loads(text[s:e + 1])
            except json.JSONDecodeError:
                pass
        repaired = _repair_truncated_json(text)
        if repaired:
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass
        # resposta cortada no meio de um item: descarta o item incompleto
        cut = text.rfind("},")
        if cut > s:
            try:
                return json.loads(text[s:cut + 1] + "]")
            except json.JSONDecodeError:
                pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    raise GeminiError("Não consegui interpretar a resposta da IA. Tente gerar novamente.")


def gerar_pareceres_pautas(*, pautas_texto: str, nicho: str, publico: str, tom: str, rede: str,
                           sugestoes: list[str]) -> tuple[dict, str]:
    """Devolve ({id_da_pauta: parecer}, modelo_usado)."""
    algoritmo = carregar_algoritmo_instagram() if rede in ("Instagram", "Qualquer rede") else ""
    algoritmo_bloco = (f"ALGORITMO DO INSTAGRAM (base factual, use para justificar sugestões dessa rede):\n{algoritmo}\n\n"
                       if algoritmo else "")
    prompt = prompts.PROMPT_PARECER_PAUTAS.format(
        persona=prompts.SYSTEM_PERSONA,
        base_estrategica=references.build_scientific_grounding_block(),
        algoritmo_bloco=algoritmo_bloco,
        nicho=nicho,
        publico=publico or "não informado (considere o público típico do nicho)",
        tom=tom,
        rede=rede,
        sugestoes=", ".join(sugestoes[:10]) if sugestoes else "n/d",
        pautas=pautas_texto,
    )
    raw, modelo = call_gemini(prompt)
    dados = _extract_json(raw)
    if isinstance(dados, dict):  # às vezes vem embrulhado: {"pautas": [...]}
        dados = next((v for v in dados.values() if isinstance(v, list)), None)
    if not isinstance(dados, list):
        raise GeminiError("A IA não retornou o formato esperado. Tente gerar novamente.")
    out = {}
    for n, item in enumerate(dados, 1):
        if isinstance(item, dict):
            try:
                out[int(item.get("id", n))] = item
            except (TypeError, ValueError):
                out[n] = item
    return out, modelo
