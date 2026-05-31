"""
tune.py — Optimizator: ko'p sozlamalarni avtomatik sinab, eng yaxshisini topadi.

ISHGA TUSHIRISH:
    python tune.py

Bu fayl turli EMA, stop-loss, take-profit va trend-filtr sozlamalarini sinab,
natijalarni JADVAL ko'rinishida ko'rsatadi. Shunday qilib biz "qaysi sozlama
win rate'ni va foydani oshiradi?" degan savolga javob topamiz.

DIQQAT — "overfitting" xavfi:
  Agar biz o'tmishga JUDA mos sozlamani tanlasak, u kelajakda ishlamasligi mumkin.
  Shuning uchun: oddiy, mantiqiy sozlamalarni afzal ko'ring, juda "mukammal"
  natijaga ishonmang. Eng yaxshi yo'l — ma'lumotni ikkiga bo'lib sinash
  (split test), bu pastda ko'rsatilgan.
"""

import data
import strategy
import backtest

# Sinab ko'riladigan sozlamalar (kombinatsiyalar)
FAST_OPTIONS = [10, 20]
SLOW_OPTIONS = [50, 100]
TREND_OPTIONS = [0, 200]          # 0 = filtr o'chiq, 200 = katta trend filtri
SL_TP_OPTIONS = [                 # (stop_loss, take_profit)
    (0.01, 0.02),                 # 1:2
    (0.01, 0.015),                # 1:1.5 (win rate yuqoriroq, foyda kichikroq)
    (0.015, 0.045),               # 1:3 (win rate pastroq, foyda kattaroq)
    (0.02, 0.02),                 # 1:1
]


def evaluate(bars, fast, slow, trend, sl, tp):
    signals = strategy.generate_signals(bars, fast=fast, slow=slow, trend_filter=trend)
    return backtest.run_backtest(
        bars, signals,
        stop_loss_pct=sl, take_profit_pct=tp,
    )


def main():
    print("Ma'lumot tayyorlanmoqda (sintetik)...\n")
    bars = data.get_synthetic_data(days=2000)

    rows = []
    for fast in FAST_OPTIONS:
        for slow in SLOW_OPTIONS:
            if fast >= slow:
                continue
            for trend in TREND_OPTIONS:
                for sl, tp in SL_TP_OPTIONS:
                    r = evaluate(bars, fast, slow, trend, sl, tp)
                    if r.num_trades < 10:        # juda kam savdo = ishonchsiz
                        continue
                    rows.append({
                        "fast": fast, "slow": slow, "trend": trend,
                        "sl": sl, "tp": tp,
                        "ret": r.total_return_pct,
                        "win": r.win_rate,
                        "trades": r.num_trades,
                        "dd": r.max_drawdown_pct,
                        "exp": r.expectancy,
                    })

    # --- Jadvalni chiqaramiz, WIN RATE bo'yicha saralangan ---
    print("=" * 78)
    print("  NATIJALAR (win rate bo'yicha saralangan, yuqoridagisi eng yuqori win rate)")
    print("=" * 78)
    header = f"{'fast':>4} {'slow':>4} {'trend':>5} {'SL%':>5} {'TP%':>5} " \
             f"{'daromad%':>9} {'win%':>6} {'savdo':>6} {'dd%':>7} {'exp$':>7}"
    print(header)
    print("-" * 78)
    for r in sorted(rows, key=lambda x: x["win"], reverse=True):
        print(f"{r['fast']:>4} {r['slow']:>4} {r['trend']:>5} "
              f"{r['sl']*100:>5.1f} {r['tp']*100:>5.1f} "
              f"{r['ret']:>+9.1f} {r['win']:>6.1f} {r['trades']:>6} "
              f"{r['dd']:>7.1f} {r['exp']:>7.1f}")

    # --- Eng yaxshi 3 tasi (daromad bo'yicha) ---
    print("\n" + "=" * 78)
    print("  ENG YAXSHI 3 TA (umumiy daromad bo'yicha)")
    print("=" * 78)
    best = sorted(rows, key=lambda x: x["ret"], reverse=True)[:3]
    for i, r in enumerate(best, 1):
        print(f"{i}) fast={r['fast']} slow={r['slow']} trend={r['trend']} "
              f"SL={r['sl']*100:.1f}% TP={r['tp']*100:.1f}% "
              f"-> daromad {r['ret']:+.1f}%, win {r['win']:.1f}%, "
              f"expectancy ${r['exp']:.1f}/savdo")

    print("\nXULOSA:")
    print(" - Yuqori win% odatda kichikroq TP bilan keladi (lekin foyda kamayishi mumkin).")
    print(" - Trend filtri (trend=200) ko'pincha savdo sonini kamaytiradi, sifatni oshiradi.")
    print(" - AYNAN expectancy ($/savdo) musbat bo'lishi eng muhim — win% emas.")


if __name__ == "__main__":
    main()
