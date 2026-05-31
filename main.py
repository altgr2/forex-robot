"""
main.py — Hammasini birlashtiruvchi asosiy fayl.

ISHGA TUSHIRISH (Windows'da):
    python main.py

Hech qanday qo'shimcha kutubxona o'rnatish KERAK EMAS.
Boshlang'ich uchun: hech narsani o'zgartirmasdan ishga tushiring va natijani ko'ring.
"""

import data
import strategy
import backtest

# =========================================================================
# CONFIG — sozlamalar (keyin shu raqamlarni o'zgartirib sinab ko'rishingiz mumkin)
# =========================================================================
USE_REAL_DATA = False     # False = soxta ma'lumot (internetsiz sinash)
                          # True  = Stooq'dan real Forex ma'lumoti (internet kerak)
SYMBOL = "eurusd"         # real ma'lumot uchun valyuta juftligi (kichik harflar)
START_BALANCE = 10_000.0  # boshlang'ich (virtual) pul

# Strategiya sozlamalari
FAST_EMA = 10
SLOW_EMA = 100
TREND_FILTER = 200        # katta trend filtri (0 = o'chiq). Sifatni oshiradi.

# Risk sozlamalari
# Quyidagi 1:1 nisbati YUQORI win rate beradi (~60%).
# Yuqori FOYDA (lekin past win rate) uchun: STOP_LOSS=0.015, TAKE_PROFIT=0.045
RISK_PER_TRADE = 0.01     # har savdoda 1% risk
STOP_LOSS = 0.02          # 2% stop-loss
TAKE_PROFIT = 0.02        # 2% take-profit (1:1 -> yuqori win rate)
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
          f"{bars[0].date} dan {bars[-1].date} gacha.\n")

    # 2) Strategiya signallarini hisoblaymiz
    signals = strategy.generate_signals(
        bars, fast=FAST_EMA, slow=SLOW_EMA, trend_filter=TREND_FILTER
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

    # 4) Natijani chiroyli chiqaramiz
    print("=" * 50)
    print("           BACKTEST NATIJASI")
    print("=" * 50)
    print(f"Boshlang'ich pul   : ${result.start_balance:,.2f}")
    print(f"Yakuniy pul        : ${result.end_balance:,.2f}")
    print(f"Umumiy daromad     : {result.total_return_pct:+.2f}%")
    print(f"Savdolar soni      : {result.num_trades}")
    print(f"Yutuq foizi        : {result.win_rate:.1f}%")
    print(f"Eng katta pasayish : {result.max_drawdown_pct:.2f}% (max drawdown)")
    print("=" * 50)

    if result.total_return_pct > 0:
        print("Natija: ijobiy (o'tmishda foyda bergan).")
    else:
        print("Natija: salbiy (o'tmishda zarar bergan). Sozlamalarni o'zgartirib ko'ring.")
    print("\nESLATMA: o'tmish natijasi kelajakni KAFOLATLAMAYDI. "
          "Bu faqat strategiyani tekshirish usuli.")


if __name__ == "__main__":
    main()
