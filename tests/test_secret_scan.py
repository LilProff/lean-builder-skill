from secret_scan import Hit, main, scan

FAKE_PAYSTACK = "sk_live_" + "x" * 24


def test_finds_key_in_source(tmp_path):
    f = tmp_path / "app.ts"
    f.write_text("line1\nline2\nconst k = '" + FAKE_PAYSTACK + "'\n", encoding="utf-8")
    assert scan(tmp_path) == [Hit(f, 3, "paystack")]


def test_flags_env_file_but_not_example(tmp_path):
    (tmp_path / ".env").write_text("A=1\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("A=\n", encoding="utf-8")
    hits = scan(tmp_path)
    assert [(h.path.name, h.kind) for h in hits] == [(".env", "env-file")]


def test_flags_env_variants(tmp_path):
    (tmp_path / ".env.local").write_text("A=1\n", encoding="utf-8")
    assert [h.kind for h in scan(tmp_path)] == ["env-file"]


def test_skips_node_modules(tmp_path):
    d = tmp_path / "node_modules" / "pkg"
    d.mkdir(parents=True)
    (d / "x.js").write_text(FAKE_PAYSTACK, encoding="utf-8")
    assert scan(tmp_path) == []


def test_skips_large_and_binary(tmp_path):
    (tmp_path / "big.txt").write_text(FAKE_PAYSTACK + "\n" + "a" * (3 * 1024 * 1024), encoding="utf-8")
    (tmp_path / "img.bin").write_bytes(b"\x00\x01" + FAKE_PAYSTACK.encode())
    assert scan(tmp_path) == []


def test_clean_project_has_no_hits(tmp_path):
    (tmp_path / "a.py").write_text("PAYSTACK_SECRET_KEY = os.environ['PAYSTACK_SECRET_KEY']\n", encoding="utf-8")
    assert scan(tmp_path) == []


def test_output_hides_secret(tmp_path, capsys):
    (tmp_path / "a.ts").write_text(FAKE_PAYSTACK, encoding="utf-8")
    assert main([str(tmp_path)]) == 1
    out = capsys.readouterr()
    assert FAKE_PAYSTACK not in out.out + out.err
    assert "paystack" in out.out


def test_main_clean_returns_0(tmp_path):
    assert main([str(tmp_path)]) == 0


# Final review fix (Important 2): env files gitignored in a real repo are fine.
def _git_repo(tmp_path, ignore):
    import subprocess
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text(ignore, encoding="utf-8")


def test_ignored_env_file_in_git_repo_not_flagged(tmp_path):
    _git_repo(tmp_path, ".env.local\n")
    (tmp_path / ".env.local").write_text("A=1\n", encoding="utf-8")
    assert scan(tmp_path) == []


def test_unignored_env_file_in_git_repo_flagged(tmp_path):
    _git_repo(tmp_path, "node_modules/\n")
    (tmp_path / ".env").write_text("A=1\n", encoding="utf-8")
    assert [h.kind for h in scan(tmp_path)] == ["env-file"]
