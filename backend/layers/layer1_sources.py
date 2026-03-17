"""
layer1_sources.py — News source trust scores and catalyst metadata.
"""

# ── Source Trust Scores ───────────────────────────────────────────────────────
SOURCE_TRUST = {
    # Tier 1 — Premium financial wire services (0.90-1.00)
    "reuters":                     0.95,
    "bloomberg":                   0.95,
    "the economic times":          0.90,
    "economic times":              0.90,
    "et markets":                  0.90,
    "financial times":             0.90,
    "wall street journal":         0.88,

    # Tier 2 — Quality Indian financial media (0.75-0.89)
    "mint":                        0.85,
    "livemint":                    0.85,
    "moneycontrol":                0.83,
    "business standard":           0.83,
    "business today":              0.80,
    "cnbc tv18":                   0.80,
    "cnbctv18":                    0.80,
    "ndtv profit":                 0.78,
    "zee business":                0.75,

    # Tier 3 — General news with financial coverage (0.60-0.74)
    "the hindu":                   0.72,
    "hindustan times":             0.70,
    "times of india":              0.68,
    "india today":                 0.65,
    "ndtv":                        0.65,
    "press trust of india":        0.72,
    "pti":                         0.72,
    "ani":                         0.68,

    # Tier 4 — International general media (0.55-0.65)
    "associated press":            0.65,
    "ap":                          0.65,
    "afp":                         0.62,
    "guardian":                    0.60,
    "bbc":                         0.60,

    # Default for unknown sources
    "_default":                    0.50,
}

# ── Catalyst Type Definitions ────────────────────────────────────────────────
# Each type has: direction (long/short/both), base_intensity, intraday_relevance
CATALYST_TYPES = {
    # Long catalysts
    "earnings_beat":        {"direction": "long",  "base": 0.80, "relevance": "HIGH"},
    "guidance_raised":      {"direction": "long",  "base": 0.75, "relevance": "HIGH"},
    "product_launch":       {"direction": "long",  "base": 0.65, "relevance": "HIGH"},
    "contract_win":         {"direction": "long",  "base": 0.70, "relevance": "HIGH"},
    "acquisition_positive": {"direction": "long",  "base": 0.60, "relevance": "MEDIUM"},
    "fii_buying":           {"direction": "long",  "base": 0.65, "relevance": "HIGH"},
    "promoter_buying":      {"direction": "long",  "base": 0.60, "relevance": "MEDIUM"},
    "dividend_declared":    {"direction": "long",  "base": 0.50, "relevance": "MEDIUM"},
    "buyback_announced":    {"direction": "long",  "base": 0.55, "relevance": "MEDIUM"},
    "capacity_expansion":   {"direction": "long",  "base": 0.55, "relevance": "LOW"},
    "sector_tailwind":      {"direction": "long",  "base": 0.45, "relevance": "MEDIUM"},

    # Short catalysts
    "earnings_miss":        {"direction": "short", "base": 0.80, "relevance": "HIGH"},
    "guidance_cut":         {"direction": "short", "base": 0.80, "relevance": "HIGH"},
    "regulatory_action":    {"direction": "short", "base": 0.85, "relevance": "HIGH"},
    "sebi_notice":          {"direction": "short", "base": 0.88, "relevance": "HIGH"},
    "ed_raid":              {"direction": "short", "base": 0.90, "relevance": "HIGH"},
    "management_exit":      {"direction": "short", "base": 0.72, "relevance": "HIGH"},
    "promoter_pledge":      {"direction": "short", "base": 0.70, "relevance": "MEDIUM"},
    "fii_selling":          {"direction": "short", "base": 0.65, "relevance": "HIGH"},
    "debt_concern":         {"direction": "short", "base": 0.68, "relevance": "MEDIUM"},
    "litigation_risk":      {"direction": "short", "base": 0.65, "relevance": "MEDIUM"},
    "sector_headwind":      {"direction": "short", "base": 0.45, "relevance": "MEDIUM"},

    # Neutral / mixed
    "general_news":         {"direction": "both",  "base": 0.30, "relevance": "LOW"},
    "analyst_coverage":     {"direction": "both",  "base": 0.40, "relevance": "MEDIUM"},
    "results_preview":      {"direction": "both",  "base": 0.50, "relevance": "HIGH"},
}


def get_source_trust(source_name: str) -> float:
    """
    Return trust score for a news source.
    Case-insensitive lookup with fallback to default.
    """
    if not source_name:
        return SOURCE_TRUST["_default"]
    name_lower = source_name.lower().strip()
    if name_lower in SOURCE_TRUST:
        return SOURCE_TRUST[name_lower]
    for key, score in SOURCE_TRUST.items():
        if key != "_default" and (key in name_lower or name_lower in key):
            return score
    return SOURCE_TRUST["_default"]


def get_catalyst_info(catalyst_type: str) -> dict:
    """Return catalyst metadata. Falls back to general_news."""
    return CATALYST_TYPES.get(catalyst_type, CATALYST_TYPES["general_news"])

