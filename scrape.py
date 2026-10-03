#!/usr/bin/env python3
"""FunNow 高雄 住宿／休息 比價爬蟲。

抓 FunNow 公開頁面（不需登入），整理每個方案的 FunNow 價與店家官方定價（FunNow 頁面上的劃線價），
輸出 data.json 給 index.html 顯示。只用 Python 標準函式庫。
"""
import html as htmllib
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = "https://www.myfunnow.com"
REGION = 6                      # 台南｜高雄
CATEGORIES = {64: "住宿", 65: "休息"}
CITY = "高雄"                   # 只留地址在這個縣市的店家
MAX_PAGES = 15
DELAY = 1.0                     # 每次請求間隔（秒），不要調太小
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            print(f"  ! {url} 失敗 ({e})，第 {i + 1} 次", file=sys.stderr)
            time.sleep(3 * (i + 1))
    return None


def num(s):
    return int(s.replace(",", "")) if s else None


def clean(s):
    s = re.sub(r"<!--.*?-->", "", s or "", flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    return htmllib.unescape(s).strip()


def list_branch_ids():
    ids = {}
    for cat in CATEGORIES:
        seen = set()
        for page in range(1, MAX_PAGES + 1):
            h = get(f"{BASE}/zh-tw/regions/{REGION}/categories/{cat}?page={page}")
            time.sleep(DELAY)
            found = re.findall(r'href="/zh-tw/branches/(\d+)"', h or "")
            fresh = [i for i in found if i not in seen]
            if not fresh:
                break
            seen.update(fresh)
            for i in fresh:
                ids.setdefault(i, None)
        print(f"分類 {CATEGORIES[cat]}：{len(seen)} 家")
    return list(ids)


def parse_branch(bid, h):
    biz = None
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', h, re.S):
        try:
            j = json.loads(m.group(1))
        except ValueError:
            continue
        for o in j if isinstance(j, list) else [j]:
            if isinstance(o, dict) and o.get("@type") == "LocalBusiness":
                biz = o
    if not biz:
        return None
    addr = biz.get("address") or {}
    loc = addr.get("addressLocality") or ""
    rating = biz.get("aggregateRating") or {}
    products = []
    for m in re.finditer(r'<a href="/zh-tw/products/(\d+)".*?</a>', h, re.S):
        seg = m.group(0)
        name = re.search(r'<h3 class="product-name[^"]*"[^>]*>(.*?)</h3>', seg, re.S)
        price = re.search(r'data-testid="product-card-price"[^>]*>(?:\s|<!--.*?-->)*([\d,]+)', seg)
        srrp = re.search(r"<del[^>]*>(?:\s|<!--.*?-->)*([\d,]+)", seg)
        name = clean(name.group(1)) if name else ""
        hours = re.search(r"(\d+(?:\.\d+)?)\s*[hH]", name.split("｜")[0])
        products.append({
            "id": m.group(1),
            "name": name,
            "type": "休息" if hours else "住宿",
            "hours": float(hours.group(1)) if hours else None,
            "price": num(price.group(1)) if price else None,       # FunNow 價（None = 目前無法預訂）
            "official": num(srrp.group(1)) if srrp else None,     # 店家官方定價（FunNow 劃線價）
        })
    return {
        "id": bid,
        "name": biz.get("name") or "",
        "city": loc[:3],
        "district": loc[3:],
        "address": loc + (addr.get("streetAddress") or ""),
        "rating": rating.get("ratingValue"),
        "reviews": rating.get("reviewCount"),
        "url": f"{BASE}/zh-tw/branches/{bid}",
        "products": products,
    }


def main():
    ids = list_branch_ids()
    print(f"共 {len(ids)} 家店，開始抓方案…")
    branches, failed = [], 0
    for n, bid in enumerate(ids, 1):
        h = get(f"{BASE}/zh-tw/branches/{bid}")
        time.sleep(DELAY)
        b = parse_branch(bid, h) if h else None
        if not b:
            failed += 1
            continue
        if b["city"].startswith(CITY) and b["products"]:
            branches.append(b)
        if n % 20 == 0:
            print(f"  {n}/{len(ids)}")
    total = sum(len(b["products"]) for b in branches)
    print(f"{CITY}：{len(branches)} 家、{total} 個方案；失敗 {failed} 家")
    if not branches:
        # 抓不到就不要覆蓋舊資料，讓排程顯示失敗
        sys.exit("沒有抓到任何店家，保留原本的 data.json")
    tw = datetime.now(timezone(timedelta(hours=8)))
    out = {"updated": tw.strftime("%Y-%m-%d %H:%M"), "city": CITY, "branches": branches}
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
