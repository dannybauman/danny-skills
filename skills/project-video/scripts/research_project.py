#!/usr/bin/env python3
"""
Research a GitHub repository and output structured JSON for the video generator.

Usage:
    python research_project.py --repo https://github.com/user/repo
    python research_project.py --repo /path/to/local/repo --url https://app.example.com
    python research_project.py --repo user/repo --since "last week"
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
from pathlib import Path


# Known dependencies to detect for tech stack
TECH_STACK_MAP = {
    "package.json": {
        "react": "React",
        "next": "Next.js",
        "vue": "Vue",
        "nuxt": "Nuxt",
        "svelte": "Svelte",
        "angular": "Angular",
        "express": "Express",
        "fastify": "Fastify",
        "koa": "Koa",
        "hono": "Hono",
        "tailwindcss": "Tailwind CSS",
        "prisma": "Prisma",
        "drizzle-orm": "Drizzle",
        "mongoose": "Mongoose",
        "socket.io": "Socket.IO",
        "three": "Three.js",
        "electron": "Electron",
        "vite": "Vite",
        "webpack": "Webpack",
        "typescript": "TypeScript",
    },
    "pyproject.toml": {
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "starlette": "Starlette",
        "sqlalchemy": "SQLAlchemy",
        "pydantic": "Pydantic",
        "celery": "Celery",
        "pandas": "pandas",
        "numpy": "NumPy",
        "pytorch": "PyTorch",
        "torch": "PyTorch",
        "tensorflow": "TensorFlow",
        "scikit-learn": "scikit-learn",
        "httpx": "httpx",
        "click": "Click",
        "typer": "Typer",
        "rich": "Rich",
    },
    "requirements.txt": {
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "sqlalchemy": "SQLAlchemy",
        "celery": "Celery",
        "pandas": "pandas",
        "numpy": "NumPy",
        "torch": "PyTorch",
        "tensorflow": "TensorFlow",
        "scikit-learn": "scikit-learn",
    },
    "Cargo.toml": {
        "actix-web": "Actix Web",
        "axum": "Axum",
        "rocket": "Rocket",
        "tokio": "Tokio",
        "serde": "Serde",
        "diesel": "Diesel",
        "sqlx": "SQLx",
        "warp": "Warp",
        "clap": "Clap",
        "tauri": "Tauri",
    },
    "Gemfile": {
        "rails": "Ruby on Rails",
        "sinatra": "Sinatra",
        "sidekiq": "Sidekiq",
        "devise": "Devise",
        "pundit": "Pundit",
        "grape": "Grape",
        "hanami": "Hanami",
    },
    "go.mod": {
        "gin-gonic/gin": "Gin",
        "gofiber/fiber": "Fiber",
        "gorilla/mux": "Gorilla Mux",
        "labstack/echo": "Echo",
        "go-chi/chi": "Chi",
        "gorm.io/gorm": "GORM",
        "ent/ent": "Ent",
    },
}


def run_gh(args, capture_json=True):
    """Run a gh CLI command and return parsed output. Returns None on failure."""
    cmd = ["gh"] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None
        output = result.stdout.strip()
        if not output:
            return None
        if capture_json:
            return json.loads(output)
        return output
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def parse_repo_identifier(repo_arg):
    """Parse repo argument into (owner, name, is_local) tuple.

    Accepts:
        https://github.com/user/repo
        https://github.com/user/repo.git
        github.com/user/repo
        user/repo
        /path/to/local/repo
    """
    # Local path
    if os.path.isdir(repo_arg):
        return None, None, True

    # Strip URL components
    cleaned = repo_arg.rstrip("/")
    cleaned = re.sub(r"\.git$", "", cleaned)
    cleaned = re.sub(r"^https?://", "", cleaned)
    cleaned = re.sub(r"^github\.com/", "", cleaned)

    parts = cleaned.split("/")
    if len(parts) >= 2:
        return parts[0], parts[1], False
    return None, None, False


def get_local_repo_info(path):
    """Gather info from a local repository path."""
    repo_path = Path(path).resolve()
    info = {}

    info["name"] = repo_path.name
    info["full_name"] = repo_path.name
    info["url"] = str(repo_path)

    # Try to get remote URL for full_name
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            remote = result.stdout.strip()
            match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", remote)
            if match:
                info["full_name"] = match.group(1)
                info["url"] = f"https://github.com/{info['full_name']}"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Description from .github or package.json
    info["description"] = None
    pkg_json = repo_path / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
                info["description"] = pkg.get("description")
        except (json.JSONDecodeError, IOError):
            pass

    # Languages by file extension
    info["languages"] = _count_local_languages(repo_path)
    if info["languages"]:
        info["primary_language"] = max(info["languages"], key=info["languages"].get)
    else:
        info["primary_language"] = None

    # Tree summary and file count
    info["tree_summary"], info["total_files"] = _build_local_tree_summary(repo_path)

    # README
    info["readme_summary"] = None
    info["features"] = []
    info["install_command"] = None
    readme_path = _find_readme(repo_path)
    if readme_path:
        try:
            readme_text = readme_path.read_text(errors="replace")
            info["readme_summary"] = _extract_readme_summary(readme_text)
            info["features"] = _extract_features(readme_text)
            info["install_command"] = _extract_install_command(readme_text)
        except IOError:
            pass

    # Tech stack
    info["tech_stack"] = _detect_tech_stack_local(repo_path)

    # Recent commits from git log
    info["recent_commits"] = _get_local_commits(repo_path)

    # Fields we can't get locally
    info["homepage"] = None
    info["topics"] = []
    info["stars"] = None
    info["forks"] = None
    info["contributors"] = None
    info["recent_prs"] = []
    info["created_at"] = None
    info["license"] = _detect_local_license(repo_path)

    return info


def _count_local_languages(repo_path):
    """Count lines by file extension to approximate language breakdown."""
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".tsx": "TypeScript", ".jsx": "JavaScript", ".rb": "Ruby",
        ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
        ".swift": "Swift", ".c": "C", ".cpp": "C++", ".h": "C",
        ".cs": "C#", ".php": "PHP", ".sh": "Shell", ".bash": "Shell",
        ".css": "CSS", ".scss": "CSS", ".html": "HTML", ".vue": "Vue",
        ".svelte": "Svelte", ".zig": "Zig", ".ex": "Elixir",
        ".exs": "Elixir", ".lua": "Lua", ".r": "R", ".R": "R",
    }
    counts = {}
    try:
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden dirs and common non-source dirs
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".") and d not in (
                    "node_modules", "vendor", "venv", ".venv", "__pycache__",
                    "dist", "build", "target", ".git",
                )
            ]
            for f in files:
                ext = Path(f).suffix.lower()
                lang = ext_map.get(ext)
                if lang:
                    counts[lang] = counts.get(lang, 0) + 1
    except OSError:
        return {}

    total = sum(counts.values())
    if total == 0:
        return {}
    return {lang: round(count / total * 100, 1) for lang, count in
            sorted(counts.items(), key=lambda x: -x[1])}


def _build_local_tree_summary(repo_path):
    """Build a summary of top-level directories and file counts."""
    parts = []
    total = 0
    try:
        entries = sorted(repo_path.iterdir())
    except OSError:
        return "", 0

    for entry in entries:
        if entry.name.startswith("."):
            continue
        if entry.name in ("node_modules", "vendor", "venv", ".venv", "__pycache__"):
            continue
        if entry.is_file():
            total += 1
        elif entry.is_dir():
            count = sum(1 for _ in entry.rglob("*") if _.is_file()
                        and not any(p.startswith(".") for p in _.relative_to(repo_path).parts))
            total += count
            if count > 0:
                parts.append(f"{entry.name}/ ({count} files)")

    return ", ".join(parts), total


def _find_readme(repo_path):
    """Find README file with case-insensitive matching."""
    for name in ("README.md", "readme.md", "Readme.md", "README.rst",
                 "README.txt", "README"):
        p = repo_path / name
        if p.exists():
            return p
    return None


def _extract_readme_summary(text):
    """Extract first 2-3 sentences from README, skipping badges and headings."""
    lines = text.split("\n")
    content_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip empty, headings, badges, HTML tags, images
        if not stripped:
            if content_lines:
                break  # Stop at first blank line after content
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("[!") or stripped.startswith("[!["):
            continue
        if stripped.startswith("<") and not stripped.startswith("<a"):
            continue
        if stripped.startswith("!["):
            continue
        if re.match(r"^[=>|]", stripped):
            continue
        content_lines.append(stripped)
        if len(content_lines) >= 3:
            break

    if not content_lines:
        return None

    text = " ".join(content_lines)
    # Extract up to 3 sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(sentences[:3])
    if len(summary) > 500:
        summary = summary[:497] + "..."
    return summary


def _extract_features(text):
    """Extract feature list items from README."""
    features = []
    in_features_section = False

    for line in text.split("\n"):
        stripped = line.strip()

        # Detect feature-like headings
        if re.match(r"^#{1,3}\s+.*(feature|what it does|highlights|key|overview|capabilities)", stripped, re.I):
            in_features_section = True
            continue

        # Another heading ends the section
        if in_features_section and re.match(r"^#{1,3}\s+", stripped):
            break

        if in_features_section and re.match(r"^[-*]\s+", stripped):
            item = re.sub(r"^[-*]\s+", "", stripped)
            # Strip markdown bold/links but keep text
            item = re.sub(r"\*\*(.+?)\*\*", r"\1", item)
            item = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", item)
            if item and len(item) > 3:
                features.append(item)

    return features[:10]


def _extract_install_command(text):
    """Extract install command from README."""
    patterns = [
        r"(?:pip|pip3)\s+install\s+\S+",
        r"npm\s+install\s+(?:-[gD]\s+)?\S+",
        r"npx\s+\S+",
        r"yarn\s+add\s+\S+",
        r"pnpm\s+(?:add|install)\s+\S+",
        r"brew\s+install\s+\S+",
        r"cargo\s+install\s+\S+",
        r"gem\s+install\s+\S+",
        r"go\s+install\s+\S+",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def _detect_tech_stack_local(repo_path):
    """Detect tech stack from local manifest files."""
    stack = set()
    for manifest, deps_map in TECH_STACK_MAP.items():
        filepath = repo_path / manifest
        if not filepath.exists():
            continue
        try:
            content = filepath.read_text(errors="replace").lower()
            for dep_key, dep_name in deps_map.items():
                if dep_key.lower() in content:
                    stack.add(dep_name)
        except IOError:
            continue
    return sorted(stack)


def _get_local_commits(repo_path, limit=10):
    """Get recent commits from local git repo."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "log",
             f"-{limit}", "--format=%H|%s|%aI"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return []
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append({
                    "sha": parts[0][:7],
                    "message": parts[1],
                    "date": parts[2][:10],
                })
        return commits
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _detect_local_license(repo_path):
    """Detect license from local LICENSE file."""
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE"):
        p = repo_path / name
        if p.exists():
            try:
                text = p.read_text(errors="replace")[:500].lower()
                if "mit license" in text or "permission is hereby granted" in text:
                    return "MIT"
                if "apache license" in text:
                    return "Apache-2.0"
                if "gnu general public license" in text:
                    if "version 3" in text:
                        return "GPL-3.0"
                    return "GPL-2.0"
                if "bsd" in text:
                    return "BSD"
                if "mozilla public" in text:
                    return "MPL-2.0"
                if "isc license" in text:
                    return "ISC"
                return "Other"
            except IOError:
                pass
    return None


