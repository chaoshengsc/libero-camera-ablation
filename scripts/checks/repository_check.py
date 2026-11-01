"""Check existing public links, JavaScript syntax and citation versions offline.

Run from any directory: python scripts/checks/repository_check.py
Requires Git and Node.js, imports no policy/simulator and writes no files.
Only Git-tracked public documentation and JavaScript are inspected.
"""

import argparse
import html
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r'!?\[([^\]\n]*)\]\((<[^>\n]+>|[^\s)]+)(?:\s+"[^"\n]*")?\)')
DESTINATION = re.compile(r'\((<[^>\n]+>|[^\s)]+)(?:\s+"[^"\n]*")?\)')


def markdown_links(text):
    """Visit inner images and outer links separately, including README badges."""
    brackets, escaped = [], False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "[":
            brackets.append(index)
        elif char == "]" and brackets:
            brackets.pop()
            match = DESTINATION.match(text, index + 1)
            if match:
                yield match[1].strip("<>")


def tracked_files(root):
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True)
    return {root / name for name in result.stdout.decode().split("\0") if name}


def without_fences(text):
    lines, fence = [], None
    for line in text.splitlines():
        match = re.match(r" {0,3}(`{3,}|~{3,})", line)
        if match:
            marker = match[1]
            if fence is None:
                fence = marker[0], len(marker)
            elif marker[0] == fence[0] and len(marker) >= fence[1] and not line[match.end():].strip():
                fence = None
        elif fence is None and not line.startswith("    "):
            lines.append(line)
    return "\n".join(lines)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.anchors, self.links = set(), []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if not value:
                continue
            if key == "id" or (key == "name" and tag == "a"):
                self.anchors.add(value)
            elif key in {"href", "src", "poster"}:
                self.links.append(value)
            elif key == "srcset" and not value.startswith("data:"):
                self.links.extend(part.strip().split()[0] for part in value.split(",") if part.strip())


def document(path):
    text = path.read_text()
    markdown = path.suffix.lower() == ".md"
    if markdown:
        text = without_fences(text)
    page = Page(text)
    if markdown:
        counts = {}
        for heading in re.findall(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", text, flags=re.M):
            heading = LINK.sub(lambda m: m[1], re.sub(r"<[^>]+>", "", heading))
            slug = "".join(c for c in html.unescape(heading).lower() if c.isalnum() or c in " _-").replace(" ", "-")
            number = counts.get(slug, 0)
            counts[slug] = number + 1
            page.anchors.add(slug + (f"-{number}" if number else ""))
        # Code examples are not published links.
        link_text = re.sub(r"(`+).*?\1", "", text)
        page.links.extend(markdown_links(link_text))
    return page


def check_links(root, files):
    errors, count, pages = [], 0, {}

    def load(path):
        if path not in pages:
            pages[path] = document(path)
        return pages[path]

    for source in sorted(p for p in files if p.suffix.lower() in {".md", ".html"}):
        if source.is_symlink():
            errors.append(f"{source.relative_to(root)}: documentation symlink is not supported")
            continue
        for url in load(source).links:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc:
                continue
            count += 1
            target = (source.parent / unquote(parsed.path)).resolve() if parsed.path else source
            label = f"{source.relative_to(root)}: {url}"
            if not target.is_relative_to(root):
                errors.append(f"{label}: target escapes the repository")
                continue
            prefix = str(target) + "/"
            directory = any(str(p).startswith(prefix) for p in files)
            if target not in files and not directory:
                errors.append(f"{label}: target is not a tracked public file/directory")
                continue
            if parsed.fragment:
                if directory:
                    target = next((target / name for name in ("index.html", "README.md") if target / name in files), target)
                if target.suffix.lower() in {".md", ".html"} and unquote(parsed.fragment) not in load(target).anchors:
                    errors.append(f"{label}: missing fragment")
    return errors, count


def check_versions(root):
    patterns = {"pyproject.toml": r'(?m)^version\s*=\s*"([^"\n]+)"',
                "CITATION.cff": r'(?m)^version:\s*"([^"\n]+)"',
                "README.md": r"version\s*=\s*\{([^}\n]+)\}",
                "README_CN.md": r"version\s*=\s*\{([^}\n]+)\}"}
    values, errors = {}, []
    for name, pattern in patterns.items():
        match = re.search(pattern, (root / name).read_text())
        if match:
            values[name] = match[1]
        else:
            errors.append(f"{name}: version field missing")
    if len(set(values.values())) > 1:
        errors.append(f"Citation/project version mismatch: {values}")
    return errors


def check_javascript(files):
    node = shutil.which("node")
    if node is None:
        return ["Node.js is required for the existing JavaScript syntax check"], 0
    errors, count = [], 0
    for path in sorted(p for p in files if p.suffix == ".js"):
        result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True, timeout=30, check=False)
        count += 1
        if result.returncode:
            errors.append(f"{path.name}: JavaScript syntax check failed\n{result.stderr.strip()}")
    return errors, count


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root; defaults to this checkout")
    root = parser.parse_args(argv).root.resolve()
    try:
        files = tracked_files(root)
        links, link_count = check_links(root, files)
        javascript, js_count = check_javascript(files)
        errors = links + javascript + check_versions(root)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        errors = [str(error)]
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Checked {link_count} public links/fragments, {js_count} JavaScript files and four version fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())
