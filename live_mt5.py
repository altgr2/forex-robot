"""
live_mt5.py — Botni MetaTrader 5 (MT5) ga ulab JONLI ishlatish.

============================  DIQQAT! XAVFSIZLIK  ============================
  * Bu fayl HAQIQIY buyurtma yuborishi mumkin. Avval FAQAT DEMO akkauntda ishlating!
  * DRY_RUN = True  bo'lganda bot HECH NARSA yubormaydi, faqat "nima qilardim"
    deb ko'rsatadi. Avval shu rejimda sinang.
  * Bot REAL akkaunt aniqlasa, ALLOW_REAL_ACCOUNT = False bo'lsa, savdoni RAD etadi.
  * Trading yuqori riskli. Yo'qotishga tayyor bo'lmagan pulni ishlatmang.
=============================================================================

OLDINDAN KERAK (faqat Windows):
  1. MetaTrader 5 dasturini o'rnating (broker saytidan yoki metatrader5.com).
  2. MT5 da BEPUL DEMO akkaunt oching (virtual pul) va unga kiring.
  3. MT5 dasturi OCHIQ tursin.
  4. Python kutubxonasini o'rnating:
         pip install MetaTrader5
  5. Ushbu faylni ishga tushiring:
         python live_mt5.py
"""

from __future__ import annotations

import datetime
import time

import strategy
from data import Bar

# =========================================================================
# CONFIG — sozlamalar (calibrate.py tavsiyasiga moslang)
# =========================================================================
SYMBOL = "EURUSD"         # MT5 dagi belgi (brokeringizda "EURUSD.m" bo'lishi mumkin)
TIMEFRAME = "D1"          # vaqt oralig'i: D1=kunlik, H1=soatlik, M15=15 daqiqa
BARS_TO_LOAD = 400        # nechta oxirgi sham yuklansin (indikatorlar uchun yetarli)

# Strategiya (main.py / calibrate.py bilan bir xil bo'lsin)
FAST, SLOW, TREND = 20, 50, 200
MIN_CONFIDENCE = 85       # 80% ishonch gate: faqat shundan oshganda savdo

# Risk (calibrate.py tavsiyasiga moslang)
STOP_LOSS = 0.03          # 3% stop-loss
TAKE_PROFIT = 0.015       # 1.5% take-profit
LOT = 0.01                # savdo hajmi (0.01 = micro lot, demo uchun kichik boshlang)

# Xavfsizlik
DRY_RUN = True            # True = BUYURTMA YUBORMAYDI, faqat ko'rsatadi (avval shunday sinang!)
ALLOW_REAL_ACCOUNT = False  # True qilmaguncha real akkauntda savdo qilmaydi
MAGIC = 20240601          # botning "imzosi" (o'z savdolarini ajratish uchun)

# Ishlash rejimi
RUN_FOREVER = False       # False = bir marta tekshiradi va to'xtaydi
CHECK_EVERY_MINUTES = 60  # RUN_FOREVER=True bo'lsa, har necha daqiqada tekshirsin
# =========================================================================


def _import_mt5():
    """MetaTrader5 kutubxonasini yuklaydi (faqat Windows'da mavjud)."""
    try:
        import MetaTrader5 as mt5
        return mt5
    except ImportError:
        print("XATO: 'MetaTrader5' kutubxonasi topilmadi.")
        print("O'rnating (Windows'da):  pip install MetaTrader5")
        raise SystemExit(1)


def get_bars(mt5, symbol: str, timeframe_str: str, count: int) -> list[Bar]:
    """MT5 dan oxirgi `count` ta shamni oladi va Bar ro'yxatiga aylantiradi."""
    tf = getattr(mt5, f"TIMEFRAME_{timeframe_str}", None)
    if tf is None:
        raise SystemExit(f"Noto'g'ri TIMEFRAME: {timeframe_str}")

    rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
    if rates is None or len(rates) == 0:
        raise SystemExit(
            f"'{symbol}' uchun narx olinmadi. Belgi nomini va MT5 ochiqligini tekshiring. "
            f"(xato: {mt5.last_error()})"
        )

    bars: list[Bar] = []
    for r in rates:
        dt = datetime.datetime.fromtimestamp(int(r["time"]))
        bars.append(Bar(
            date=dt.strftime("%Y-%m-%d %H:%M"),
            open=float(r["open"]),
            high=float(r["high"]),
            low=float(r["low"]),
            close=float(r["close"]),
        ))
    return bars


def has_open_position(mt5, symbol: str, magic: int) -> bool:
    """Bu bot ochgan savdo (shu belgida) hozir ochiqmi?"""
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return False
    return any(p.magic == magic for p in positions)


