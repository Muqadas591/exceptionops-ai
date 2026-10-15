from dataclasses import dataclass
from typing import Any


@dataclass
class ConnectorOutcome:
    success: bool
    result: dict[str, Any]
    error: str | None = None


def build_email_draft(payload: dict[str, Any]) -> ConnectorOutcome:
    recipient = (payload.get("recipient") or "").strip()
    subject = (payload.get("subject") or "").strip()
    message = (payload.get("message") or "").strip()

    if not recipient or "@" not in recipient:
        return ConnectorOutcome(
            success=False,
            result={},
            error="A valid recipient email address is required.",
        )

    if not subject or not message:
        return ConnectorOutcome(
            success=False,
            result={},
            error="Email subject and message are required.",
        )

    # This action creates a draft only. No email is sent.
    return ConnectorOutcome(
        success=True,
        result={
            "connector": "safe_email_draft",
            "outcome": "draft_created",
            "sent": False,
            "recipient": recipient,
            "subject": subject,
            "body": message,
        },
    )


def simulate_accounting_action(
    payload: dict[str, Any],
) -> ConnectorOutcome:
    invoice_reference = str(
        payload.get("invoice_reference", "")
    ).strip()

    if not invoice_reference:
        return ConnectorOutcome(
            success=False,
            result={},
            error="Invoice reference is required.",
        )

    # Simulation only. No accounting system is contacted or changed.
    return ConnectorOutcome(
        success=True,
        result={
            "connector": "simulated_accounting",
            "outcome": "simulation_completed",
            "external_transaction_created": False,
            "invoice_reference": invoice_reference,
            "message": (
                "Simulated accounting validation completed. "
                "No real transaction was posted."
            ),
        },
    )


def simulate_webhook_action(
    payload: dict[str, Any],
) -> ConnectorOutcome:
    event_name = str(payload.get("event_name", "")).strip()

    if not event_name:
        return ConnectorOutcome(
            success=False,
            result={},
            error="Webhook event name is required.",
        )

    # No URL is accepted and no HTTP request is sent.
    return ConnectorOutcome(
        success=True,
        result={
            "connector": "simulated_webhook",
            "outcome": "simulation_completed",
            "request_sent": False,
            "event_name": event_name,
            "payload": payload.get("event_payload", {}),
        },
    )


def execute_connector(
    action_type: str,
    payload: dict[str, Any],
) -> ConnectorOutcome:
    if action_type == "email_draft":
        return build_email_draft(payload)

    if action_type == "accounting_simulation":
        return simulate_accounting_action(payload)

    if action_type == "webhook_simulation":
        return simulate_webhook_action(payload)

    return ConnectorOutcome(
        success=False,
        result={},
        error=f"Unsupported action type: {action_type}",
    )