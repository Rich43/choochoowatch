import os
from typing import Tuple

import requests
from bs4 import BeautifulSoup

from log_utils import log


def create_rentry_spoofed(content: str = "\ud83d\uded6 ChooChoo Log", secret_file: str = "rentry_secret.txt") -> Tuple[str, str]:
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://rentry.co/",
    }
    resp = session.get("https://rentry.co", headers=headers)
    log(f"Fetched Rentry homepage: {resp.status_code}")
    soup = BeautifulSoup(resp.text, "html.parser")
    token_tag = soup.find("input", {"name": "csrf-token"})
    csrf = token_tag["value"].strip() if token_tag and token_tag.has_attr("value") else ""
    if not csrf:
        raise Exception("Failed to retrieve CSRF token from Rentry")

    data = {
        "csrf-token": csrf,
        "edit_code": "",
        "text": content,
        "lang": "plain_text",
    }
    post_headers = headers.copy()
    post_headers["Content-Type"] = "application/x-www-form-urlencoded"
    post = session.post("https://rentry.co", data=data, headers=post_headers, allow_redirects=False)
    if post.status_code == 302 and "Location" in post.headers:
        slug = post.headers["Location"].lstrip("/")
        edit_resp = session.get(f"https://rentry.co/{slug}/edit", headers=headers)
        soup = BeautifulSoup(edit_resp.text, "html.parser")
        edit_code = soup.find("input", {"name": "edit_code"})["value"]
        with open(secret_file, "w", encoding="utf-8") as f:
            f.write(f"{slug}\n{edit_code}")
        return slug, edit_code
    raise Exception(f"Failed to create paste: {post.status_code}")


def read_rentry_credentials(secret_file: str = "rentry_secret.txt") -> Tuple[str, str]:
    if os.path.exists(secret_file):
        with open(secret_file, "r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
            if len(lines) == 2:
                return lines[0], lines[1]
    return create_rentry_spoofed(secret_file=secret_file)


def update_rentry_log(log_path: str = "choochoowatch.log", secret_file: str = "rentry_secret.txt") -> None:
    try:
        slug, edit_code = read_rentry_credentials(secret_file)
        with open(log_path, "r", encoding="utf-8") as f:
            last_lines = f.readlines()[-10:]
        content = "### \ud83d\uded6 ChooChoo Watch Log\n\n```\n" + "".join(last_lines).strip() + "\n```"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Referer": f"https://rentry.co/{slug}",
        }
        data = {
            "edit_code": edit_code,
            "content": content,
        }
        resp = requests.post(f"https://rentry.co/api/edit/{slug}", data=data, headers=headers)
        if resp.status_code == 200:
            log(f"\ud83d\udd01 Rentry updated: https://rentry.co/{slug}")
        else:
            log(f"\u274c Failed to update Rentry: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        log(f"Rentry update error: {e}")
