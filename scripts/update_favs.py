import os
import re
from pathlib import Path

import requests

MAX_REPOS = int(os.getenv("MAX_FAVORITE_REPOS", "9"))
USERNAME = os.getenv("GITHUB_USERNAME") or os.getenv("GITHUB_REPOSITORY_OWNER")
TOKEN = os.getenv("GITHUB_TOKEN")


def fetch_top_repos(username: str, max_repos: int) -> list[dict]:
    """
    Fetch top repositories for the given user sorted by stars (desc).
    """
    url = "https://api.github.com/search/repositories"
    query = f"user:{username} fork:false"

    headers = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max_repos,
    }

    resp = requests.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("items", [])


def build_projects_html(username: str, repos: list[dict]) -> str:
    """
    Build the HTML snippet for the favorite projects section.
    """
    anchors: list[str] = []
    for repo in repos:
        name = repo["name"]
        html_url = repo["html_url"]
        anchors.append(
            f'    <a href="{html_url}">'
            f'<img width="278" '
            f'src="https://denvercoder1-github-readme-stats.vercel.app/api/pin/'
            f'?username={username}&repo={name}&theme=nightowl&hide_border=true&show_icons=false" '
            f'alt="{name}"></a>'
        )

    anchors_block = "\n".join(anchors)

    snippet = f"""<details open>
  <summary><h2>📘 My Favorite Open Source Projects</h2></summary>
  <p align="left">
{anchors_block}
  </p>
</details>"""

    return snippet


def update_readme(readme_path: Path, new_block: str) -> bool:
    """
    Replace the section between FAVORITE_PROJECTS markers with new_block.
    Returns True if the file was changed.
    """
    content = readme_path.read_text(encoding="utf-8")

    pattern = re.compile(
        r"(<!-- FAVORITE_PROJECTS:START -->)(.*?)(<!-- FAVORITE_PROJECTS:END -->)",
        re.DOTALL,
    )

    replacement = r"\1\n" + new_block + r"\n\3"
    new_content, count = pattern.subn(replacement, content)

    if count == 0:
        raise RuntimeError(
            "Markers <!-- FAVORITE_PROJECTS:START --> and "
            "<!-- FAVORITE_PROJECTS:END --> not found in README.md"
        )

    if new_content != content:
        readme_path.write_text(new_content, encoding="utf-8")
        return True

    return False


def main() -> None:
    if not USERNAME:
        raise RuntimeError(
            "USERNAME not set (GITHUB_USERNAME or GITHUB_REPOSITORY_OWNER)."
        )

    repos = fetch_top_repos(USERNAME, MAX_REPOS)
    projects_html = build_projects_html(USERNAME, repos)

    readme_path = Path("README.md")
    changed = update_readme(readme_path, projects_html)

    if changed:
        print("README.md updated with new favorite projects.")
    else:
        print("README.md already up to date; no changes.")


if __name__ == "__main__":
    main()
