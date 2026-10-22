import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from html.parser import HTMLParser

URL = "https://moneyfarm.jp/projects"
STATE_FILE = Path("known_tickets.json")
BASE = "https://moneyfarm.jp"

class TicketLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = dict(attrs)
            href = attrs.get("href", "")
            if href and re.match(r"^/projects/[^/?#]+/?$", href):
                self._href = href
                self._parts = []

    def handle_data(self, data):
        if self._href is not None:
            s = data.strip()
            if s:
                self._parts.append(s)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            title = " ".join(self._parts).strip()
            self.links.append((self._href.rstrip("/"), title))
            self._href = None
            self._parts = []

def fetch_tickets():
    req = Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; MoneyFarmNewTicketMonitor/1.0)"})
    with urlopen(req, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")
    parser = TicketLinkParser()
    parser.feed(html)
    # Deduplicate links while preserving order; ignore any non-ticket path.
    result = {}
    for path, title in parser.links:
        if path == "/projects":
            continue
        ticket_id = path.rsplit("/", 1)[-1]
        result[ticket_id] = {
            "title": title or ticket_id,
            "url": urljoin(BASE, path),
        }
    if not result:
        raise RuntimeError(
            "チケットのリンクを取得できませんでした。サイト構造変更またはJavaScript描画の可能性があります。"
        )
    return result

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID が設定されていません。")
    import urllib.parse
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": "true",
    }).encode()
    req = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(req, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")

def main():
    current = fetch_tickets()
    if STATE_FILE.exists():
        try:
            previous = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"保存済み状態ファイルを読めません: {exc}")
        if not previous:
            # Empty starter file means this is the initial baseline.
            print("Initial baseline saved; no notification sent.")
        else:
            new_ids = [tid for tid in current if tid not in previous]
            if new_ids:
                lines = ["🆕 Money Farmに新しいファームチケットが掲載された可能性があります。", ""]
                for tid in new_ids:
                    item = current[tid]
                    lines.append(f"・{item['title']}")
                    lines.append(item["url"])
                    lines.append("")
                lines.append("一覧ページ: https://moneyfarm.jp/projects")
                send_telegram("\\n".join(lines).strip())
                print(f"New ticket(s): {', '.join(new_ids)}")
            else:
                print("No new tickets.")
    STATE_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
