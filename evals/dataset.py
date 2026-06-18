"""Eval dataset — representative financial queries with expected key points.

All items are answerable from general financial knowledge (no uploaded documents
required), so the harness runs without Postgres. Each item carries:

  id          unique short id
  query       the user question
  category    definition | factual | calculation | analysis | reasoning | comparison
  complexity  "simple"  → a definition / short factual answer
              "complex" → multi-step reasoning, calculation, comparison, analysis
  key_points  concept strings expected in a good answer (for deterministic coverage)
"""

DATASET = [
    # ---------------------------------------------------------------- simple
    {
        "id": "cpr-def",
        "query": "What is CPR in mortgage finance?",
        "category": "definition",
        "complexity": "simple",
        "key_points": ["conditional prepayment rate", "annual", "prepay"],
    },
    {
        "id": "smm-def",
        "query": "Define SMM (single monthly mortality) in prepayment modeling.",
        "category": "definition",
        "complexity": "simple",
        "key_points": ["single monthly mortality", "month", "prepay"],
    },
    {
        "id": "psa-def",
        "query": "What does the PSA benchmark represent in prepayment modeling?",
        "category": "definition",
        "complexity": "simple",
        "key_points": ["prepayment", "benchmark", "ramp"],
    },
    {
        "id": "mbs-def",
        "query": "What is a mortgage-backed security?",
        "category": "definition",
        "complexity": "simple",
        "key_points": ["pool", "mortgage", "securit"],
    },
    {
        "id": "duration-def",
        "query": "What is duration in fixed income?",
        "category": "definition",
        "complexity": "simple",
        "key_points": ["interest rate", "sensitiv", "price"],
    },
    {
        "id": "ytm-def",
        "query": "What is yield to maturity?",
        "category": "definition",
        "complexity": "simple",
        "key_points": ["return", "maturity", "bond"],
    },
    {
        "id": "ltv-def",
        "query": "What does the loan-to-value (LTV) ratio measure?",
        "category": "factual",
        "complexity": "simple",
        "key_points": ["loan", "value", "ratio"],
    },
    {
        "id": "bps-def",
        "query": "What is a basis point?",
        "category": "factual",
        "complexity": "simple",
        "key_points": ["0.01", "percent", "hundredth"],
    },
    {
        "id": "prepay-risk-def",
        "query": "What is prepayment risk?",
        "category": "definition",
        "complexity": "simple",
        "key_points": ["early", "repay", "reinvest"],
    },
    {
        "id": "wal-def",
        "query": "What is weighted average life (WAL) of a bond?",
        "category": "definition",
        "complexity": "simple",
        "key_points": ["average", "principal", "time"],
    },

    # --------------------------------------------------------------- complex
    {
        "id": "smm-to-cpr-calc",
        "query": "A mortgage pool has a single monthly mortality (SMM) of 1%. "
                 "Approximately what is the annualized CPR? Show the formula.",
        "category": "calculation",
        "complexity": "complex",
        "key_points": ["1 - (1 - smm)", "12", "11"],
    },
    {
        "id": "duration-price-calc",
        "query": "A bond has a modified duration of 5 and its yield rises by 50 "
                 "basis points. Estimate the percentage change in its price.",
        "category": "calculation",
        "complexity": "complex",
        "key_points": ["2.5", "decrease", "duration"],
    },
    {
        "id": "rates-prepay-reasoning",
        "query": "Explain how rising interest rates affect mortgage prepayment "
                 "speeds, and why.",
        "category": "reasoning",
        "complexity": "complex",
        "key_points": ["rising", "slower", "refinanc", "incentive"],
    },
    {
        "id": "neg-convexity",
        "query": "How does negative convexity affect MBS valuation when interest "
                 "rates fall?",
        "category": "analysis",
        "complexity": "complex",
        "key_points": ["prepay", "convexity", "price"],
    },
    {
        "id": "cpr-vs-psa",
        "query": "Compare CPR and the PSA model as prepayment measures, including "
                 "when each is more useful.",
        "category": "comparison",
        "complexity": "complex",
        "key_points": ["constant", "ramp", "season", "benchmark"],
    },
    {
        "id": "stress-test",
        "query": "Walk through how you would stress test a mortgage portfolio for "
                 "interest-rate risk.",
        "category": "analysis",
        "complexity": "complex",
        "key_points": ["scenario", "shock", "duration", "convexity"],
    },
    {
        "id": "prepay-wal",
        "query": "Explain the relationship between prepayment speed and the "
                 "weighted average life of an MBS.",
        "category": "reasoning",
        "complexity": "complex",
        "key_points": ["faster", "shorter", "average life"],
    },
    {
        "id": "subordinate-tranche-risk",
        "query": "Analyze the key risk factors when investing in subordinate MBS "
                 "tranches.",
        "category": "analysis",
        "complexity": "complex",
        "key_points": ["credit", "subordinat", "loss"],
    },
    {
        "id": "treasury-rate-risk",
        "query": "Compare the interest-rate risk of a 2-year Treasury versus a "
                 "10-year Treasury.",
        "category": "comparison",
        "complexity": "complex",
        "key_points": ["longer", "duration", "sensitiv"],
    },
    {
        "id": "seasoned-pool-forecast",
        "query": "How would you forecast prepayment for a seasoned 30-year "
                 "mortgage pool?",
        "category": "reasoning",
        "complexity": "complex",
        "key_points": ["season", "burnout", "incentive"],
    },
]