def get_remote_repo_info(owner, repo_name, repo_arg):
    """Gather info from a remote GitHub repository."""
    nwo = f"{owner}/{repo_name}"
    info = {}

    # Core repo metadata
    fields = (
        "name,description,url,homepageUrl,repositoryTopics,"
        "stargazerCount,forkCount,licenseInfo,createdAt,"
        "primaryLanguage,languages"
    )
    meta = run_gh(["repo", "view", repo_arg, "--json", fields])
    if meta is None:
        print(f"Error: Could not fetch repo '{repo_arg}'. Check that it exists "
              "and `gh` is authenticated.", file=sys.stderr)
        sys.exit(1)

    info["name"] = meta.get("name", repo_name)
    info["full_name"] = nwo
    info["description"] = meta.get("description")
    info["url"] = meta.get("url", f"https://github.com/{nwo}")
    info["homepage"] = meta.get("homepageUrl") or None

    topics_raw = meta.get("repositoryTopics") or []
    if isinstance(topics_raw, list):
        info["topics"] = [
            t.get("name", t) if isinstance(t, dict) else t
            for t in topics_raw
        ]
    else:
        info["topics"] = []

    info["stars"] = meta.get("stargazerCount")
    info["forks"] = meta.get("forkCount")

    license_info = meta.get("licenseInfo")
    if isinstance(license_info, dict):
        info["license"] = license_info.get("spdxId") or license_info.get("name")
    else:
        info["license"] = None

    info["created_at"] = (meta.get("createdAt") or "")[:10] or None

    primary_lang = meta.get("primaryLanguage")
    if isinstance(primary_lang, dict):
        info["primary_language"] = primary_lang.get("name")
    else:
        info["primary_language"] = None

    # Languages as percentages
    langs_raw = meta.get("languages") or []
    if isinstance(langs_raw, list):
        total = sum(
            (l.get("size", 0) if isinstance(l, dict) else 0) for l in langs_raw
        )
        if total > 0:
            info["languages"] = {
                l["name"]: round(l["size"] / total * 100, 1)
                for l in langs_raw if isinstance(l, dict) and "name" in l
            }
        else:
            info["languages"] = {}
    else:
        info["languages"] = {}

    return info, nwo


