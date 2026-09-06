"""
utils/helpers.py — funções utilitárias transversais (sem lógica de negócio).
"""


def truncar(texto: str, tamanho: int = 80) -> str:
    if not texto:
        return ""
    return texto if len(texto) <= tamanho else texto[: tamanho - 1] + "…"