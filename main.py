"""
main.py — Hammasini birlashtiruvchi asosiy fayl.

ISHGA TUSHIRISH (Windows'da):
    python main.py

Hech qanday qo'shimcha kutubxona o'rnatish KERAK EMAS.

ISH TARTIBI:
    1. Avval `python calibrate.py` ni ishga tushiring — u 80% win rate beradigan
       eng yaxshi sozlamani topadi (STOP_LOSS, TAKE_PROFIT, MIN_CONFIDENCE).
    2. O'sha 3 raqamni pastdagi CONFIG ga ko'chiring.
    3. `python main.py` ni ishga tushiring.
"""

import data
import strategy
import backtest

# =========================================================================
# CONFIG — sozlamalar
# =========================================================================
USE_REAL_DATA = False     # False = soxta ma'lumot (internetsiz sinash)
                          # True  = Stooq'dan real Forex ma'lumoti (internet kerak)
SYMBOL = "eurusd"         # real ma'lumot uchun valyuta juftligi (kichik harflar)
START_BALANCE = 10_000.0  # boshlang'ich (virtual) pul

# Strategiya sozlamalari
FAST_EMA = 20
SLOW_EMA = 50
TREND_FILTER = 200        # katta trend filtri (0 = o'chiq)

# >>> 80% ISHONCH GATE <<<
# Bot FAQAT ishonch bali shu qiymatdan oshgan setuplarda savdo qiladi.
# Aniq qiymatni `python calibrate.py` topadi. 0 = gate o'chiq (hamma signal).
MIN_CONFIDENCE = 85

# Talab qilinadigan minimal yutish foizi. Backtest shundan past chiqsa,
# bot "bu sozlama ishonchsiz" deb ogohlantiradi.
REQUIRED_WIN_RATE = 80.0

# Risk sozlamalari (calibrate.py tavsiyasiga ko'ra moslang)
RISK_PER_TRADE = 0.01     # har savdoda 1% risk
STOP_LOSS = 0.030         # 3% stop-loss
TAKE_PROFIT = 0.015       # 1.5% take-profit
# =========================================================================


def main():
    # 1) Ma'lumotni olamiz
    if USE_REAL_DATA:
        print(f"Real ma'lumot yuklanmoqda: {SYMBOL} ...")
        bars = data.get_real_data(SYMBOL)
    else:
        print("Soxta (sintetik) ma'lumot ishlatilmoqda (internetsiz sinash).")
        bars = data.get_synthetic_data()

    print(f"Jami {len(bars)} kunlik ma'lumot. "
          f"{bars[0].date} dan {bars[-1].date} gacha.")
    print(f"Ishonch gate: faqat ball >= {MIN_CONFIDENCE} bo'lgan setuplarda savdo.\n")

    # 2) Strategiya signallarini hisoblaymiz (ishonch gate bilan)
    signals = strategy.generate_signals(
        bars, fast=FAST_EMA, slow=SLOW_EMA,
        trend_filter=TREND_FILTER, min_confidence=MIN_CONFIDENCE,
    )

    # 3) Backtest (o'tmishda sinash)
    result = backtest.run_backtest(
        bars,
        signals,
        start_balance=START_BALANCE,
        risk_per_trade=RISK_PER_TRADE,
        stop_loss_pct=STOP_LOSS,
        take_profit_pct=TAKE_PROFIT,
    )

    # 4) Hech qanday savdo bo'lmasa — bu sizning qoidangiz ishlayotgani belgisi
    if result.num_trades == 0:
        print("HECH QANDAY SAVDO BO'LMADI.")
        print(f"Sababi: hech bir setup {MIN_CONFIDENCE} ishonch chegarasiga yetmadi.")
        print("Bu YOMON emas — bot 'ishonch past' deb savdodan tiyildi (pulni saqladi).")
        print("MIN_CONFIDENCE ni pasaytirib ko'ring yoki calibrate.py ni ishlating.")
        return

    # 5) Natijani chiroyli chiqaramiz
    print("=" * 52)
    print("            BACKTEST NATIJASI")
    print("=" * 52)
    print(f"Boshlang'ich pul   : ${result.start_balance:,.2f}")
    print(f"Yakuniy pul        : ${result.end_balance:,.2f}")
    print(f"Umumiy daromad     : {result.total_return_pct:+.2f}%")
    print(f"Savdolar soni      : {result.num_trades}")
    print(f"Yutuq foizi        : {result.win_rate:.1f}%")
    print(f"Expectancy         : ${result.expectancy:.2f}/savdo")
    print(f"Eng katta pasayish : {result.max_drawdown_pct:.2f}% (max drawdown)")
    print("=" * 52)

    # 6) Sizning 80% qoidangizni tekshiramiz
    if result.win_rate >= REQUIRED_WIN_RATE and result.expectancy > 0:
        print(f"YAXSHI: yutish foizi {REQUIRED_WIN_RATE:.0f}% dan yuqori VA "
              f"expectancy musbat. Bu sozlama sizning qoidangizga mos.")
    elif result.win_rate >= REQUIRED_WIN_RATE:
        print(f"DIQQAT: yutish foizi {REQUIRED_WIN_RATE:.0f}% dan yuqori, LEKIN "
              f"expectancy musbat emas — bu sozlama pul ishlamaydi! Tuzating.")
    else:
        print(f"DIQQAT: yutish foizi {REQUIRED_WIN_RATE:.0f}% dan PAST "
              f"({result.win_rate:.1f}%). calibrate.py bilan sozlamani toping.")

    print("\nESLATMA: o'tmish natijasi kelajakni KAFOLATLAMAYDI. "
          "Real puldan oldin demo akkauntda sinang.")


if __name__ == "__main__":
    main()
