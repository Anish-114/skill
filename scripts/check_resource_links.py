#!/usr/bin/env python3
"""
Verification script for learning resource URLs in backend/app/data/learning_resources.json.
Checks HTTP accessibility of all URLs and reports broken or unreachable links.
Exits with 0 if all links are reachable (2xx/3xx), or 1 if any link fails.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import httpx

DATA_PATH = Path(__file__).resolve().parent.parent / "backend" / "app" / "data" / "learning_resources.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 SkillBridgeBot/1.0"


def check_url(client: httpx.Client, url: str) -> Tuple[int, str]:
    """
    Checks URL reachability using HEAD with GET fallback.
    Returns (status_code, error_message).
    """
    try:
        # Try HEAD request first for speed
        resp = client.head(url, follow_redirects=True, timeout=10.0)
        # If server disallows HEAD, fall back to GET with stream=True
        if resp.status_code == 405:
            resp = client.get(url, follow_redirects=True, timeout=10.0)
        return resp.status_code, ""
    except Exception as exc:
        try:
            # Retry once with GET
            resp = client.get(url, follow_redirects=True, timeout=10.0)
            return resp.status_code, ""
        except Exception as get_exc:
            return 0, str(get_exc)


def verify_all_links(json_file: Path) -> bool:
    if not json_file.exists():
        print(f"[ERROR] Resources file not found at: {json_file}")
        return False

    with open(json_file, "r", encoding="utf-8") as f:
        data: Dict[str, List[dict]] = json.load(f)

    total_links = 0
    passed_links = 0
    failed_links = []

    print("=" * 70)
    print(f"VERIFYING LEARNING RESOURCE LINKS ({json_file.name})")
    print("=" * 70)

    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(headers=headers, verify=True) as client:
        for skill, resources in data.items():
            if not resources:
                continue
            for res in resources:
                total_links += 1
                url = res.get("url", "")
                title = res.get("title", "Resource")
                if not url:
                    failed_links.append((skill, title, url, 0, "Empty URL string"))
                    continue

                code, err = check_url(client, url)
                if 200 <= code < 400:
                    passed_links += 1
                    print(f"  [PASS] {skill:22} | {code} | {title} -> {url}")
                else:
                    failed_links.append((skill, title, url, code, err))
                    print(f"  [FAIL] {skill:22} | {code or 'ERR'} | {title} -> {url} ({err})")

    print("=" * 70)
    print(f"SUMMARY: {passed_links}/{total_links} links passed.")

    if failed_links:
        print(f"\n[FAILED LINKS: {len(failed_links)}]")
        for skill, title, url, code, err in failed_links:
            print(f"  - [{skill}] {title}: {url} (Status: {code}, Error: {err})")
        print("=" * 70)
        return False

    print("ALL RESOURCE LINKS VERIFIED SUCCESSFULLY!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    file_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_PATH
    success = verify_all_links(file_arg)
    sys.exit(0 if success else 1)
