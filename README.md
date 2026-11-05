# 🔶 Inteligência Editorial

Radar de tendências em alta + parecer estratégico do Gemini: o que é cada pauta,
como encaixá-la no seu nicho, quais gatilhos mentais usar e por que ela chama a atenção.

## Rodar
```
pip install -r requirements.txt
streamlit run app.py
```

## Chave Gemini
Cole em `core/ai_generator.py`, na constante `GEMINI_API_KEY`.
Para publicar no GitHub/Streamlit Cloud, deixe a constante vazia e use
*App settings → Secrets*: `GEMINI_API_KEY = "sua-chave"`.

## Estrutura
- `app.py` — interface (uma aba: Radar de tendências em alta)
- `config/niches.py` — 30 nichos macro, tons e redes (adicione linhas para criar novos)
- `config/prompts.py` — prompt do parecer
- `config/references.py` — guard-rails éticos
- `core/trends_engine.py` — fontes gratuitas, cruzamento e ranking
- `core/ai_generator.py` — Gemini
- `database/db.py` — não é mais usado pelo app (pode ficar ou ser removido)

## Fontes (gratuitas, sem chave)
Google Trends BR/EUA, Wikipédia, Google News (nicho e editoria), Bing News, G1,
Reddit r/brasil, Hacker News (nichos de tecnologia) e Google Suggest.
Opcional: YouTube, com `YOUTUBE_API_KEY` (chave gratuita) no `.env`.
