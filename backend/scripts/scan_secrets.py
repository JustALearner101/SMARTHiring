import os
import re
import subprocess
from pathlib import Path

# Base directories
REPO_ROOT = Path(__file__).resolve().parents[2]

# Regex patterns for common secrets and credentials
SECRET_PATTERNS = [
    ("OpenAI API Key", re.compile(r"sk-[a-zA-Z0-9_-]{24,}")),
    ("Anthropic API Key", re.compile(r"sk-ant-[a-zA-Z0-9_-]{24,}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z-_]{35}")),
    ("Groq API Key", re.compile(r"gsk_[a-zA-Z0-9]{20,}")),
    ("Generic Private Key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("GitHub Token", re.compile(r"(?:ghp|gho|ghu|ghs|ghr|github_pat)_[a-zA-Z0-9_]{36,}")),
    ("Slack Token", re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}")),
    ("JWT Token", re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}")),
    ("Supabase Key", re.compile(r"sbp_[a-zA-Z0-9]{20,}")),
    ("AWS Access Key", re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}")),
    (
        "Hardcoded Database Password",
        re.compile(r"(?:postgres|postgresql|mysql|mongodb|redis)://[a-zA-Z0-9_\-\.]+:(?!(?:postgres|password|pass|\[YOUR-PASSWORD\]|<password>|123456|\$))[^\s@/]+@[a-zA-Z0-9_\-\.]+"),
    ),
    (
        "High Entropy API Secret",
        re.compile(r"""(?:api[_-]?key|secret[_-]?key|auth[_-]?token|password|passwd|smtp_pass(?:word)?)\s*[:=]\s*['"]([a-zA-Z0-9_\-\.]{20,})['"]""", re.IGNORECASE),
    ),
]

IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf",
    ".woff", ".woff2", ".ttf", ".eot", ".lock", ".idx", ".darc"
}

IGNORE_FILES = {
    "uv.lock", "pnpm-lock.yaml", "package-lock.json", ".ruff_cache",
    ".pytest_cache", ".git"
}

FALSE_POSITIVE_HINTS = [
    "change-this", "[YOUR-", "YOUR_API_KEY", "sk-ant-api03-xxx", "sk-...",
    "dummy", "mock", "example", "placeholder", "test-secret", "fake",
    "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "postgresql://postgres:[YOUR-PASSWORD]",
    "notifications@smarthiring.ai",
    "http://localhost",
    "sha256", "checksum", "integrity",
    "test_jwt_secret", "secret-key",
]

def scan_file(file_path: Path, rel_path: str):
    findings = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            line_str = line.strip()
            if not line_str or line_str.startswith("#") and "example" in line_str.lower():
                continue
            
            # Check false positives
            if any(hint in line_str for hint in FALSE_POSITIVE_HINTS):
                continue
            
            for pat_name, pattern in SECRET_PATTERNS:
                matches = pattern.findall(line_str)
                for m in matches:
                    val = m if isinstance(m, str) else m[0]
                    # Filter out short or obviously benign values
                    if len(val) < 12:
                        continue
                    if any(h in val.lower() for h in ["example", "placeholder", "test", "your-", "secret"]):
                        continue
                    
                    masked = val[:4] + "..." + val[-4:] if len(val) > 8 else "***"
                    findings.append({
                        "file": rel_path,
                        "line": idx,
                        "type": pat_name,
                        "preview": masked,
                        "sample": line_str[:120],
                    })
    except Exception:
        pass
    return findings

def scan_git_history():
    print("\nScanning Git commit history (diffs across recent commits)...")
    try:
        log_diff = subprocess.check_output(
            ["git", "log", "-p", "--no-textconv", "-n", "100"],
            cwd=REPO_ROOT
        ).decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Failed to read git log: {e}")
        return []

    findings = []
    lines = log_diff.splitlines()
    current_commit = "unknown"
    current_file = "unknown"

    for idx, line in enumerate(lines):
        if line.startswith("commit "):
            current_commit = line.split()[1][:8]
        elif line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            line_str = line[1:].strip()
            if any(hint in line_str for hint in FALSE_POSITIVE_HINTS):
                continue
            for pat_name, pattern in SECRET_PATTERNS:
                matches = pattern.findall(line_str)
                for m in matches:
                    val = m if isinstance(m, str) else m[0]
                    if len(val) < 12:
                        continue
                    if any(h in val.lower() for h in ["example", "placeholder", "test", "your-", "secret"]):
                        continue
                    masked = val[:4] + "..." + val[-4:] if len(val) > 8 else "***"
                    findings.append({
                        "commit": current_commit,
                        "file": current_file,
                        "line": idx,
                        "type": pat_name,
                        "preview": masked,
                        "sample": line_str[:120],
                    })
    return findings

def main():
    print(f"Scanning repository at: {REPO_ROOT}")
    
    # Get all tracked git files
    try:
        git_output = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT).decode("utf-8")
        all_files = [f.strip() for f in git_output.splitlines() if f.strip()]
    except Exception as e:
        print(f"Failed to list git files: {e}")
        all_files = []

    # Also include any unstaged / untracked files not in .gitignore
    extra_output = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT).decode("utf-8")
    for line in extra_output.splitlines():
        if len(line) > 3:
            f = line[3:].strip()
            if f not in all_files and os.path.exists(REPO_ROOT / f):
                all_files.append(f)

    all_findings = []
    scanned_count = 0

    for rel in all_files:
        p = REPO_ROOT / rel
        if not p.is_file():
            continue
        if p.suffix.lower() in IGNORE_EXTENSIONS:
            continue
        if any(ign in rel for ign in IGNORE_FILES):
            continue
        
        scanned_count += 1
        res = scan_file(p, rel)
        if res:
            all_findings.extend(res)

    print(f"\nScanned {scanned_count} files in working tree.")
    print(f"Found {len(all_findings)} potential secret(s) in working tree.")
    for f in all_findings:
        print(f"[{f['type']}] {f['file']}:{f['line']}")
        print(f"  Match: {f['preview']}")
        print(f"  Line:  {f['sample']}\n")

    history_findings = scan_git_history()
    print(f"\nFound {len(history_findings)} potential secret(s) in Git history.")
    for h in history_findings:
        print(f"[{h['type']}] commit {h['commit']} in {h['file']}")
        print(f"  Match: {h['preview']}")
        print(f"  Line:  {h['sample']}\n")

if __name__ == "__main__":
    main()
