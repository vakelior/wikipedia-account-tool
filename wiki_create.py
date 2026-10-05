#!/usr/bin/env python3
"""
Wikipedia account creator via Playwright (Chromium real browser).

Same approach as the cloud-browser method: a real headless Chromium with a
clean fingerprint + full JavaScript is used to submit Special:CreateAccount,
letting the invisible hCaptcha resolve itself. When a visual hCaptcha appears,
we abort with a clear message (visual solving is not reliable headless).

Usage:
    python wiki_create.py --username JamesFletcher94 --password 'Fletcher2026!Secure'
    python wiki_create.py --batch batches/sample.json
    python wiki_create.py --username X --password Y --email foo@example.com
"""

import argparse
import json
import sys
import time

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

CREATE_URL = "https://auth.wikimedia.org/enwiki/wiki/Special:CreateAccount"
CHECK_URL = "https://en.wikipedia.org/w/api.php?action=query&meta=userinfo&format=json"


def create_account(page, username, password, email="", retype=None, timeout_ms=60000):
    retype = retype or password

    print(f"[*] Opening {CREATE_URL} ...")
    page.goto(CREATE_URL, wait_until="domcontentloaded", timeout=60000)
    time.sleep(2)

    page.fill("input#wpName, input[name='wpName'], #wpName1", username)
    page.fill("input#wpPassword, input[name='wpPassword'], input[name='password']", password)
    page.fill("input#wpRetype, input[name='wpRetype'], input[name='retype']", retype)

    if email:
        try:
            page.fill("input#wpEmail, input[name='wpEmail'], input[name='email']", email)
        except PWTimeout:
            pass

    print("[*] Submitting CreateAccount ...")
    page.click("button[type='submit'], #wpCreateaccount, input[type='submit']")
    page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    time.sleep(3)

    body = page.inner_text("body")

    ok = ("has been created" in body) or (f"Welcome, {username}" in body) or ("Welcome," in body and username in body)
    if ok:
        print(f"[+] SUCCESS: account '{username}' created.")
        return {"username": username, "password": password, "email": email, "status": "created"}

    if "captcha" in body.lower() or "hcaptcha" in body.lower():
        err = "visual hCaptcha appeared — cannot solve headless. Try again (IP may be flagged)."
        print(f"[!] FAIL (captcha): {username} -> {err}")
        return {"username": username, "status": "captcha_required"}

    if "created 6 accounts" in body or "maximum allowed" in body.lower():
        err = "IP account-creation limit hit (6 accounts / 24h per IP)."
        print(f"[!] FAIL (ip-limit): {username} -> {err}")
        return {"username": username, "status": "ip_limit"}

    if "blocked" in body.lower() and ("open proxy" in body.lower() or "webhost" in body.lower()):
        err = "IP blocked by Wikimedia (open proxy / webhost)."
        print(f"[!] FAIL (blocked): {username} -> {err}")
        return {"username": username, "status": "blocked"}

    snippet = body[:400].replace("\n", " ")
    print(f"[?] UNKNOWN result for {username}: {snippet}")
    return {"username": username, "status": "unknown", "detail": snippet}


def _new_context(browser):
    return browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="Europe/London",
    )


def run_batch(path):
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    accounts = cfg.get("accounts", [])
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = _new_context(browser)
        page = ctx.new_page()
        for a in accounts:
            r = create_account(page, a["username"], a["password"], a.get("email", ""))
            results.append(r)
            time.sleep(3)
            try:
                page.goto("https://auth.wikimedia.org/enwiki/wiki/Special:UserLogout",
                          wait_until="domcontentloaded", timeout=20000)
                time.sleep(1)
            except Exception:
                pass
        browser.close()
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--username")
    ap.add_argument("--password")
    ap.add_argument("--email", default="")
    ap.add_argument("--batch")
    ap.add_argument("--out", default="results.json")
    args = ap.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        if args.batch:
            results = run_batch(args.batch)
        elif args.username and args.password:
            ctx = _new_context(browser)
            page = ctx.new_page()
            results = [create_account(page, args.username, args.password, args.email)]
        else:
            ap.error("Provide --username/--password OR --batch")
        browser.close()

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    ok = sum(1 for r in results if r["status"] == "created")
    print(f"\n=== DONE: {ok}/{len(results)} created ===")
    sys.exit(0 if ok == len(results) else 2)


if __name__ == "__main__":
    main()
