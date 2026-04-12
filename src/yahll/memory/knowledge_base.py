"""
Knowledge base bridge — reads skills from A Taste of Knowlegement dynamically.
No hardcoded topics. Adding a skill there makes it available to Yahll automatically.
"""
import os
import glob

KNOWLEDGE_BASE_PATH = r"C:\Users\Drugos-Laptop\Desktop\A Taste of Knowlegement\skills"


def _skills_dir() -> str:
    return KNOWLEDGE_BASE_PATH


def list_skills() -> list[dict]:
    """Return all available skills: [{name, file, first_line}]"""
    skills_dir = _skills_dir()
    if not os.path.isdir(skills_dir):
        return []

    results = []
    for path in sorted(glob.glob(os.path.join(skills_dir, "*.md"))):
        name = os.path.splitext(os.path.basename(path))[0]
        first_line = ""
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#"):
                        first_line = line.lstrip("#").strip()
                        break
        except OSError:
            pass
        results.append({"name": name, "file": path, "title": first_line or name})
    return results


def get_skills_index() -> str:
    """
    One-line-per-skill index injected into Yahll's system prompt at startup.
    Lightweight — just names, not full content.
    """
    skills = list_skills()
    if not skills:
        return ""
    lines = ["## KNOWLEDGE BASE (A Taste of Knowlegement)", "Available skills — use load_skill(name) to read full content:", ""]
    for s in skills:
        lines.append(f"- {s['name']}: {s['title']}")
    lines.append("")
    lines.append(f"Source: {_skills_dir()}")
    return "\n".join(lines)


def load_skill(name: str) -> dict:
    """
    Load a full skill file by name (with or without .md).
    Fuzzy match — 'ml' matches 'ml-from-scratch'.
    Returns {name, content} or {error}.
    """
    skills_dir = _skills_dir()
    if not os.path.isdir(skills_dir):
        return {"error": f"Knowledge base not found at {skills_dir}"}

    # Exact match first
    exact = os.path.join(skills_dir, name if name.endswith(".md") else name + ".md")
    if os.path.isfile(exact):
        with open(exact, encoding="utf-8") as f:
            return {"name": name, "content": f.read()}

    # Fuzzy match — find files where name is a substring
    name_lower = name.lower()
    matches = []
    for path in glob.glob(os.path.join(skills_dir, "*.md")):
        fname = os.path.splitext(os.path.basename(path))[0]
        if name_lower in fname.lower():
            matches.append((fname, path))

    if len(matches) == 1:
        fname, path = matches[0]
        with open(path, encoding="utf-8") as f:
            return {"name": fname, "content": f.read()}
    elif len(matches) > 1:
        return {"error": f"Ambiguous: {[m[0] for m in matches]}. Be more specific."}
    else:
        available = [os.path.splitext(os.path.basename(p))[0]
                     for p in glob.glob(os.path.join(skills_dir, "*.md"))]
        return {"error": f"Skill '{name}' not found.", "available": available}
