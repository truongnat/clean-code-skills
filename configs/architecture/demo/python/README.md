# import-linter demo (Python) — verified, not decorative

`app/` is a small layered package: `domain` -> `application` -> `infrastructure` -> `interface`.
`app/domain/legacy_total.py` breaks both contracts on purpose, so you can watch the tool fail
before you point it at a real repo.

    cd configs/architecture/demo/python
    PYTHONPATH=.:stubs lint-imports --config .importlinter      # -> 2 contracts BROKEN
    rm app/domain/legacy_total.py
    PYTHONPATH=.:stubs lint-imports --config .importlinter      # -> all contracts KEPT
    git checkout app/domain/legacy_total.py

`stubs/sqlalchemy/` exists only so the checker can resolve a forbidden third-party import
without installing the ORM; delete it in your repo, where sqlalchemy is a real dependency.

Measured on import-linter 2.15 (Python 3.13): the broken run reports
`Module app.domain is not allowed to import app.infrastructure` and
`app.domain.legacy_total is not allowed to import sqlalchemy`.
