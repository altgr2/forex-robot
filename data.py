"""
data.py — Bozor ma'lumotini olish (narxlar).

Bu fayl HECH QANDAY qo'shimcha kutubxona talab qilmaydi — faqat sof Python.

Ikki rejim bor:
  1) SINTETIK (soxta) ma'lumot — internet kerak emas, faqat sinab ko'rish uchun.
  2) REAL ma'lumot — Stooq.com'dan bepul yuklab oladi (internet kerak, API kalit shart emas).
"""

from __future__ import annotations

import csv
import datetime
import io
import random
import urllib.request
from dataclasses import dataclass


@dataclass
class Bar:
    """Bir kunlik narx: sana, ochilish, yuqori, past, yopilish."""
    date: str
    open: float
    high: float
    low: float
    close: float


def get_synthetic_data(days: int = 1500, seed: int = 42) -> list[Bar]:
    """
    EURUSD'ga o'xshash soxta narx ma'lumotini yaratadi (internetsiz ishlaydi).
    """
    rnd = random.Random(seed)
    start_price = 1.08          # EURUSD odatda ~1.08 atrofida
    price = start_price
    prev_close = start_price
    today = datetime.date.today()

    bars: list[Bar] = []
    for i in range(days):
        # Kunlik o'zgarish: kichik tasodifiy harakat + juda yengil trend
        ret = rnd.gauss(0.0002, 0.006)
        price = price * (1 + ret)

        open_ = prev_close
        close = price
        high = max(open_, close) * (1 + abs(rnd.gauss(0, 0.002)))
        low = min(open_, close) * (1 - abs(rnd.gauss(0, 0.002)))
        date = today - datetime.timedelta(days=days - i)

        bars.append(Bar(str(date), open_, high, low, close))
        prev_close = close

    return bars


def get_real_data(symbol: str = "eurusd", interval: str = "d") -> list[Bar]:
    """
    Stooq.com'dan REAL Forex ma'lumotini bepul yuklab oladi.
    Internet kerak, lekin ro'yxatdan o'tish yoki API kalit KERAK EMAS.

    symbol misollari (Forex):
        "eurusd" -> Yevro / Dollar
        "gbpusd" -> Funt / Dollar
        "usdjpy" -> Dollar / Yapon yenasi
    interval:
        "d" -> kunlik, "w" -> haftalik, "m" -> oylik
    """
    url = f"https://stooq.com/q/d/l/?s={symbol}&i={interval}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))
    bars: list[Bar] = []
    for row in reader:
        try:
            bars.append(Bar(
                date=row["Date"],
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
            ))
        except (ValueError, KeyError):
            continue  # bo'sh yoki buzuq qatorlarni o'tkazib yuboramiz

    if not bars:
        raise RuntimeError(
            f"'{symbol}' uchun ma'lumot yuklanmadi. "
            "Internetni yoki valyuta juftligi nomini tekshiring."
        )
    return bars
