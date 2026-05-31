"""
strategy.py — Savdo strategiyasi (qachon sotib olish/sotish).

Sof Python — qo'shimcha kutubxona kerak emas.

Strategiya:
  1) EMA crossover (ikki silliqlangan o'rtacha narx kesishishi):
       - Tez EMA sekin EMA dan YUQORIga chiqsa -> trend YUQORI (sotib olish moyilligi)
       - Tez EMA sekin EMA dan PASTga tushsa  -> trend PAST  (sotish moyilligi)
  2) RSI filtri (0..100 kuch ko'rsatkichi):
       - Yolg'on signallarni kamaytirish uchun ishlatiladi.

Maqsad: oddiy, lekin shovqinni kamaytiradigan, ishonchli signal berish.
"""

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

    # Dastlabki o'rtacha (oddiy o'rtacha)
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


def generate_signals(
    bars: list[Bar],
    fast: int = 20,
    slow: int = 50,
    rsi_period: int = 14,
    trend_filter: int = 0,
) -> list[int]:
    """
    Har bir kun uchun signal qaytaradi:
        1  -> LONG  (narx ko'tariladi deb o'ylaymiz)
       -1  -> SHORT (narx tushadi deb o'ylaymiz)
        0  -> hech narsa qilmaymiz

    trend_filter:
        0  -> o'chiq.
        >0 -> KATTA trend filtri (masalan 200). Bu uzun muddatli EMA.
              Faqat katta trend yo'nalishida savdo qilamiz:
                - narx katta-EMA dan YUQORIDA bo'lsa -> faqat LONG ruxsat
                - narx katta-EMA dan PASTDA bo'lsa   -> faqat SHORT ruxsat
              Bu "oqimga qarshi suzmaslik" qoidasi — sifatni va win rate'ni oshiradi.
    """
    closes = [b.close for b in bars]
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    rsi_vals = rsi(closes, rsi_period)
    ema_trend = ema(closes, trend_filter) if trend_filter > 0 else None

    warmup = max(slow, trend_filter)

    signals = [0] * len(bars)
    for i in range(len(bars)):
        # Indikatorlar "qizib ulgurishi" uchun boshlang'ich davrni o'tkazamiz
        if i < warmup:
            continue

        up_trend = ema_fast[i] > ema_slow[i]
        down_trend = ema_fast[i] < ema_slow[i]

        # Katta trend filtri (agar yoqilgan bo'lsa)
        big_up = big_down = True
        if ema_trend is not None:
            big_up = closes[i] > ema_trend[i]
            big_down = closes[i] < ema_trend[i]

        if up_trend and big_up and 50 < rsi_vals[i] < 70:
            signals[i] = 1
        elif down_trend and big_down and 30 < rsi_vals[i] < 50:
            signals[i] = -1

    return signals
