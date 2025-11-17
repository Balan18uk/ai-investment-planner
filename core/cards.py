# core/cards.py

from typing import Optional


def make_projection_text(
    *,
    principal: float,
    months: int,
    rate_pct: Optional[float],
    min_investment: float,
) -> str:
    if rate_pct is None:
        return ""

    if principal < min_investment:
        return (
            "- Client budget is below the minimum investment, "
            "so projection is not shown."
        )

    years = months / 12.0
    r = rate_pct / 100.0
    future_value = principal * (1 + r) ** years
    gain = future_value - principal

    # Human readable duration
    if months < 24:
        duration_text = f"{months} months"
    else:
        whole_years = months // 12
        remaining_months = months % 12
        if remaining_months == 0:
            duration_text = f"{whole_years} years"
        else:
            duration_text = f"{whole_years} years {remaining_months} months"

    return (
        f"💡 <b>If you invest £{principal:,.0f} for {duration_text}, "
        f"the projected value could be about £{future_value:,.0f} "
        f"(gain of ~£{gain:,.0f}).</b>"
    )

def make_product_card_html(
    rec,
    *,
    principal: float,
    term_months: int,
    label: str,
    highlight: bool = False,
    bg_best: str = "#e6ffe6",   # light green
    bg_alt: str = "#f5f5f5",    # light grey
) -> str:
    """
    Build the full HTML for a single product card.

    highlight=True  -> uses bg_best
    highlight=False -> uses bg_alt
    Colours can be overridden when calling if you want a different theme.
    """
    bg_colour = bg_best if highlight else bg_alt

    lines = [
        f"<b>{rec.product_name}</b> ({rec.product_type})",
        f"- Risk level: {rec.risk_level}",
        f"- Minimum term: {rec.min_term_months} months",
        f"- Minimum investment: £{rec.min_investment:,.0f}",
    ]

    rate = getattr(rec, "expected_return_pct", None)
    if rate is not None:
        lines.append(
            f"- Indicative annual return: {rate:.1f}% "
            "(illustrative only, not guaranteed)"
        )

    projection = make_projection_text(
        principal=principal,
        months=term_months,
        rate_pct=rate,
        min_investment=rec.min_investment,
    )
    if projection:
        lines.append(projection)

    inner_html = "<br>".join(lines)

    # make the label look like a badge when highlight=True
    if highlight:
        # Green pill badge
        label_html = (
            f'<span style="display:inline-block; '
            f'background:#22c55e; color:white; padding:2px 10px; '
            f'border-radius:999px; font-size:0.8rem; font-weight:600;">'
            f'{label}</span>'
    )
    else:
        # Subtle grey label for alternatives
        label_html = (
            f'<span style="display:inline-block; '
            f'color:#666; font-size:0.8rem; font-weight:500;">'
            f'{label}</span>'
    )


    return f"""
    <div style="background-color:{bg_colour}; padding:16px;
                border-radius:10px; margin-bottom:12px;">
        <div style="margin-bottom:4px;">
            {label_html}
        </div>
        <div>{inner_html}</div>
    </div>
    """
