
import re
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class FieldCandidate:
    value: str | None
    confidence: float
    evidence: str | None


class InvoiceExtractionProvider(Protocol):
    """Interface implemented by every invoice extraction provider."""

    @property
    def name(self) -> str:
        ...

    def extract(self, text: str) -> dict[str, FieldCandidate]:
        ...


def _find_field(
    text: str,
    patterns: list[str],
    confidence: float,
    flags: int = re.IGNORECASE | re.MULTILINE,
) -> FieldCandidate:
    for pattern in patterns:
        match = re.search(pattern, text, flags)

        if match:
            value = match.group(1).strip(" \t:;#")
            evidence = match.group(0).strip()

            if value:
                return FieldCandidate(
                    value=value,
                    confidence=confidence,
                    evidence=evidence[:300],
                )

    return FieldCandidate(
        value=None,
        confidence=0.0,
        evidence=None,
    )


class RuleBasedInvoiceProvider:
    """Free, deterministic baseline. No AI model or API key required."""

    @property
    def name(self) -> str:
        return "rule_based_v1"

    def extract(self, text: str) -> dict[str, FieldCandidate]:
        invoice_number = _find_field(
            text,
            [
                r"^\s*(?:invoice\s*(?:number|no\.?|#|id))\s*[:#-]?\s*"
                r"([A-Z0-9][A-Z0-9/_-]{1,49})\s*$",
                r"^\s*(?:inv\.?\s*#)\s*[:#-]?\s*"
                r"([A-Z0-9][A-Z0-9/_-]{1,49})\s*$",
            ],
            confidence=0.90,
        )

        invoice_date = _find_field(
            text,
            [
                r"^\s*invoice\s*date\s*[:#-]?\s*"
                r"(\d{4}-\d{2}-\d{2})\s*$",
                r"^\s*invoice\s*date\s*[:#-]?\s*"
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*$",
                r"^\s*date\s*[:#-]?\s*"
                r"(\d{4}-\d{2}-\d{2})\s*$",
            ],
            confidence=0.85,
        )

        due_date = _find_field(
            text,
            [
                r"^\s*due\s*date\s*[:#-]?\s*"
                r"(\d{4}-\d{2}-\d{2})\s*$",
                r"^\s*due\s*date\s*[:#-]?\s*"
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*$",
            ],
            confidence=0.85,
        )

        # Prefer an explicitly labeled total. Avoid assuming that
        # a subtotal, tax amount, or line item is the invoice total.
        total_amount = _find_field(
            text,
            [
                r"^\s*(?:grand\s+total|invoice\s+total|total\s+due|"
                r"amount\s+due|total\s+amount|total)\s*[:\-]?\s*"
                r"(?:PKR|Rs\.?|USD|EUR|GBP|\$|€|£)?\s*"
                r"([0-9][0-9,]*(?:\.\d{1,2})?)\s*$",
            ],
            confidence=0.80,
        )

        currency = _find_field(
            text,
            [
                r"^\s*currency\s*[:#-]?\s*([A-Z]{3})\s*$",
            ],
            confidence=0.90,
            flags=re.IGNORECASE | re.MULTILINE,
        )

        if currency.value:
            currency = FieldCandidate(
                value=currency.value.upper(),
                confidence=currency.confidence,
                evidence=currency.evidence,
            )
        else:
            # Only infer currency from explicit currency markers.
            marker = re.search(
                r"\b(PKR|USD|EUR|GBP)\b|Rs\.?|\$|€|£",
                text,
                re.IGNORECASE,
            )

            if marker:
                marker_text = marker.group(0).upper()
                mapped = {
                    "RS": "PKR",
                    "RS.": "PKR",
                    "$": "USD",
                    "€": "EUR",
                    "£": "GBP",
                }
                inferred = mapped.get(marker_text, marker_text)

                if inferred in {"PKR", "USD", "EUR", "GBP"}:
                    currency = FieldCandidate(
                        value=inferred,
                        confidence=0.65,
                        evidence=marker.group(0),
                    )

        supplier_name = _find_field(
            text,
            [
                r"^\s*(?:supplier|supplier\s+name|vendor|vendor\s+name|"
                r"billed\s+by)\s*[:#-]\s*(.{2,150}?)\s*$",
            ],
            confidence=0.75,
        )

        return {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "supplier_name": supplier_name,
            "currency": currency,
            "total_amount": total_amount,
        }
