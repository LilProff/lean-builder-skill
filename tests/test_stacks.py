import jsonschema
import pytest

from conftest import load_json

TYPES = ("website", "saas", "internal", "agent")
CONTEXTS = ("personal", "client", "startup")
BASE_OVERLAYS = {"claude-md-lean", "status-md", "env-example", "gitignore-secrets"}


@pytest.fixture
def stacks(shared_dir):
    return load_json(shared_dir / "stacks.json")


@pytest.fixture
def tiers(shared_dir):
    return load_json(shared_dir / "free-tiers.json")


def matching(stacks, build_type, context, commercial):
    return [
        r for r in stacks["rows"]
        if r["type"] == build_type and r["context"] == context and r["commercial"] in ("any", commercial)
    ]


def test_schema_valid(stacks, shared_dir):
    jsonschema.validate(stacks, load_json(shared_dir / "stacks.schema.json"))


def test_every_combination_has_exactly_one_row(stacks):
    for t in TYPES:
        for c in CONTEXTS:
            for commercial in (True, False):
                assert len(matching(stacks, t, c, commercial)) == 1, (t, c, commercial)


def test_all_providers_exist(stacks, tiers):
    for r in stacks["rows"]:
        for provider in r["stack"].values():
            assert provider in tiers, (r["id"], provider)
        for options in r["fallbacks"].values():
            for provider in options:
                assert provider in tiers, (r["id"], provider)


def test_fallback_roles_exist_in_stack(stacks):
    for r in stacks["rows"]:
        assert set(r["fallbacks"]) <= set(r["stack"]), r["id"]


def test_client_rows_owned_by_client(stacks):
    for r in stacks["rows"]:
        assert r["accounts_owner"] == ("client" if r["context"] == "client" else "builder"), r["id"]


def test_every_role_has_a_why(stacks):
    for r in stacks["rows"]:
        assert set(r["why"]) == set(r["stack"]), r["id"]


def test_base_overlays_on_every_row(stacks):
    for r in stacks["rows"]:
        assert BASE_OVERLAYS <= set(r["overlays"]), r["id"]


def test_no_business_row_on_github_pages(stacks, tiers):
    for r in stacks["rows"]:
        if r["context"] != "personal":
            hosts = [r["stack"].get("host")] + r["fallbacks"].get("host", [])
            assert "github-pages" not in hosts, r["id"]
