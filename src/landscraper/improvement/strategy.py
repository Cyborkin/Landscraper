"""Strategy evaluation based on cycle metrics.

Analyzes performance metrics and generates recommendations for
tuning the next cycle's behavior.
"""

from typing import Any


def evaluate_strategy(metrics: dict[str, Any]) -> list[dict[str, str]]:
    """Evaluate cycle metrics and return strategy recommendations.

    Each recommendation is a dict with:
    - area: what aspect to adjust (e.g., "scraping", "scoring", "sources")
    - recommendation: what to change
    - severity: "info", "warning", "critical"
    """
    recommendations: list[dict[str, str]] = []

    # High error rate suggests scraping issues
    error_rate = metrics.get("error_rate", 0)
    if error_rate > 0.3:
        recommendations.append({
            "area": "scraping",
            "recommendation": f"Error rate is {error_rate:.0%}. Review failing scrapers and consider disabling unreliable sources.",
            "severity": "critical",
        })
    elif error_rate > 0.1:
        recommendations.append({
            "area": "scraping",
            "recommendation": f"Error rate is {error_rate:.0%}. Monitor source health.",
            "severity": "warning",
        })

    # Low yield rate suggests too much noise
    yield_rate = metrics.get("yield_rate", 0)
    if yield_rate < 0.01 and metrics.get("total_raw_records", 0) > 10:
        recommendations.append({
            "area": "pipeline",
            "recommendation": "Very low yield rate. Consider adjusting correlation thresholds or adding keyword filters.",
            "severity": "warning",
        })

    # Low conversion rate suggests validators are too strict
    conversion_rate = metrics.get("conversion_rate", 0)
    if conversion_rate < 0.3 and metrics.get("total_developments", 0) > 5:
        recommendations.append({
            "area": "consensus",
            "recommendation": f"Low conversion rate ({conversion_rate:.0%}). Review validator rules — they may be too restrictive.",
            "severity": "warning",
        })

    # Low source diversity
    source_count = metrics.get("unique_source_count", 0)
    if source_count < 2:
        recommendations.append({
            "area": "sources",
            "recommendation": "Limited source diversity. Add more data sources for better corroboration.",
            "severity": "info",
        })

    # Mostly cold/monitor leads
    tier_dist = metrics.get("tier_distribution", {})
    total_leads = metrics.get("total_validated_leads", 0)
    hot_warm = tier_dist.get("hot", 0) + tier_dist.get("warm", 0)
    if total_leads > 5 and hot_warm / total_leads < 0.1:
        recommendations.append({
            "area": "scoring",
            "recommendation": "Few hot/warm leads. Review scoring weights — location demand or project scale may need adjustment.",
            "severity": "info",
        })

    # Low average confidence
    avg_conf = metrics.get("avg_confidence", 0)
    if avg_conf < 0.4 and total_leads > 0:
        recommendations.append({
            "area": "data_quality",
            "recommendation": f"Low average confidence ({avg_conf:.2f}). Focus on enriching leads with more complete data.",
            "severity": "warning",
        })

    # No errors and good metrics — positive feedback
    if not recommendations:
        recommendations.append({
            "area": "general",
            "recommendation": "Cycle performed well. No strategy changes recommended.",
            "severity": "info",
        })

    return recommendations