def place_order(mt5, symbol: str, direction: int) -> None:
    """Bozor narxida buyurtma yuboradi (stop-loss va take-profit bilan)."""
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"  Narx olinmadi: {symbol}")
        return

    info = mt5.symbol_info(symbol)
    digits = info.digits if info else 5

    if direction == 1:  # LONG (sotib olish)
        price = tick.ask
        sl = round(price * (1 - STOP_LOSS), digits)
        tp = round(price * (1 + TAKE_PROFIT), digits)
        order_type = mt5.ORDER_TYPE_BUY
        yon = "BUY (LONG)"
    else:               # SHORT (sotish)
        price = tick.bid
        sl = round(price * (1 + STOP_LOSS), digits)
        tp = round(price * (1 - TAKE_PROFIT), digits)
        order_type = mt5.ORDER_TYPE_SELL
        yon = "SELL (SHORT)"

    print(f"  Yo'nalish: {yon} | narx={price} | SL={sl} | TP={tp} | lot={LOT}")

    if DRY_RUN:
        print("  [DRY_RUN] Buyurtma YUBORILMADI (sinov rejimi). "
              "Haqiqiy savdo uchun DRY_RUN = False qiling.")
        return

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(LOT),
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": MAGIC,
        "comment": "kiro-forex-bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"  XATO: buyurtma bajarilmadi. Javob: {result}")
    else:
        print(f"  Buyurtma bajarildi! ticket={result.order}")


def run_once(mt5) -> None:
    """Bir marta tekshiradi: ishonch yetarli bo'lsa savdo qiladi, bo'lmasa kutadi."""
    bars = get_bars(mt5, SYMBOL, TIMEFRAME, BARS_TO_LOAD)

    # Oxirgi YOPILGAN sham bo'yicha qaror qilamiz (oxirgisi hali shakllanyapti)
    scored = strategy.score_setups(bars, FAST, SLOW, trend_filter=TREND)
    direction, score = scored[-2]

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yon = {1: "LONG", -1: "SHORT", 0: "yo'q"}[direction]
    print(f"[{now}] {SYMBOL} | setup: {yon} | ishonch bali: {score} "
          f"(kerak >= {MIN_CONFIDENCE})")

    if has_open_position(mt5, SYMBOL, MAGIC):
        print("  Ochiq savdo bor — yangi savdo ochilmaydi (kutamiz).")
        return

    if direction != 0 and score >= MIN_CONFIDENCE:
        print("  Ishonch YETARLI — savdo ochilmoqda.")
        place_order(mt5, SYMBOL, direction)
    else:
        print("  Ishonch past yoki setup yo'q — SAVDO QILMAYMIZ (kutamiz).")


def main():
    mt5 = _import_mt5()

    if not mt5.initialize():
        print(f"MT5 ga ulanib bo'lmadi. MT5 dasturi ochiqmi? (xato: {mt5.last_error()})")
        raise SystemExit(1)

    # Akkaunt turini tekshiramiz (demo / real)
    acct = mt5.account_info()
    if acct is None:
        print("Akkaunt ma'lumoti olinmadi. MT5 da akkauntga kirganmisiz?")
        mt5.shutdown()
        raise SystemExit(1)

    is_real = acct.trade_mode == mt5.ACCOUNT_TRADE_MODE_REAL
    tur = "REAL" if is_real else "DEMO/CONTEST"
    print(f"Ulandi: #{acct.login} | {acct.server} | tur: {tur} | "
          f"balans: {acct.balance} {acct.currency}")

    if is_real and not ALLOW_REAL_ACCOUNT:
        print("\nTO'XTASH: bu REAL akkaunt, lekin ALLOW_REAL_ACCOUNT = False.")
        print("Xavfsizlik uchun savdo qilinmaydi. Avval DEMO akkauntda sinang.")
        mt5.shutdown()
        raise SystemExit(0)

    # Belgini "Market Watch" ga qo'shamiz (aks holda narx kelmasligi mumkin)
    if not mt5.symbol_select(SYMBOL, True):
        print(f"Belgi tanlanmadi: {SYMBOL}. Broker'da nomi boshqacha bo'lishi mumkin "
              f"(masalan '{SYMBOL}.m').")

    if DRY_RUN:
        print(">>> DRY_RUN yoqilgan: buyurtma YUBORILMAYDI, faqat ko'rsatiladi.\n")

    try:
        if RUN_FOREVER:
            print(f"Doimiy rejim: har {CHECK_EVERY_MINUTES} daqiqada tekshiriladi. "
                  f"To'xtatish: Ctrl+C\n")
            while True:
                run_once(mt5)
                time.sleep(CHECK_EVERY_MINUTES * 60)
        else:
            run_once(mt5)
    except KeyboardInterrupt:
        print("\nTo'xtatildi (Ctrl+C).")
    finally:
        mt5.shutdown()
        print("MT5 aloqasi yopildi.")


if __name__ == "__main__":
    main()
