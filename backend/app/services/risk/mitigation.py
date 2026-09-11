"""
Deterministic mitigation recommendations.

Maps threat types, severity levels, and observed signals to specific,
evidence-based mitigation actions. Recommendations are framed as
risk-reduction strategies, not assertions about unverified causes.
"""


def get_seasonality_mitigations(severity_score: float, low_periods: list[str]) -> list[str]:
    """
    Mitigation recommendations for seasonal demand fluctuation.
    
    Args:
        severity_score: 0-100 threat severity
        low_periods: List of months/periods with low demand
    
    Returns:
        List of actionable mitigation strategies
    """
    mitigations = []
    
    if severity_score >= 70:
        mitigations.extend([
            "Develop explicit cash-flow reserves or credit facility to cover low-season operational costs.",
            "Negotiate flexible payment terms with suppliers to reduce working-capital pressure during low periods.",
            "Identify complementary seasonal services or products to smooth revenue during low-demand periods.",
        ])
    
    if severity_score >= 50:
        mitigations.extend([
            "Conduct a detailed demand-cycle analysis to forecast low-season cash needs.",
            "Build 2-3 months of operating expenses as a reserve buffer.",
            "Create a supplier communication plan to maintain relationships and ensure continued supply during low demand.",
        ])
    
    if low_periods:
        mitigations.append(
            f"Plan inventory and staffing adjustments for identified low periods ({', '.join(low_periods)}). "
            "Monitor actual versus forecast performance monthly."
        )
    
    mitigations.append(
        "Track seasonal patterns monthly and update forecasts annually. "
        "Adjust working-capital strategy if observed seasonality changes significantly."
    )
    
    return mitigations


def get_supply_chain_mitigations(
    severity_score: float,
    supplier_count: int,
    lead_time_cv: float,
    stockout_frequency: float,
    fulfillment_rate: float,
) -> list[str]:
    """
    Mitigation recommendations for supply-chain bottleneck risk.
    
    Args:
        severity_score: 0-100 threat severity
        supplier_count: Number of active suppliers
        lead_time_cv: Lead-time coefficient of variation
        stockout_frequency: Estimated stockouts per year
        fulfillment_rate: Historical fulfillment rate (0.0-1.0)
    
    Returns:
        List of actionable mitigation strategies
    """
    mitigations = []
    
    # Supplier concentration risk
    if supplier_count <= 2:
        mitigations.extend([
            "Actively qualify and onboard at least one additional backup supplier "
            "with comparable cost, quality, and delivery capability.",
            "Conduct a formal supplier risk assessment for existing suppliers "
            "(financial stability, capacity, regulatory compliance).",
        ])
    
    if supplier_count <= 4:
        mitigations.append(
            "Establish formal supplier diversity strategy to reduce single-source dependency. "
            "Consider geographic or organizational diversity."
        )
    
    # Lead-time variability risk
    if lead_time_cv > 0.35:
        mitigations.extend([
            "Implement a supplier performance scorecard to track lead-time consistency. "
            "Set lead-time targets and penalties/bonuses.",
            "Establish a safety-stock policy to buffer against lead-time variability. "
            "Calculate optimal buffer based on demand volatility and service-level targets.",
        ])
    
    # Fulfillment/stockout risk
    if stockout_frequency > 4 or fulfillment_rate < 0.90:
        mitigations.extend([
            "Implement an order-management system to track fulfillment performance. "
            "Root-cause analyze each stockout or late delivery.",
            "Review inventory reorder points and lead times. "
            "Adjust safety stock or reorder frequency to improve fulfillment.",
            "Consider supplier agreements with minimum fill rates or penalties for non-fulfillment.",
        ])
    
    # Overall high risk
    if severity_score >= 70:
        mitigations.extend([
            "Develop a formal supply-chain continuity plan. "
            "Define alternative suppliers, logistics routes, or contingency stocks for critical inputs.",
            "Review payment terms and relationships with key suppliers. "
            "Consider upfront orders or commitments to secure supply during periods of high demand.",
        ])
    
    mitigations.append(
        "Monitor supplier performance and market conditions quarterly. "
        "Update supplier list and safety-stock strategies if risk profile changes."
    )
    
    return mitigations


def get_buyer_concentration_mitigations(
    severity_score: float,
    top_buyer_share: float,
    buyer_count: int,
    hhi: float,
) -> list[str]:
    """
    Mitigation recommendations for buyer concentration risk.
    
    Args:
        severity_score: 0-100 threat severity
        top_buyer_share: Sales share of largest buyer (0.0-1.0)
        buyer_count: Total distinct buyers
        hhi: Herfindahl-Hirschman Index (0-10000)
    
    Returns:
        List of actionable mitigation strategies
    """
    mitigations = []
    
    # High concentration: one buyer > 50%
    if top_buyer_share > 0.50:
        mitigations.extend([
            "Develop a customer diversification roadmap. "
            "Target specific market segments, geographies, or buyer types to reduce top-buyer share to <40%.",
            "Document the top buyer's payment terms, contract length, and renewal conditions. "
            "Prepare contingency plans for contract termination or volume reduction.",
            "Proactively engage with the top buyer: understand their changing needs, "
            "offer new products/services, and negotiate multi-year agreements if beneficial.",
        ])
    
    # Moderate concentration: top 3 > 75%
    if top_buyer_share > 0.35 and hhi > 2500:
        mitigations.extend([
            "Accelerate customer acquisition for lower-concentration growth. "
            "Set sales targets to add 3-5 new buyers of meaningful size within 12 months.",
            "Review pricing and terms with major buyers to ensure profitability and flexibility.",
        ])
    
    # Low buyer count
    if buyer_count < 10:
        mitigations.append(
            "Build a customer acquisition and retention strategy tailored to your market. "
            "Aim for at least 10-15 buyers to reduce single-customer dependency."
        )
    
    # Overall high risk
    if severity_score >= 70:
        mitigations.extend([
            "Implement a customer relationship management (CRM) system to track buyer health, "
            "contract terms, and renewal dates.",
            "Create a sales and marketing budget explicitly for customer diversification. "
            "Track progress toward concentration reduction targets monthly.",
        ])
    
    mitigations.append(
        "Review customer composition and concentration quarterly. "
        "Monitor buyer health and industry trends that could affect demand. "
        "Adjust diversification strategy if concentration increases or major buyers signal changes."
    )
    
    return mitigations
