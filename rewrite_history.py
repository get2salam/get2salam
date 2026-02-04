"""Rewrite git history to remove 'qanoon' from commit messages."""
import subprocess, sys

# Get all commits
result = subprocess.run(["git", "log", "--format=%H %s", "--all", "--reverse"], 
                       capture_output=True, text=True)
commits = []
for line in result.stdout.strip().split("\n"):
    if line.strip():
        hash_val, msg = line.split(" ", 1)
        commits.append((hash_val, msg))

print(f"Total commits: {len(commits)}")

# Check which need fixing
needs_fix = [(h, m) for h, m in commits if "qanoon" in m.lower()]
print(f"Commits with 'qanoon': {len(needs_fix)}")
for h, m in needs_fix:
    fixed = m.replace("qanoon-api", "legal-api").replace("qanoon-rag", "rag-legal-search").replace("qanoon", "legal-platform")
    print(f"  {h[:7]}: '{m}' -> '{fixed}'")

if not needs_fix:
    print("Nothing to fix!")
    sys.exit(0)

# Use interactive rebase with GIT_SEQUENCE_EDITOR to reword
# Simpler: use git-filter-repo or manual approach
# Since it's only 7 commits, let's do a fresh orphan approach

print("\nRewriting with fresh history...")

# Get commit info in order
result = subprocess.run(["git", "log", "--format=%H|%aI|%aE|%aN|%s", "--reverse"], 
                       capture_output=True, text=True)

import os
os.environ["FILTER_BRANCH_SQUELCH_WARNING"] = "1"

# Write a Python msg-filter script
filter_script = '''
import sys
msg = sys.stdin.read()
msg = msg.replace("qanoon-api", "legal-api")
msg = msg.replace("qanoon-rag", "rag-legal-search") 
msg = msg.replace("qanoon", "legal-platform")
sys.stdout.write(msg)
'''

with open("_msg_filter.py", "w") as f:
    f.write(filter_script)

# Run filter-branch with python as msg-filter
result = subprocess.run(
    ["git", "filter-branch", "--msg-filter", "python _msg_filter.py", "--force", "--", "--all"],
    capture_output=True, text=True,
    env={**os.environ, "FILTER_BRANCH_SQUELCH_WARNING": "1"}
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)

# Verify
result = subprocess.run(["git", "log", "--oneline", "--all"], capture_output=True, text=True)
print("\nNew history:")
print(result.stdout)

# Check for remaining qanoon references
if "qanoon" in result.stdout.lower():
    print("WARNING: Still found 'qanoon' in history!")
else:
    print("✅ All 'qanoon' references removed from commit messages!")

# Clean up
os.remove("_msg_filter.py")
