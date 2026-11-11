
from __future__ import annotations

import argparse
import getpass
import json
import sys
import uuid

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MANIFEST = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "demo_manifest.json"
)

DEFAULT_INVOICE_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "invoices"
)

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "run-results"
    / "latest-run.json"
)

DEFAULT_BASE_URL = "http://127.0.0.1:8001"


class DemoAPIError(Exception):
    def __init__(
        self,
        status_code: int,
        payload: Any,
    ):
        self.status_code = status_code
        self.payload = payload

        super().__init__(
            f"API request failed with HTTP {status_code}: "
            f"{payload}"
        )


class ExceptionOpsClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        raw_body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        request_headers = {
            "Accept": "application/json",
        }

        if self.token:
            request_headers["Authorization"] = (
                f"Bearer {self.token}"
            )

        if headers:
            request_headers.update(headers)

        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            request_headers["Content-Type"] = (
                "application/json"
            )
        elif raw_body is not None:
            body = raw_body
        elif method.upper() in {"POST", "PUT", "PATCH"}:
            body = b""
        else:
            body = None

        request = Request(
            url=f"{self.base_url}{path}",
            data=body,
            headers=request_headers,
            method=method.upper(),
        )

        try:
            with urlopen(request, timeout=60) as response:
                response_body = response.read()

        except HTTPError as exc:
            response_body = exc.read()

            try:
                error_payload = json.loads(
                    response_body.decode("utf-8")
                )
            except (UnicodeDecodeError, json.JSONDecodeError):
                error_payload = {
                    "message": "The API returned an unreadable error."
                }

            raise DemoAPIError(
                exc.code,
                error_payload,
            ) from exc

        except URLError as exc:
            raise RuntimeError(
                "Could not connect to the ExceptionOps API. "
                "Check the API port and server status."
            ) from exc

        if not response_body:
            return {}

        try:
            return json.loads(
                response_body.decode("utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError):
            return response_body.decode(
                "utf-8",
                errors="replace",
            )

    def verify_application(self) -> dict[str, Any]:
        health = self.request("/api/v1/health")

        if health.get("app_name") != "ExceptionOps AI":
            raise RuntimeError(
                "The configured API does not identify itself "
                "as ExceptionOps AI. "
                f"Received: {health.get('app_name')!r}. "
                "Check the base URL before continuing."
            )

        if health.get("status") != "ok":
            raise RuntimeError(
                "The ExceptionOps API did not report a healthy "
                "liveness status."
            )

        return health

    def login(
        self,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        response = self.request(
            "/api/v1/auth/login",
            method="POST",
            payload={
                "email": email,
                "password": password,
            },
        )

        self.token = response["access_token"]

        user = response["user"]
        role = user.get("role")

        if role not in {"admin", "reviewer"}:
            self.token = None

            raise RuntimeError(
                "The demonstration runner requires an admin "
                "or reviewer account. "
                f"The authenticated account has role {role!r}."
            )

        return user

    def upload_document(
        self,
        file_path: Path,
    ) -> tuple[dict[str, Any], bool]:
        boundary = (
            "----ExceptionOpsDemo"
            + uuid.uuid4().hex
        )

        content = file_path.read_bytes()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; '
            f'filename="{file_path.name}"\r\n'
            "Content-Type: text/plain; charset=utf-8\r\n"
            "\r\n"
        ).encode("utf-8")

        body += content

        body += (
            f"\r\n--{boundary}--\r\n"
        ).encode("utf-8")

        headers = {
            "Content-Type": (
                f"multipart/form-data; boundary={boundary}"
            ),
        }

        try:
            result = self.request(
                "/api/v1/documents",
                method="POST",
                raw_body=body,
                headers=headers,
            )

            return result, False

        except DemoAPIError as exc:
            # Reuse an identical existing document rather than
            # creating a duplicate or modifying the database.
            if exc.status_code == 409:
                detail = (
                    exc.payload.get("detail", {})
                    if isinstance(exc.payload, dict)
                    else {}
                )

                if isinstance(detail, dict):
                    document_id = detail.get("document_id")

                    if document_id is not None:
                        existing = self.request(
                            f"/api/v1/documents/{document_id}"
                        )
                        return existing, True

            raise

    def extract_document(
        self,
        document_id: int,
    ) -> dict[str, Any]:
        return self.request(
            f"/api/v1/documents/{document_id}/extract",
            method="POST",
        )

    def evaluate_document(
        self,
        document_id: int,
    ) -> dict[str, Any]:
        return self.request(
            f"/api/v1/documents/{document_id}/evaluate",
            method="POST",
        )

    def create_workflow(
        self,
        document_id: int,
        scenario: str,
    ) -> dict[str, Any]:
        return self.request(
            f"/api/v1/documents/{document_id}/workflow",
            method="POST",
            headers={
                "Idempotency-Key": (
                    f"synthetic-demo-{scenario}-v1"
                ),
            },
        )

    def advance_workflow(
        self,
        workflow_id: int,
    ) -> dict[str, Any]:
        return self.request(
            f"/api/v1/workflows/{workflow_id}/advance",
            method="POST",
        )

    def create_or_get_review(
        self,
        workflow_id: int,
    ) -> dict[str, Any]:
        return self.request(
            f"/api/v1/workflows/{workflow_id}/review",
            method="POST",
        )


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Manifest not found: {path}. "
            "Generate the synthetic dataset first."
        )

    manifest = json.loads(
        path.read_text(encoding="utf-8")
    )

    if manifest.get("is_synthetic") is not True:
        raise ValueError(
            "The manifest is not marked as synthetic."
        )

    records = manifest.get("records")

    if not isinstance(records, list) or not records:
        raise ValueError(
            "The manifest does not contain demo records."
        )

    return manifest


def run_demo(
    client: ExceptionOpsClient,
    manifest: dict[str, Any],
    invoice_dir: Path,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    for index, record in enumerate(
        manifest["records"],
        start=1,
    ):
        scenario = record["scenario"]
        filename = record["filename"]
        invoice_path = invoice_dir / filename

        if not invoice_path.is_file():
            raise FileNotFoundError(
                f"Demo invoice not found: {invoice_path}"
            )

        print()
        print(
            f"[{index}/{len(manifest['records'])}] "
            f"Processing {scenario}"
        )

        document, reused_document = (
            client.upload_document(invoice_path)
        )

        document_id = int(document["id"])

        print(
            f"  Document ID: {document_id}"
            + (" (reused)" if reused_document else "")
        )

        extraction = client.extract_document(
            document_id
        )

        print(
            f"  Extraction: {extraction.get('status')}"
        )

        evaluation = client.evaluate_document(
            document_id
        )

        actual_decision = evaluation["decision"]
        expected_decision = record["expected_decision"]

        actual_findings = {
            finding.get("rule_code")
            for finding in evaluation.get("findings", [])
        }

        expected_findings = set(
            record.get("expected_findings", [])
        )

        missing_findings = sorted(
            expected_findings - actual_findings
        )

        decision_matches = (
            actual_decision == expected_decision
        )

        findings_match = not missing_findings

        print(
            f"  Evaluation: {actual_decision}"
        )

        if missing_findings:
            print(
                "  Missing expected findings: "
                + ", ".join(missing_findings)
            )

        workflow = client.create_workflow(
            document_id,
            scenario,
        )

        workflow_id = int(workflow["id"])

                # Advance only workflows that still need processing.
        # Existing evaluated or review workflows are not advanced again.
        if workflow.get("status") in {
            "received",
            "failed",
            "extracted",
        }:
            workflow = client.advance_workflow(
                workflow_id
            )

        workflow_status = workflow["status"]

        print(
            f"  Workflow: {workflow_id} "
            f"({workflow_status})"
        )

        review = None

        if workflow_status in {
            "needs_review",
            "evaluated",
        }:
            review = client.create_or_get_review(
                workflow_id
            )

            print(
                f"  Review: {review['id']} "
                f"({review['status']})"
            )

        results.append(
            {
                "demo_record_id": record["demo_record_id"],
                "scenario": scenario,
                "document_id": document_id,
                "document_reused": reused_document,
                "extraction_status": extraction.get("status"),
                "evaluation_id": evaluation["id"],
                "expected_decision": expected_decision,
                "actual_decision": actual_decision,
                "decision_matches": decision_matches,
                "expected_findings": sorted(expected_findings),
                "actual_findings": sorted(actual_findings),
                "missing_expected_findings": missing_findings,
                "findings_match": findings_match,
                "workflow_id": workflow_id,
                "workflow_status": workflow_status,
                "review_id": review["id"] if review else None,
                "review_status": review["status"] if review else None,
            }
        )

    all_decisions_match = all(
        item["decision_matches"]
        for item in results
    )

    all_findings_match = all(
        item["findings_match"]
        for item in results
    )

    return {
        "application": "ExceptionOps AI",
        "demo_name": manifest["dataset_name"],
        "demo_version": manifest["dataset_version"],
        "is_synthetic": True,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "record_count": len(results),
        "decision_checks_passed": all_decisions_match,
        "finding_checks_passed": all_findings_match,
        "status": (
            "passed"
            if all_decisions_match and all_findings_match
            else "expectation_mismatch"
        ),
        "results": results,
        "safety_note": (
            "No review was approved and no external action "
            "was automatically executed by this runner."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the ExceptionOps AI synthetic demonstration "
            "through the real API."
        )
    )

    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=(
            "API base URL. Example: "
            "http://127.0.0.1:8001"
        ),
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Existing admin or reviewer account email.",
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
    )

    parser.add_argument(
        "--invoice-dir",
        type=Path,
        default=DEFAULT_INVOICE_DIR,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    args = parser.parse_args()

    password = getpass.getpass(
        "ExceptionOps account password: "
    )

    try:
        manifest = load_manifest(args.manifest)

        client = ExceptionOpsClient(
            args.base_url
        )

        health = client.verify_application()

        print(
            f"Connected to {health['app_name']} "
            f"({health['environment']})"
        )

        user = client.login(
            args.email,
            password,
        )

        print(
            f"Authenticated as {user['email']} "
            f"with role {user['role']}"
        )

        report = run_demo(
            client,
            manifest,
            args.invoice_dir,
        )

        args.output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.output.write_text(
            json.dumps(
                report,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        print()
        print("Synthetic demonstration finished.")
        print(f"Status: {report['status']}")
        print(f"Records: {report['record_count']}")
        print(f"Report: {args.output}")

        if report["status"] != "passed":
            print(
                "One or more actual results did not match "
                "the documented expectations."
            )
            return 2

        return 0

    except (
        DemoAPIError,
        FileNotFoundError,
        ValueError,
        RuntimeError,
        KeyError,
        OSError,
    ) as exc:
        print(
            f"DEMO FAILED: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