def get_contributors(nwo):
    """Get contributor count for a repo."""
    data = run_gh(["api", f"repos/{nwo}/contributors?per_page=100"])
    if isinstance(data, list):
        return len(data)
    return None


def get_recent_prs(repo_arg, since=None):
    """Get recent merged PRs."""
    data = run_gh([
        "pr", "list", "--repo", repo_arg, "--state", "merged",
        "--limit", "10", "--json", "title,number,mergedAt",
    ])
    if not isinstance(data, list):
        return []
    prs = []
    for pr in data:
        merged_at = pr.get("mergedAt", "")
        prs.append({
            "title": pr.get("title", ""),
            "number": pr.get("number"),
            "merged_at": merged_at[:10] if merged_at else None,
        })
    # Note: --since filtering for PRs is best-effort; gh pr list doesn't
    # support --since directly, so we return the most recent 10.
    return prs


def get_recent_commits(nwo, since=None):
    """Get recent commits from the GitHub API."""
    endpoint = f"repos/{nwo}/commits?per_page=10"
    if since:
        endpoint += f"&since={since}"
    data = run_gh(["api", endpoint])
    if not isinstance(data, list):
        return []
    commits = []
    for c in data:
        commit_info = c.get("commit", {})
        sha = c.get("sha", "")
        date_str = commit_info.get("author", {}).get("date", "")
        commits.append({
            "message": commit_info.get("message", "").split("\n")[0],
            "sha": sha[:7],
            "date": date_str[:10] if date_str else None,
        })
    return commits


