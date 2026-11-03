#!/usr/bin/env python3
"""Shopify Dev Dashboard client-credentials helper (alleen stdlib).

Gebruik:
    python3 scripts/shopify_auth.py check            # winkel zonder voorvoegsel
    python3 scripts/shopify_auth.py check suelta     # SHOPIFY_SUELTA_*

Als module:
    from shopify_auth import graphql
    graphql("suelta", "{ shop { name } }")

Leest .env in de projectmap. Toont nooit het secret of het token.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "2026-10")
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
_cache: dict[str, tuple[str, float]] = {}

ERRORS = {
    "app_not_installed": "App staat niet op deze winkel: installeer de app (stap 3).",
    "application_cannot_be_found": "Client ID klopt niet of hoort bij een andere organisatie.",
    "invalid_client": "Client secret fout of vernieuwd: zet het opnieuw in .env.",
}


def load_env(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def config(store: str | None = None) -> tuple[str, str, str]:
    load_env()
    prefix = f"SHOPIFY_{store.upper()}_" if store else "SHOPIFY_"
    names = [prefix + n for n in ("SHOP", "CLIENT_ID", "CLIENT_SECRET")]
    values = [os.environ.get(n, "") for n in names]
    missing = [n for n, v in zip(names, values) if not v]
    if missing:
        sys.exit(f"Ontbreekt in .env: {', '.join(missing)}")
    shop = values[0].removeprefix("https://").rstrip("/")
    return shop, values[1], values[2]


def get_token(store: str | None = None) -> tuple[str, str, str]:
    """Return (shop, access_token, scopes). Token is 24 uur geldig; gecachet per run."""
    shop, client_id, secret = config(store)
    cached = _cache.get(shop)
    if cached and cached[1] > time.time() + 60:
        return shop, cached[0], ""
    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": secret,
    }).encode()
    req = urllib.request.Request(
        f"https://{shop}/admin/oauth/access_token", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        hint = next((v for k, v in ERRORS.items() if k in text), "")
        sys.exit(f"Token ophalen mislukt ({e.code}) voor {shop}: {text[:300]}\n{hint}")
    token = data["access_token"]
    _cache[shop] = (token, time.time() + int(data.get("expires_in", 86399)))
    return shop, token, data.get("scope", "")


def graphql(store: str | None, query: str, variables: dict | None = None) -> dict:
    shop, token, _ = get_token(store)
    req = urllib.request.Request(
        f"https://{shop}/admin/api/{API_VERSION}/graphql.json",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"GraphQL-fout ({e.code}): {e.read().decode(errors='replace')[:500]}")
    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"], indent=2))
    return result["data"]


def check(store: str | None = None) -> None:
    shop, _, scopes = get_token(store)
    print(f"token ok ({shop})")
    data = graphql(store, "{ shop { name myshopifyDomain } productsCount { count } }")
    print(f"winkel:    {data['shop']['name']} ({data['shop']['myshopifyDomain']})")
    print(f"producten: {data['productsCount']['count']}")
    if scopes:
        print(f"scopes:    {len(scopes.split(','))} ({scopes})")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] != "check":
        sys.exit(__doc__)
    check(args[1] if len(args) > 1 else None)
