import re

from conftest import SHARED

OVERLAYS = SHARED / "overlays"


def read(*parts):
    return (OVERLAYS.joinpath(*parts)).read_text(encoding="utf-8")


def test_audit_log_has_rls_and_no_update_delete():
    sql = read("audit-log-table", "files", "db", "audit_log.sql").lower()
    assert "create table" in sql and "audit_log" in sql
    assert "alter table audit_log enable row level security" in sql
    assert "for select" in sql
    # Final review fix (Important 5): only the server writes (service role); no browser insert policy,
    # and the admin check uses org_members from rls_template.sql, not a table no overlay creates.
    assert "for insert" not in sql
    assert "for update" not in sql and "for delete" not in sql
    assert "user_roles" not in sql and "org_members" in sql


def test_audit_log_columns():
    sql = read("audit-log-table", "files", "db", "audit_log.sql").lower()
    for column in ("id uuid primary key default gen_random_uuid()", "actor_id uuid", "action text not null",
                   "entity text not null", "entity_id text", "before jsonb", "after jsonb",
                   "created_at timestamptz not null default now()"):
        assert column in sql, column


def test_rls_template_uses_org_id():
    sql = read("rls-policies", "files", "db", "rls_template.sql").lower()
    assert "org_id uuid" in sql
    assert "auth.uid()" in sql
    for action in ("select", "insert", "update", "delete"):
        assert re.search(rf"for {action}\b", sql), action


def test_dockerfile_uses_port_env():
    dockerfile = read("cloud-run-fastapi", "files", "api", "Dockerfile")
    assert "${PORT" in dockerfile
    assert "uvicorn" in dockerfile


def test_health_route_declared():
    main_py = read("cloud-run-fastapi", "files", "api", "main.py")
    assert '@app.get("/health")' in main_py
    assert '{"status": "ok"}' in main_py


def test_requirements_minimum_versions_only():
    lines = [line.strip() for line in read("cloud-run-fastapi", "files", "api", "requirements.txt").splitlines()
             if line.strip()]
    assert any(line.startswith("fastapi>=") for line in lines)
    assert any(line.startswith("uvicorn[standard]>=") for line in lines)
    assert not any("==" in line for line in lines)
