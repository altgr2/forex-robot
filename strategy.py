"""
strategy.py — Savdo strategiyasi va ISHONCH BALI (confidence score).

Sof Python — qo'shimcha kutubxona kerak emas.

Asosiy g'oya:
  Har bir kun uchun biz nafaqat "LONG yoki SHORT" deymiz, balki bu signalga
  qanchalik ISHONISHIMIZNI 0..100 ball bilan baholaymiz.

  Ishonch bali = qancha shart bir vaqtda mos kelgani.
  Qancha ko'p shart mos kelsa, signal shuncha ishonchli.

  Keyin (calibrate.py da) biz tarixda tekshiramiz: qaysi ball darajasida
  yutish foizi 80% dan oshadi? Va bot FAQAT shu chegaradan oshgan setuplarda
  savdo qiladi.
"""

from __future__ import annotations

from data import Bar


def ema(values: list[float], period: int) -> list[float]:
    """Eksponensial siljuvchi o'rtacha (Exponential Moving Average)."""
    if not values:
        return []
    out = [values[0]] * len(values)
    mult = 2 / (period + 1)
    for i in range(1, len(values)):
        out[i] = (values[i] - out[i - 1]) * mult + out[i - 1]
    return out


def rsi(values: list[float], period: int = 14) -> list[float]:
    """
    RSI (Relative Strength Index) — Wilder usuli.
    Birinchi `period` ta qiymat uchun 50 (neytral) qaytaramiz.
    """
    n = len(values)
    result = [50.0] * n
    if n < period + 1:
        return result

    gains = [0.0] * n
    losses = [0.0] * n
    for i in range(1, n):
        change = values[i] - values[i - 1]
        gains[i] = max(change, 0.0)
        losses[i] = max(-change, 0.0)

    avg_gain = sum(gains[1:period + 1]) / period
    avg_loss = sum(losses[1:period + 1]) / period

    def to_rsi(ag: float, al: float) -> float:
        if al == 0:
            return 100.0
        rs = ag / al
        return 100 - (100 / (1 + rs))

    result[period] = to_rsi(avg_gain, avg_loss)
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        result[i] = to_rsi(avg_gain, avg_loss)

    return result


def score_setups(
    bars: list[Bar],
    fast: int = 20,
    slow: int = 50,
    rsi_period: int = 14,
    trend_filter: int = 200,
) -> list[tuple[int, int]]:
    """
    Har bir kun uchun (direction, score) qaytaradi:
        direction:  1 = LONG nomzodi, -1 = SHORT nomzodi, 0 = setup yo'q
        score:      0..100 — signalga ISHONCH darajasi

    Ishonch quyidagi mustaqil tasdiqlovchi shartlardan yig'iladi.
    Har biri ma'lum ball beradi; jami 100 ga yetadi.
    """
    closes = [b.close for b in bars]
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    rsi_vals = rsi(closes, rsi_period)
    ema_trend = ema(closes, trend_filter) if trend_filter > 0 else None

    warmup = max(slow, trend_filter, rsi_period) + 5
    n = len(bars)
    out: list[tuple[int, int]] = [(0, 0)] * n

    for i in range(n):
        if i < warmup:
            continue

        up_trend = ema_fast[i] > ema_slow[i]
        down_trend = ema_fast[i] < ema_slow[i]

        # Katta trend yo'nalishi
        big_up = big_down = True
        if ema_trend is not None:
            big_up = closes[i] > ema_trend[i]
            big_down = closes[i] < ema_trend[i]

        # EMA qiyaligi (slope) — trend kuchaymoqdami?
        fast_rising = ema_fast[i] > ema_fast[i - 3]
        fast_falling = ema_fast[i] < ema_fast[i - 3]
        slow_rising = ema_slow[i] > ema_slow[i - 5]
        slow_falling = ema_slow[i] < ema_slow[i - 5]

        # --- LONG nomzodi ---
        if up_trend and big_up:
            score = 40  # asosiy shart bajarildi (trend + katta trend)
            if 50 < rsi_vals[i] < 65:      # sog'lom momentum (haddan oshmagan)
                score += 15
            if slow_rising:                # sekin EMA ko'tarilmoqda
                score += 15
            if fast_rising:                # tez EMA ko'tarilmoqda
                score += 15
            if closes[i] > ema_fast[i]:    # narx tez EMA dan yuqorida
                score += 15
            out[i] = (1, min(score, 100))

        # --- SHORT nomzodi ---
        elif down_trend and big_down:
            score = 40
            if 35 < rsi_vals[i] < 50:
                score += 15
            if slow_falling:
                score += 15
            if fast_falling:
                score += 15
            if closes[i] < ema_fast[i]:
                score += 15
            out[i] = (-1, min(score, 100))

    return out


def generate_signals(
    bars: list[Bar],
    fast: int = 20,
    slow: int = 50,
    rsi_period: int = 14,
    trend_filter: int = 200,
    min_confidence: int = 0,
) -> list[int]:
    """
    Signal qaytaradi (1 = LONG, -1 = SHORT, 0 = hech narsa).

    min_confidence:
        Faqat ishonch bali shu qiymatdan KATTA yoki TENG bo'lgan setuplar
        signalga aylanadi. Qolganlari 0 (savdo yo'q).
        Bu — sizning "80% dan oshganda savdo qil" talabingizning yuragi.
        (Aniq qiymatni calibrate.py topadi.)
    """
    scored = score_setups(bars, fast, slow, rsi_period, trend_filter)
    signals = [0] * len(bars)
    for i, (direction, score) in enumerate(scored):
        if direction != 0 and score >= min_confidence:
            signals[i] = direction
    return signals
