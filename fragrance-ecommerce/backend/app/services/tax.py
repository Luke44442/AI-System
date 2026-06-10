"""Sales tax calculation.

A pragmatic US destination-based tax estimator using average combined
state + local rates. This is intentionally simple and overridable: for full
compliance, swap `estimate_tax_rate` for a TaxJar / Stripe Tax / Avalara call —
the call sites only depend on `calculate_tax(subtotal, address)`.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP

# Average combined (state + local) sales tax rates by US state code.
# Source: Tax Foundation combined averages, rounded. NH/OR/MT/DE/AK ~ 0% state.
US_STATE_TAX_RATES: dict[str, Decimal] = {
    "AL": Decimal("0.0924"), "AK": Decimal("0.0176"), "AZ": Decimal("0.0840"),
    "AR": Decimal("0.0947"), "CA": Decimal("0.0882"), "CO": Decimal("0.0777"),
    "CT": Decimal("0.0635"), "DE": Decimal("0.0000"), "FL": Decimal("0.0702"),
    "GA": Decimal("0.0735"), "HI": Decimal("0.0444"), "ID": Decimal("0.0602"),
    "IL": Decimal("0.0882"), "IN": Decimal("0.0700"), "IA": Decimal("0.0694"),
    "KS": Decimal("0.0869"), "KY": Decimal("0.0600"), "LA": Decimal("0.0955"),
    "ME": Decimal("0.0550"), "MD": Decimal("0.0600"), "MA": Decimal("0.0625"),
    "MI": Decimal("0.0600"), "MN": Decimal("0.0749"), "MS": Decimal("0.0707"),
    "MO": Decimal("0.0825"), "MT": Decimal("0.0000"), "NE": Decimal("0.0694"),
    "NV": Decimal("0.0823"), "NH": Decimal("0.0000"), "NJ": Decimal("0.0660"),
    "NM": Decimal("0.0778"), "NY": Decimal("0.0852"), "NC": Decimal("0.0698"),
    "ND": Decimal("0.0696"), "OH": Decimal("0.0723"), "OK": Decimal("0.0899"),
    "OR": Decimal("0.0000"), "PA": Decimal("0.0634"), "RI": Decimal("0.0700"),
    "SC": Decimal("0.0744"), "SD": Decimal("0.0640"), "TN": Decimal("0.0955"),
    "TX": Decimal("0.0820"), "UT": Decimal("0.0719"), "VT": Decimal("0.0624"),
    "VA": Decimal("0.0577"), "WA": Decimal("0.0929"), "WV": Decimal("0.0655"),
    "WI": Decimal("0.0543"), "WY": Decimal("0.0536"), "DC": Decimal("0.0600"),
}

DEFAULT_RATE = Decimal("0.0000")  # No tax for unknown / international destinations.


def estimate_tax_rate(address: dict | None) -> Decimal:
    """Return the estimated combined tax rate for a shipping address."""
    if not address:
        return DEFAULT_RATE
    country = (address.get("country") or "US").upper()
    if country not in ("US", "USA", "UNITED STATES"):
        return DEFAULT_RATE
    state = (address.get("state") or "").strip().upper()
    return US_STATE_TAX_RATES.get(state, DEFAULT_RATE)


def calculate_tax(taxable_amount: Decimal, address: dict | None) -> Decimal:
    """Calculate sales tax on a taxable amount for a destination address.

    Returns a Decimal rounded to cents. Tax is applied to the post-discount
    merchandise subtotal (shipping is treated as non-taxable here).
    """
    rate = estimate_tax_rate(address)
    if rate <= 0 or taxable_amount <= 0:
        return Decimal("0.00")
    tax = (taxable_amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return tax
