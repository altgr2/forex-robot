"""
calibrate.py — "80% ishonch gate" ni TOPISH.

ISHGA TUSHIRISH:
    python calibrate.py

Bu fayl sizning talabingizni amalga oshiradi:
    "Yutish foizi 80% dan oshmasa savdo qilmasin, oshgandagina savdo qilsin."

QANDAY ISHLAYDI:
  1. Har bir setup uchun ishonch bali (0..100) hisoblanadi (strategy.py).
  2. Tarix IKKIGA bo'linadi:
        - TRAIN (o'rganish) qismi — bu yerda qaysi ball darajasi 80% win rate
          berishini topamiz.
        - TEST (sinov) qismi — topilgan chegarani YANGI ma'lumotda tekshiramiz.
     Bu "o'tmishga moslab qo'yib, kelajakda yiqilish" (overfitting) xavfini ochadi.
  3. Faqat TEST'da ham 80% saqlangan VA expectancy MUSBAT bo'lgan sozlama tavsiya etiladi.

MUHIM TUSHUNCHA — breakeven win rate:
  Agar take-profit stop-loss'dan kichik bo'lsa, win rate yuqori chiqadi, LEKIN
  pul ishlash uchun win rate "breakeven" dan oshishi shart:
        breakeven = stop_loss / (stop_loss + take_profit)
  Masalan SL=4%, TP=1% bo'lsa breakeven = 80%. Ya'ni 80% yutib ham FOYDA = 0!
  Shuning uchun biz win rate'ni ham, expectancy'ni ham birga tekshiramiz.
"""

import data
import strategy
import backtest

# --- Sozlamalar ---
USE_REAL_DATA = False        # True qilsangiz Stooq'dan real ma'lumot (internet kerak)
SYMBOL = "eurusd"
TARGET_WIN_RATE = 80.0       # siz xohlagan minimal yutish foizi (%)
MIN_TRAIN_TRADES = 20        # ishonchli xulosa uchun minimal savdo soni (train)
MIN_TEST_TRADES = 10         # minimal savdo soni (test)
TRAIN_FRACTION = 0.60        # ma'lumotning qancha qismi o'rganish uchun

FAST, SLOW, TREND = 20, 50, 200
CONFIDENCE_LEVELS = [40, 55, 70, 85, 100]

# (stop_loss, take_profit) variantlari — turli risk:reward nisbatlari
SL_TP_OPTIONS = [
    (0.020, 0.020),   # 1:1   -> breakeven 50%
    (0.025, 0.0125),  # 2:1   -> breakeven 66.7%
    (0.030, 0.015),   # 2:1   -> breakeven 66.7%
    (0.030, 0.010),   # 3:1   -> breakeven 75%
    (0.040, 0.010),   # 4:1   -> breakeven 80%  (ogohlantirish uchun)
]


def build_labeled_setups(bars, sl, tp):
    """Har bir setup uchun (index, score, outcome 0/1) ro'yxatini quradi."""
    scored = strategy.score_setups(bars, FAST, SLOW, trend_filter=TREND)
    labeled = []
    for i, (direction, score) in enumerate(scored):
        if direction == 0:
            continue
        outcome = backtest.forward_outcome(bars, i, direction, sl, tp)
        if outcome is None:
            continue
        labeled.append((i, score, outcome))
    return labeled


def win_rate(subset):
    if not subset:
        return 0.0
    return sum(o for _, _, o in subset) / len(subset) * 100