def get_readme(nwo):
    """Fetch and decode README content from GitHub API."""
    content = run_gh(
        ["api", f"repos/{nwo}/readme", "--jq", ".content"],
        capture_json=False,
    )
    if not content:
        return None
    try:
        # GitHub returns base64-encoded content; the --jq extracts just the
        # content field as a raw string. It may contain newlines from the
        # base64 encoding.
        decoded = base64.b64decode(content.replace("\n", "")).decode("utf-8", errors="replace")
        return decoded
    except Exception:
        return None


def get_remote_tree_summary(nwo):
    """Get tree summary from GitHub API."""
    data = run_gh(["api", f"repos/{nwo}/git/trees/HEAD"])
    if not isinstance(data, dict):
        return "", 0

    tree = data.get("tree", [])
    dirs = []
    file_count = 0

    for item in tree:
        path = item.get("path", "")
        item_type = item.get("type", "")
        if path.startswith("."):
            continue
        if item_type == "blob":
            file_count += 1
        elif item_type == "tree":
            # Get subtree file count
            subtree_sha = item.get("sha")
            if subtree_sha:
                subtree = run_gh(["api", f"repos/{nwo}/git/trees/{subtree_sha}?recursive=1"])
                if isinstance(subtree, dict):
                    sub_files = sum(
                        1 for t in subtree.get("tree", [])
                        if t.get("type") == "blob"
                    )
                    file_count += sub_files
                    if sub_files > 0:
                        dirs.append(f"{path}/ ({sub_files} files)")

    summary = ", ".join(dirs)
    return summary, file_count


def get_remote_manifests(nwo):
    """Fetch manifest files from GitHub to detect tech stack."""
    stack = set()
    manifests_to_check = [
        ("package.json", "package.json"),
        ("pyproject.toml", "pyproject.toml"),
        ("requirements.txt", "requirements.txt"),
        ("Cargo.toml", "Cargo.toml"),
        ("Gemfile", "Gemfile"),
        ("go.mod", "go.mod"),
    ]
    for manifest_name, lookup_key in manifests_to_check:
        content = run_gh(
            ["api", f"repos/{nwo}/contents/{manifest_name}", "--jq", ".content"],
            capture_json=False,
        )
        if not content:
            continue
        try:
            decoded = base64.b64decode(content.replace("\n", "")).decode("utf-8", errors="replace").lower()
        except Exception:
            continue
        deps_map = TECH_STACK_MAP.get(lookup_key, {})
        for dep_key, dep_name in deps_map.items():
            if dep_key.lower() in decoded:
                stack.add(dep_name)
    return sorted(stack)


