# 📡 mkt_sm — Radar de Tendências & Parecer Aprofundado

Sistema que mapeia tendências em 6 fontes (com coleta propositalmente profunda)
e usa o Gemini para produzir um **parecer ultra aprofundado**: agrupa
tendências em macro-temas, dá múltiplos exemplos táticos por tema e entrega
ideias de conteúdo — tudo cruzado com o algoritmo do Instagram 2026 e os
insights reais do(a) profissional.

Instância desta cópia: **Social Media, Marketing Digital e Estratégia de
Posicionamento** (nutricionista era a instância original — ver `config/niches.py`
pra trocar de volta ou clonar pra outro nicho).

---

## 1. Estrutura de pastas

```
mkt_sm/
│
├── app.py                    # Interface Streamlit
├── requirements.txt
├── README.md
├── .env.example                # copie para .env e preencha suas chaves
├── .gitignore
│
├── config/
│   ├── niches.py                # nichos, sub-nichos, dores, cores de marca
│   ├── prompts.py                # templates de prompt (o parecer aprofundado está aqui)
│   └── references.py             # base estratégica interna (guard-rails éticos)
│
├── core/
│   ├── ai_generator.py           # integração Gemini + geração do parecer aprofundado
│   └── trends_engine.py          # coleta e scoring das 6 fontes de tendências (mapeamento profundo)
│
├── knowledge/
│   └── instagram_algoritmo_2026.md   # base factual do algoritmo — edite à vontade
│
├── database/
│   └── db.py                     # SQLite: insights + histórico de pareceres
│
└── utils/
    └── helpers.py
```

---

## 2. O que mudou nesta versão (em relação à cópia de nutrição)

**A) Mapeamento de tendências mais profundo**
- Cada fonte agora coleta até 25 itens (antes eram 15) — mais volume bruto de sinal.
- `build_trend_intelligence()` retorna até 25 tendências rankeadas (antes 15).
- YouTube: busca por até 10 dias atrás (antes 7) e 20 resultados (antes 12).

**B) Parecer Ultra Aprofundado (novo)**
- Antes: "Inteligência Editorial" gerava um diagnóstico + lista de ideias.
- Agora: `core/ai_generator.gerar_parecer_aprofundado()` produz uma leitura
  MUITO mais densa — a IA é instruída explicitamente a:
  1. Agrupar tendências dispersas em **macro-temas** (não tratar cada uma isolada).
  2. Dar **no mínimo 3 exemplos táticos concretos** por macro-tema (regra
     obrigatória no prompt, não sugestão).
  3. Escrever um **resumo geral denso** (3-6 parágrafos), citando tendências
     específicas, não generalidades.
  4. Nomear o sinal de algoritmo/comportamento que cada ideia mira.
- `max_tokens` da chamada subiu para 16384 (era 8192) — a resposta é
  intencionalmente longa, então o teto de tokens precisa acompanhar.
- Interface: botão único e explícito **"🧠 GERAR PARECER ULTRA APROFUNDADO
  COM IA"**, na aba "Radar de Tendências", logo abaixo da lista de tendências
  brutas.

**C) Nicho adaptado**
- `config/niches.py`: nova entrada `social_media_marketing` com sub-nichos
  (gestão de tráfego, gestão de redes sociais, branding/posicionamento,
  growth/funil, marca pessoal, conteúdo/copywriting).
- `config/references.py`: guard-rails trocados de "ética científica/nutrição"
  pra "ética de marketing" (nunca prometer resultado garantido, nunca sugerir
  growth hacking antiético, nunca dark patterns manipulativos).

---

## 3. Onde colocar cada chave de API

Copie `.env.example` para `.env` (mesma pasta do `app.py`) e preencha:

| Variável | Obrigatória? | Onde conseguir |
|---|---|---|
| `GEMINI_API_KEY` | **Sim** | https://aistudio.google.com (grátis) — botão "Get API key" → "Create API key". **Não** use uma chave criada no Google Cloud Console pra outra API. |
| `YOUTUBE_API_KEY` | Não (fonte é pulada sem ela) | console.cloud.google.com → criar projeto → ativar "YouTube Data API v3" → Credenciais → Criar chave |
| `PINTEREST_ACCESS_TOKEN` | Não (fonte é pulada sem ela) | Requer conta de negócios Pinterest + app aprovado pela Pinterest. Docs: developers.pinterest.com/docs/analytics-and-reports/trends |

Google Trends, Google News, Wikipedia e Hacker News **não precisam de chave**.

---

## 4. Instalar e executar

```bash
cd mkt_sm
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1

pip install -r requirements.txt

cp .env.example .env
# edite o .env e cole suas chaves

streamlit run app.py
```

Abre em `http://localhost:8501`.

---

## 5. Como usar

1. **💡 Insights de Mercado** — registre observações reais (padrões que você
   nota com clientes, objeções recorrentes, etc). Isso ancora o parecer na
   sua experiência real.
2. **📡 Radar de Tendências**:
   - Clique em "Atualizar tendências" pra coletar as 6 fontes em profundidade
     (grátis, sem custo de IA — é só coleta bruta).
   - Clique em "Gerar Parecer Ultra Aprofundado com IA" — o Gemini lê TODAS
     as tendências coletadas + o algoritmo do Instagram + seus insights, e
     devolve: resumo geral denso, macro-temas (cada um com 3+ exemplos
     táticos), score de momento, ideias de conteúdo e riscos a evitar.
3. **📚 Histórico** — todo parecer gerado fica salvo pra consultar depois.

---

## 6. Publicar no GitHub

```bash
git init
git add .
git commit -m "mkt_sm — Radar de Tendências e Parecer Aprofundado"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```

O `.gitignore` já ignora `.env`, `database/app_data.db` e `__pycache__/`.

---

## 7. Personalizando para outro nicho

Edite `config/niches.py`, troque `PROFISSIONAL_ATIVO` pra outra chave do
dicionário `PROFISSOES` (o esqueleto de nutricionista ficou lá como
referência de como adicionar mais um). Nenhum arquivo em `core/` precisa mudar.