def main():
    if USE_REAL_DATA:
        print(f"Real ma'lumot yuklanmoqda: {SYMBOL} ...\n")
        bars = data.get_real_data(SYMBOL)
    else:
        print("Sintetik ma'lumot ishlatilmoqda (internetsiz).\n")
        bars = data.get_synthetic_data(days=2500)

    split = int(len(bars) * TRAIN_FRACTION)
    print(f"Jami {len(bars)} kun. Train: 0..{split}, Test: {split}..{len(bars)}")
    print(f"Maqsad: win rate >= {TARGET_WIN_RATE:.0f}% VA expectancy > 0\n")

    print("=" * 92)
    print(f"{'SL%':>5} {'TP%':>5} {'R:R':>5} {'b/even%':>7} {'chegara':>8} "
          f"{'train win%':>10} {'train n':>8} {'TEST win%':>9} {'test n':>7} "
          f"{'exp(R)':>7}")
    print("-" * 92)

    candidates = []
    for sl, tp in SL_TP_OPTIONS:
        labeled = build_labeled_setups(bars, sl, tp)
        train = [s for s in labeled if s[0] < split]
        test = [s for s in labeled if s[0] >= split]

        rr = tp / sl
        breakeven = sl / (sl + tp) * 100

        # Train'da 80% ga yetadigan ENG KICHIK chegarani topamiz
        chosen_thr = None
        for thr in CONFIDENCE_LEVELS:
            tr = [s for s in train if s[1] >= thr]
            if len(tr) >= MIN_TRAIN_TRADES and win_rate(tr) >= TARGET_WIN_RATE:
                chosen_thr = thr
                break

        if chosen_thr is None:
            print(f"{sl*100:>5.1f} {tp*100:>5.1f} {rr:>5.1f} {breakeven:>7.1f} "
                  f"{'—':>8} {'(80% ga yetmadi)':>30}")
            continue

        tr = [s for s in train if s[1] >= chosen_thr]
        te = [s for s in test if s[1] >= chosen_thr]
        tr_wr = win_rate(tr)
        te_wr = win_rate(te)
        te_n = len(te)

        # Expectancy (R birligida): win = +RR, loss = -1
        wr_frac = te_wr / 100
        expectancy_R = wr_frac * rr - (1 - wr_frac) * 1

        print(f"{sl*100:>5.1f} {tp*100:>5.1f} {rr:>5.1f} {breakeven:>7.1f} "
              f"{chosen_thr:>8} {tr_wr:>10.1f} {len(tr):>8} "
              f"{te_wr:>9.1f} {te_n:>7} {expectancy_R:>7.2f}")

        if te_n >= MIN_TEST_TRADES:
            candidates.append({
                "sl": sl, "tp": tp, "thr": chosen_thr,
                "test_wr": te_wr, "test_n": te_n, "exp_R": expectancy_R,
            })

    print("=" * 92)

    # --- Tavsiya: TEST'da 80% saqlagan VA expectancy musbatlar ichidan eng yaxshisi ---
    good = [c for c in candidates
            if c["test_wr"] >= TARGET_WIN_RATE and c["exp_R"] > 0]

    if not good:
        print("\nXULOSA: TEST ma'lumotida 80% win rate + musbat expectancy'ni bir vaqtda")
        print("saqlagan sozlama TOPILMADI. Bu — overfitting xavfining real isboti.")
        print("Bu HALOL natija: hozirgi ma'lumotda bot 80% kafolatini bera olmaydi,")
        print("shuning uchun u savdo qilmasligi KERAK (pulni saqlaydi).")
        if candidates:
            best = max(candidates, key=lambda c: c["exp_R"])
            print(f"\nEng yaqin variant: SL={best['sl']*100:.1f}% TP={best['tp']*100:.1f}% "
                  f"chegara={best['thr']} -> test win {best['test_wr']:.1f}%, "
                  f"expectancy {best['exp_R']:.2f}R")
        return

    best = max(good, key=lambda c: c["exp_R"])
    print("\nTAVSIYA ETILGAN SOZLAMA (test'da 80%+ va musbat expectancy):")
    print(f"   STOP_LOSS      = {best['sl']}")
    print(f"   TAKE_PROFIT    = {best['tp']}")
    print(f"   MIN_CONFIDENCE = {best['thr']}")
    print(f"   -> test win rate {best['test_wr']:.1f}%, expectancy {best['exp_R']:.2f}R")

    # --- Tavsiya etilgan sozlama bilan to'liq backtest (ketma-ket, real savdo simulyatsiyasi) ---
    print("\nShu sozlama bilan to'liq backtest:")
    signals = strategy.generate_signals(
        bars, fast=FAST, slow=SLOW, trend_filter=TREND, min_confidence=best["thr"]
    )
    result = backtest.run_backtest(
        bars, signals, stop_loss_pct=best["sl"], take_profit_pct=best["tp"]
    )
    print(f"   Savdolar soni : {result.num_trades}")
    print(f"   Yutish foizi  : {result.win_rate:.1f}%")
    print(f"   Umumiy daromad: {result.total_return_pct:+.2f}%")
    print(f"   Max drawdown  : {result.max_drawdown_pct:.2f}%")
    print(f"   Expectancy    : ${result.expectancy:.2f}/savdo")
    print("\nShu 3 raqamni main.py ichidagi CONFIG ga ko'chiring.")


if __name__ == "__main__":
    main()
