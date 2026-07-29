#!/usr/bin/env python3
"""Manual pre-commit online check for the AFNA disaster-notice gateway; not CI."""
from urllib.parse import urlparse
from urllib.request import Request, urlopen

URL = "https://www.afna.gov.tw/list.php?theme=natural_disaster&subtheme="
def main():
    try:
        with urlopen(Request(URL, headers={"User-Agent":"policy-agri-loan-handbook-audit"}), timeout=30) as response:
            final = response.url; body = response.read().decode("utf-8", "replace")
            host = urlparse(final).hostname or ""
            if response.status != 200 or host not in {"afna.gov.tw", "www.afna.gov.tw"} or "天然災害低利貸款" not in body or "login" in final.lower(): raise RuntimeError("unexpected official gateway response")
    except Exception as exc:
        print(f"DISASTER OFFICIAL GATEWAY ONLINE AUDIT FAILED: {exc}"); return 1
    print(f"DISASTER OFFICIAL GATEWAY ONLINE AUDIT PASSED: {final}")
if __name__ == "__main__": raise SystemExit(main() or 0)
