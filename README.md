# Forex Bot — o'rganish va backtest loyihasi

Forex savdosini avtomatlashtirishni o'rganish uchun **sof Python** (qo'shimcha
kutubxonasiz) loyiha. Hozircha **faqat backtest** (o'tmish ma'lumotda sinash) —
real pul ishlatilmaydi.

> ⚠️ **OGOHLANTIRISH:** Bu ta'lim maqsadidagi loyiha. Hech qanday strategiya
> kelajakdagi foydani kafolatlamaydi. Real pul tikishdan oldin uzoq vaqt
> demo (virtual pul) akkauntida sinang. Trading yuqori riskli.

## Talablar

- Python 3.10 yoki undan yuqori (Windows/Mac/Linux)
- Qo'shimcha kutubxona **kerak emas**

## Fayllar

| Fayl          | Vazifasi                                                |
|---------------|---------------------------------------------------------|
| `data.py`     | Narx ma'lumotini olish (soxta yoki Stooq'dan real)      |
| `strategy.py` | Savdo strategiyasi: EMA crossover + RSI + trend filtri  |
| `backtest.py` | O'tmish ma'lumotda sinash + risk-menejment + statistika |
| `main.py`     | Hammasini birlashtiruvchi asosiy fayl                   |
| `tune.py`     | Optimizator: eng yaxshi sozlamalarni avtomatik qidirish |

## Ishga tushirish

```bash
# Asosiy backtest (soxta ma'lumotda)
python main.py

# Turli sozlamalarni sinab ko'rish (optimizator)
python tune.py
```

Real ma'lumotda sinash uchun `main.py` ichida `USE_REAL_DATA = True` qiling
(internet kerak, lekin API kalit yoki ro'yxatdan o'tish shart emas).

## Strategiya qisqacha

1. **EMA crossover** — tez va sekin siljuvchi o'rtachalar kesishishi trend yo'nalishini beradi.
2. **RSI filtri** — yolg'on signallarni kamaytiradi.
3. **Katta trend filtri (EMA 200)** — faqat asosiy trend yo'nalishida savdo qiladi.
4. **Risk-menejment** — har savdoda kapitalning 1% i risk, stop-loss va take-profit.

## Muhim ko'rsatkichlar

- **Win rate (yutuq %)** — savdolarning necha foizi foydali tugagani.
- **Expectancy ($/savdo)** — har savdoda o'rtacha kutilayotgan foyda. **Eng muhim ko'rsatkich.**
- **Max drawdown** — kapital eng yuqori cho'qqidan eng ko'p qancha tushgani.
