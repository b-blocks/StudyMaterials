#!/usr/bin/env python3
"""Post a single tweet to X using OAuth2 user context."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
TOKEN_CACHE_PATH = ROOT_DIR / ".state" / "x_oauth_token.json"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def env(name: str, required: bool = False, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    if required and not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def b64url_sha256(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def build_basic_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return f"Basic {base64.b64encode(raw).decode('utf-8')}"


def request_json(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: dict[str, str] | None = None,
    json_body: dict[str, str] | None = None,
) -> dict:
    request_data = None
    req_headers = headers.copy() if headers else {}
    if data is not None:
        request_data = urllib.parse.urlencode(data).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    if json_body is not None:
        request_data = json.dumps(json_body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url=url, data=request_data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: HTTP {exc.code} {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc


def save_token_cache(token: dict) -> None:
    TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE_PATH.write_text(json.dumps(token, ensure_ascii=False, indent=2), encoding="utf-8")


def load_token_cache() -> dict | None:
    if not TOKEN_CACHE_PATH.exists():
        return None
    try:
        return json.loads(TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def token_is_valid(token: dict) -> bool:
    expires_at = token.get("expires_at", 0)
    return bool(token.get("access_token")) and time.time() < (expires_at - 60)


def exchange_code_for_token(
    api_base: str,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    code_verifier: str,
) -> dict:
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }
    token = request_json(
        url=f"{api_base}/2/oauth2/token",
        method="POST",
        headers={
            "Authorization": build_basic_auth_header(client_id, client_secret),
        },
        data=payload,
    )
    token["expires_at"] = int(time.time()) + int(token.get("expires_in", 0))
    return token


def refresh_access_token(api_base: str, client_id: str, client_secret: str, refresh_token: str) -> dict:
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    token = request_json(
        url=f"{api_base}/2/oauth2/token",
        method="POST",
        headers={
            "Authorization": build_basic_auth_header(client_id, client_secret),
        },
        data=payload,
    )
    token["expires_at"] = int(time.time()) + int(token.get("expires_in", 0))
    return token


def run_auth_flow(
    api_base: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    scope: str,
) -> dict:
    state = secrets.token_urlsafe(24)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = b64url_sha256(code_verifier)

    query = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    auth_url = f"https://x.com/i/oauth2/authorize?{query}"
    print("\n1) 아래 URL을 브라우저에서 열어 앱 인증을 완료하세요.")
    print(auth_url)
    print("\n2) 리다이렉트된 최종 URL 전체를 붙여 넣으세요.")
    redirected = input("Redirect URL: ").strip()

    parsed = urllib.parse.urlparse(redirected)
    params = urllib.parse.parse_qs(parsed.query)
    if params.get("state", [None])[0] != state:
        raise RuntimeError("Invalid state value. 인증 요청이 일치하지 않습니다.")
    code = params.get("code", [None])[0]
    if not code:
        raise RuntimeError("Authorization code not found in redirect URL.")

    return exchange_code_for_token(
        api_base=api_base,
        client_id=client_id,
        client_secret=client_secret,
        code=code,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
    )


def post_tweet(
    api_base: str,
    access_token: str,
    text: str,
    reply_to_tweet_id: str | None = None,
) -> dict:
    body: dict[str, dict | str] = {"text": text}
    if reply_to_tweet_id:
        body["reply"] = {"in_reply_to_tweet_id": reply_to_tweet_id}

    return request_json(
        url=f"{api_base}/2/tweets",
        method="POST",
        headers={"Authorization": f"Bearer {access_token}"},
        json_body=body,
    )


def detect_char_limit(text: str) -> int:
    if re.search(r"[가-힣ㄱ-ㅎㅏ-ㅣ]", text):
        return 140
    return 280


def split_long_fragment(fragment: str, limit: int) -> list[str]:
    if len(fragment) <= limit:
        return [fragment]

    words = fragment.split()
    if len(words) <= 1:
        return [fragment[i : i + limit] for i in range(0, len(fragment), limit)]

    chunks: list[str] = []
    current = ""
    for word in words:
        if len(word) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend([word[i : i + limit] for i in range(0, len(word), limit)])
            continue
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= limit:
            current = candidate
        else:
            chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks


def split_text_for_thread(text: str, limit: int) -> list[str]:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return []
    if len(normalized) <= limit:
        return [normalized]

    sentence_like = [
        part.strip()
        for part in re.split(r"(?<=[.!?。！？])\s+", normalized)
        if part.strip()
    ]
    if not sentence_like:
        sentence_like = [normalized]

    chunks: list[str] = []
    current = ""
    for sentence in sentence_like:
        if len(sentence) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(split_long_fragment(sentence, limit))
            continue

        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= limit:
            current = candidate
        else:
            chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks


def post_thread(api_base: str, access_token: str, text: str) -> list[str]:
    limit = detect_char_limit(text)
    chunks = split_text_for_thread(text, limit)
    if not chunks:
        raise RuntimeError("Text is empty after normalization.")

    posted_ids: list[str] = []
    parent_id: str | None = None
    for idx, chunk in enumerate(chunks, start=1):
        result = post_tweet(
            api_base=api_base,
            access_token=access_token,
            text=chunk,
            reply_to_tweet_id=parent_id,
        )
        tweet_id = (result.get("data") or {}).get("id")
        if not tweet_id:
            raise RuntimeError(f"Tweet id missing for chunk {idx}: {result}")
        posted_ids.append(tweet_id)
        parent_id = tweet_id
        print(f"Posted {idx}/{len(chunks)} (limit={limit}, len={len(chunk)}): tweet_id={tweet_id}")

    return posted_ids


def main() -> int:
    parser = argparse.ArgumentParser(description="Post a single tweet to X")
    parser.add_argument("--text", help="Tweet text. Falls back to X_POST_TEXT in .env")
    parser.add_argument(
        "--api-base",
        default=None,
        help="X API base URL (default: X_API_BASE from .env or https://api.x.com)",
    )
    args = parser.parse_args()

    load_env_file(ENV_PATH)

    try:
        client_id = env("X_CLIENT_ID", required=True)
        client_secret = env("X_CLIENT_SECRET", required=True)
        redirect_uri = env("X_REDIRECT_URI", required=True)
        scope = env(
            "X_SCOPE",
            default="tweet.read tweet.write users.read offline.access",
        )
        api_base = args.api_base or env("X_API_BASE", default="https://api.x.com")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    text = args.text or env("X_POST_TEXT")
    if not text:
        print("Missing tweet text. Use --text or set X_POST_TEXT.", file=sys.stderr)
        return 2

    token = load_token_cache() or {}
    if token_is_valid(token):
        access_token = token["access_token"]
    else:
        refresh_token = token.get("refresh_token") or env("X_REFRESH_TOKEN")
        if refresh_token:
            token = refresh_access_token(
                api_base=api_base,
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token,
            )
            save_token_cache(token)
            access_token = token["access_token"]
        else:
            token = run_auth_flow(
                api_base=api_base,
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope or "",
            )
            save_token_cache(token)
            access_token = token["access_token"]

    tweet_ids = post_thread(api_base=api_base, access_token=access_token, text=text)
    if len(tweet_ids) == 1:
        print(f"Posted successfully. tweet_id={tweet_ids[0]}")
    else:
        print(
            "Thread posted successfully. "
            f"count={len(tweet_ids)}, root_tweet_id={tweet_ids[0]}, last_tweet_id={tweet_ids[-1]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
