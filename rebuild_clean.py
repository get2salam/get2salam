"""Rebuild git history with clean commit messages."""
import subprocess, os

def git(*args, env=None):
    r = subprocess.run(["git"] + list(args), capture_output=True, text=True, env=env)
    return r.stdout.strip(), r.returncode

# Get commits — use separate format tokens to avoid pipe issues
fmt = "%H%n%aI%n%aN%n%aE%n%s%n---END---"
out, rc = git("log", f"--format={fmt}", "--reverse")
print(f"git log returned {len(out)} chars, rc={rc}")

blocks = out.split("---END---")
commits = []
for block in blocks:
    lines = [l for l in block.strip().split("\n") if l.strip()]
    if len(lines) >= 5:
        commits.append({
            "hash": lines[0], "date": lines[1],
            "name": lines[2], "email": lines[3], "msg": lines[4]
        })

print(f"Found {len(commits)} commits")

replacements = [
    ("qanoon-api", "legal-api"),
    ("qanoon-rag", "rag-legal-search"),
    ("qanoon", "legal-platform"),
]

for c in commits:
    fixed = c["msg"]
    for old, new in replacements:
        fixed = fixed.replace(old, new)
    c["new_msg"] = fixed
    if c["msg"] != fixed:
        print(f"  FIX: '{c['msg']}' -> '{fixed}'")

if not any(c["msg"] != c["new_msg"] for c in commits):
    print("Nothing to fix!")
    exit(0)

# Create orphan branch
print("\nRebuilding on clean-main...")
git("checkout", "--orphan", "clean-main")
git("rm", "-rf", ".", "--quiet")

for i, c in enumerate(commits):
    # Get the tree from that commit
    git("checkout", c["hash"], "--", ".")
    git("add", "-A")
    
    env = {**os.environ,
        "GIT_AUTHOR_DATE": c["date"], "GIT_COMMITTER_DATE": c["date"],
        "GIT_AUTHOR_NAME": c["name"], "GIT_AUTHOR_EMAIL": c["email"],
        "GIT_COMMITTER_NAME": c["name"], "GIT_COMMITTER_EMAIL": c["email"],
    }
    
    _, rc = git("commit", "-m", c["new_msg"], "--allow-empty", env=env)
    status = "OK" if rc == 0 else "FAIL"
    print(f"  [{i+1}/{len(commits)}] {c['new_msg']} [{status}]")

# Replace main with clean-main
print("\nSwapping branches...")
git("branch", "-D", "main")
git("branch", "-m", "clean-main", "main")

# Verify
out, _ = git("log", "--oneline")
print(f"\nNew history:\n{out}")
print("\n" + ("✅ ALL CLEAN!" if "qanoon" not in out.lower() else "❌ STILL DIRTY!"))

# Cleanup old refs
git("reflog", "expire", "--expire=now", "--all")
git("gc", "--prune=now", "--aggressive")