def _parse_since_to_iso(since_str):
    """Best-effort parse of human time spec to ISO date for GitHub API.

    Handles formats like "7 days ago", "last week", "2 weeks ago", "last month".
    Returns ISO date string or None.
    """
    if not since_str:
        return None

    import datetime

    now = datetime.datetime.now(datetime.timezone.utc)

    # "YYYY-MM-DD" already
    if re.match(r"^\d{4}-\d{2}-\d{2}", since_str):
        return since_str

    since_lower = since_str.lower().strip()

    if since_lower in ("last week", "1 week ago", "a week ago"):
        delta = datetime.timedelta(weeks=1)
    elif since_lower in ("last month", "1 month ago", "a month ago"):
        delta = datetime.timedelta(days=30)
    else:
        match = re.match(r"(\d+)\s*(day|week|month)s?\s*ago", since_lower)
        if match:
            n = int(match.group(1))
            unit = match.group(2)
            if unit == "day":
                delta = datetime.timedelta(days=n)
            elif unit == "week":
                delta = datetime.timedelta(weeks=n)
            elif unit == "month":
                delta = datetime.timedelta(days=n * 30)
            else:
                return None
        else:
            return None

    return (now - delta).strftime("%Y-%m-%dT%H:%M:%SZ")


def research_project(repo, url=None, since=None):
    """Research a GitHub project and return a structured dict.

    Args:
        repo: GitHub URL (https://github.com/user/repo), shorthand (user/repo),
              or local filesystem path.
        url: Optional deployed app URL to override homepage.
        since: Optional timespec for filtering recent activity (e.g. "last week").

    Returns:
        dict with project metadata, tech stack, README summary, and recent activity.
    """
    owner, repo_name, is_local = parse_repo_identifier(repo)

    if is_local:
        info = get_local_repo_info(repo)
        if url:
            info["homepage"] = url
        return info

    if not owner or not repo_name:
        print(f"Error: Could not parse repo identifier '{repo}'. "
              "Use format: user/repo or https://github.com/user/repo",
              file=sys.stderr)
        sys.exit(1)

    # Core metadata from gh repo view
    info, nwo = get_remote_repo_info(owner, repo_name, repo)

    # Override homepage with --url if provided
    if url:
        info["homepage"] = url

    # Contributor count
    info["contributors"] = get_contributors(nwo)

    # Tech stack from manifests
    info["tech_stack"] = get_remote_manifests(nwo)

    # Tree summary
    info["tree_summary"], info["total_files"] = get_remote_tree_summary(nwo)

    # README parsing
    readme_text = get_readme(nwo)
    if readme_text:
        info["readme_summary"] = _extract_readme_summary(readme_text)
        info["features"] = _extract_features(readme_text)
        info["install_command"] = _extract_install_command(readme_text)
    else:
        info["readme_summary"] = None
        info["features"] = []
        info["install_command"] = None

    # Recent PRs
    info["recent_prs"] = get_recent_prs(repo, since=since)

    # Recent commits
    since_iso = _parse_since_to_iso(since)
    info["recent_commits"] = get_recent_commits(nwo, since=since_iso)

    return info


def main():
    parser = argparse.ArgumentParser(
        description="Research a GitHub repository and output structured JSON."
    )
    parser.add_argument(
        "--repo", required=True,
        help="GitHub URL (https://github.com/user/repo), shorthand (user/repo), "
             "or local path",
    )
    parser.add_argument(
        "--url", default=None,
        help="Deployed app URL (overrides repo homepage)",
    )
    parser.add_argument(
        "--since", default=None,
        help="Time spec for recent activity, e.g. 'last week', '7 days ago'",
    )
    args = parser.parse_args()

    result = research_project(args.repo, url=args.url, since=args.since)
    json.dump(result, sys.stdout, indent=2, default=str)
    print()  # trailing newline


if __name__ == "__main__":
    main()
