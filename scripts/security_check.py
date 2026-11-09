
import argparse
import sys

from app.core.config import (
    get_settings,
    is_absolute_storage_path,
    is_valid_production_secret,
)


def run_security_checks(
    require_production: bool = False,
) -> int:
    try:
        settings = get_settings()

    except Exception:
        print(
            "[FAIL] Configuration could not be loaded."
        )
        print(
            "Check your environment configuration and "
            "production security requirements."
        )
        print(
            "Sensitive configuration values were not printed."
        )
        return 1

    production = settings.is_production

    results: list[tuple[str, str, str]] = []

    def add(
        name: str,
        passed: bool,
        detail: str,
    ):
        results.append(
            (
                "PASS" if passed else "FAIL",
                name,
                detail,
            )
        )

    def warn(
        name: str,
        detail: str,
    ):
        results.append(
            (
                "WARN",
                name,
                detail,
            )
        )

    add(
        "Authentication secret",
        is_valid_production_secret(
            settings.auth_secret_key
        ),
        "Secret is configured and passes basic strength checks.",
    )

    add(
        "Wildcard CORS",
        all(
            "*" not in origin
            for origin in settings.cors_origins_list
        ),
        "CORS origins must not contain wildcards.",
    )

    add(
        "Trusted hosts",
        bool(settings.allowed_hosts_list)
        and all(
            "*" not in host
            for host in settings.allowed_hosts_list
        ),
        "Trusted hosts must be explicitly configured.",
    )

    add(
        "API token lifetime",
        5 <= settings.access_token_expire_minutes <= 60,
        "Access token lifetime must remain between 5 and 60 minutes.",
    )

    if production:
        add(
            "Production environment",
            True,
            "APP_ENV is production.",
        )

        add(
            "Debug mode",
            not settings.debug,
            "Debug mode must be disabled.",
        )

        add(
            "API documentation",
            not settings.docs_enabled,
            "Interactive API documentation is disabled.",
        )

        add(
            "Database type",
            not settings.database_url.startswith("sqlite"),
            "Production must use a persistent database.",
        )

        add(
            "Document storage path",
            is_absolute_storage_path(
                settings.document_storage_dir
            ),
            "Production document storage must use an absolute path.",
        )

    else:
        if require_production:
            add(
                "Production environment",
                False,
                "APP_ENV must be production.",
            )
        else:
            warn(
                "Production environment",
                "Current configuration is not production.",
            )

        warn(
            "Production-only checks",
            "Some checks require APP_ENV=production.",
        )

    failures = 0
    warnings = 0

    print("\nExceptionOps AI — Security Configuration Review")
    print("=" * 58)

    for status, name, detail in results:
        print(
            f"[{status}] {name}: {detail}"
        )

        if status == "FAIL":
            failures += 1

        elif status == "WARN":
            warnings += 1

    print("=" * 58)

    print(f"Passed: {len(results) - failures - warnings}")
    print(f"Warnings: {warnings}")
    print(f"Failures: {failures}")

    if failures:
        print("\nSECURITY CHECK FAILED")
        return 1

    print("\nSECURITY CONFIGURATION CHECK PASSED")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Check ExceptionOps AI security configuration."
        )
    )

    parser.add_argument(
        "--require-production",
        action="store_true",
        help=(
            "Fail unless APP_ENV is production."
        ),
    )

    args = parser.parse_args()

    return run_security_checks(
        require_production=args.require_production,
    )


if __name__ == "__main__":
    sys.exit(main())
