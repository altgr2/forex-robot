# Forex Bot — o'rganish va backtest loyihasi

Forex savdosini avtomatlashtirishni o'rganish uchun **sof Python** (qo'shimcha
kutubxonasiz) loyiha. Hozircha **faqat backtest** (o'tmish ma'lumotda sinash) —
real pul ishlatilmaydi.

> ⚠️ **OGOHLANTIRISH:** Bu ta'lim maqsadidagi loyiha. Hech qanday strategiya
> kelajakdagi foydani kafolatlamaydi. Real pul tikishdan oldin uzoq vaqt
> demo (virtual pul) akkauntida sinang. Trading yuqori riskli.

## Talablar

- Python 3.8 yoki undan yuqori (Windows/Mac/Linux)
- Qo'shimcha kutubxona **kerak emas**

## Fayllar

| Fayl           | Vazifasi                                                       |
|----------------|----------------------------------------------------------------|
| `data.py`      | Narx ma'lumotini olish (soxta yoki Stooq'dan real)             |
| `strategy.py`  | Strategiya + ISHONCH BALI (confidence score 0..100)            |
| `backtest.py`  | O'tmishda sinash + risk-menejment + `forward_outcome` labellar |
| `calibrate.py` | 80% ishonch gate'ini topish (train/test bo'linishi bilan)      |
| `main.py`      | Hammasini birlashtiruvchi asosiy fayl                          |
| `tune.py`      | Optimizator: eng yaxshi sozlamalarni avtomatik qidirish        |
| `live_mt5.py`  | Botni MetaTrader 5 ga ulab JONLI ishlatish (avval DEMO!)       |

## Ishga tushirish

```bash
# 1) Avval kalibrlash: 80% win rate beradigan sozlamani topadi
python calibrate.py

# 2) Topilgan sozlamani main.py CONFIG ga ko'chiring, keyin:
python main.py

# (ixtiyoriy) turli sozlamalarni sinash
python tune.py
```

Real ma'lumotda sinash uchun `main.py` (yoki `calibrate.py`) ichida
`USE_REAL_DATA = True` qiling (internet kerak, API kalit shart emas).

## 80% ishonch gate (eng muhim qism)

Bot har bir setup uchun **ishonch bali (0..100)** hisoblaydi — qancha shart
bir vaqtda mos kelgani. `MIN_CONFIDENCE` chegarasidan oshgan setuplardagina
savdo qiladi. `calibrate.py` tarixni train/test ga bo'lib, qaysi chegara
**80% yutish foizini** berishini topadi.

### ⚠️ Win rate haqida halol haqiqat

Yuqori win rate o'zi yetarli **EMAS**. Take-profit'ni stop-loss'dan kichik
qilsangiz, win rate sun'iy ravishda 80% ga chiqadi, lekin pul ishlamaysiz:

```
breakeven_win_rate = stop_loss / (stop_loss + take_profit)
```

Masalan `SL=4%, TP=1%` bo'lsa breakeven = 80%. Ya'ni 80% yutib ham foyda = 0!
Shuning uchun bot **ham win rate'ni, ham expectancy'ni** (har savdoda o'rtacha
foyda) tekshiradi. Faqat ikkalasi ham yaxshi bo'lsa savdo qiladi.

Agar `calibrate.py` "80% + musbat expectancy topilmadi" desa — bu **halol
natija**: bu ma'lumotda ishonchli edge yo'q, shuning uchun bot savdo qilmaydi
(pulni saqlaydi).

## Strategiya qisqacha

1. **EMA crossover** — tez va sekin siljuvchi o'rtachalar trend yo'nalishini beradi.
2. **RSI filtri** — yolg'on signallarni kamaytiradi.
3. **Katta trend filtri (EMA 200)** — faqat asosiy trend yo'nalishida savdo.
4. **Ishonch bali + gate** — faqat yuqori ishonchli setuplarda savdo.
5. **Risk-menejment** — har savdoda kapitalning 1% i risk, stop-loss, take-profit.

## Muhim ko'rsatkichlar

- **Win rate (yutuq %)** — savdolarning necha foizi foydali tugagani.
- **Expectancy ($/savdo)** — har savdoda o'rtacha kutilayotgan foyda. **Eng muhim.**
- **Max drawdown** — kapital eng yuqori cho'qqidan eng ko'p qancha tushgani.

## Jonli savdo — MetaTrader 5 (faqat DEMO bilan boshlang!)

> ⛔ **AVVAL DEMO AKKAUNT!** Real pul bilan boshlamang. `live_mt5.py` ichida ikkita
> xavfsizlik qulfi bor: `DRY_RUN = True` (buyurtma yubormaydi, faqat ko'rsatadi) va
> `ALLOW_REAL_ACCOUNT = False` (real akkauntni rad etadi).

Kerakli qadamlar (Windows):

1. MetaTrader 5 dasturini o'rnating va unda **bepul demo akkaunt** oching.
2. MT5 dasturi ochiq tursin (demo akkauntga kirilgan).
3. Python kutubxonasini o'rnating:
   ```bash
   pip install MetaTrader5
   ```
4. Avval xavfsiz sinov (buyurtma yuborilmaydi):
   ```bash
   python live_mt5.py        # DRY_RUN = True bo'lgan holda
   ```
5. Hammasi to'g'ri ko'rsatsa, demo'da haqiqiy buyurtma uchun `live_mt5.py` ichida
   `DRY_RUN = False` qiling (lekin baribir DEMO akkauntda!).
6. Doimiy ishlash uchun `RUN_FOREVER = True` qiling (kompyuter va MT5 ochiq tursin).

Ishlash mantig'i: bot MT5 dan jonli narx oladi → ishonch balini hisoblaydi →
ball `MIN_CONFIDENCE` dan oshsa va ochiq savdo bo'lmasa → stop-loss/take-profit
bilan buyurtma yuboradi. SL/TP ni keyin MT5 o'zi nazorat qiladi.
