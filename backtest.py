"""
backtest.py — Strategiyani O'TMISH ma'lumotda sinash (real pulsiz).

Sof Python — qo'shimcha kutubxona kerak emas.

Bu bizga shuni aytadi:
  - Strategiya o'tmishda foyda berarmidi yoki zarar?
  - Necha marta savdo qildi?
  - Necha foiz savdo yutdi (win rate)?
  - Eng yomon pasayish qancha edi (max drawdown)?

ESLATMA: o'tmishdagi yaxshi natija kelajakni KAFOLATLAMAYDI.
Lekin yomon backtest = aniq yomon strategiya. Bu birinchi filtr.
"""

from dataclasses import dataclass, field

from data import Bar


@dataclass
class Trade:
    """Bitta savdo natijasi."""
    direction: int      # 1 = LONG, -1 = SHORT
    entry_price: float
    exit_price: float
    entry_date: str
    exit_date: str
    profit: float
    reason: str         # "TP" (foyda), "SL" (zarar), yoki "signal"


@dataclass
class BacktestResult:
    start_balance: float
    end_balance: float
    trades: list = field(default_factory=list)
    equity_curve: list = field(default_factory=list)  # (sana, balans) ro'yxati

    @property
    def total_return_pct(self) -> float:
        return (self.end_balance / self.start_balance - 1) * 100

    @property
    def num_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        wins = sum(1 for t in self.trades if t.profit > 0)
        return wins / len(self.trades) * 100

    @property
    def avg_win(self) -> float:
        wins = [t.profit for t in self.trades if t.profit > 0]
        return sum(wins) / len(wins) if wins else 0.0

    @property
    def avg_loss(self) -> float:
        losses = [t.profit for t in self.trades if t.profit < 0]
        return sum(losses) / len(losses) if losses else 0.0

    @property
    def expectancy(self) -> float:
        """
        Har savdoda o'rtacha kutilayotgan foyda ($).
        expectancy = (yutuq% * o'rtacha yutuq) - (zarar% * o'rtacha zarar)
        Bu MUSBAT bo'lishi shart — aks holda strategiya uzoq muddatda yo'qotadi.
        Win rate emas, AYNAN shu raqam strategiya yaxshimi-yomonligini ko'rsatadi.
        """
        if not self.trades:
            return 0.0
        return sum(t.profit for t in self.trades) / len(self.trades)

    @property
    def max_drawdown_pct(self) -> float:
        """Kapital eng yuqori cho'qqidan eng ko'p qancha tushgani (foizda)."""
        if not self.equity_curve:
            return 0.0
        peak = self.equity_curve[0][1]
        max_dd = 0.0
        for _, bal in self.equity_curve:
            peak = max(peak, bal)
            dd = (bal - peak) / peak
            max_dd = min(max_dd, dd)
        return max_dd * 100


def run_backtest(
    bars: list[Bar],
    signals: list[int],
    start_balance: float = 10_000.0,
    risk_per_trade: float = 0.01,   # har savdoda kapitalning 1% i bilan risk
    stop_loss_pct: float = 0.01,    # narx 1% qarshi ketsa -> chiqamiz (zarar)
    take_profit_pct: float = 0.02,  # narx 2% foydaga ketsa -> chiqamiz (foyda)
) -> BacktestResult:
    """
    Soddalashtirilgan, lekin to'g'ri risk-menejmentli backtest.

    Risk-menejment qoidasi:
      - Har savdoda kapitalning faqat `risk_per_trade` (1%) qismi xavf ostida.
      - Stop-loss katta zarardan himoya qiladi.
      - Take-profit foydani qulflaydi.
      - Risk:Reward = 1:2 (1% xavf, 2% maqsad).
    """
    balance = start_balance
    position = 0          # 0 = ochiq savdo yo'q, 1 = LONG, -1 = SHORT
    entry_price = 0.0
    entry_date = ""
    units = 0.0
    stop_price = 0.0
    target_price = 0.0

    trades: list[Trade] = []
    equity_curve: list = []

    for i, bar in enumerate(bars):
        signal = signals[i]

        # --- 1) Ochiq savdo bo'lsa, chiqish shartini tekshiramiz ---
        if position != 0:
            exit_now = False
            reason = ""
            exit_price = bar.close

            if position == 1:  # LONG
                if bar.low <= stop_price:
                    exit_now, reason, exit_price = True, "SL", stop_price
                elif bar.high >= target_price:
                    exit_now, reason, exit_price = True, "TP", target_price
                elif signal == -1:
                    exit_now, reason = True, "signal"
            else:              # SHORT
                if bar.high >= stop_price:
                    exit_now, reason, exit_price = True, "SL", stop_price
                elif bar.low <= target_price:
                    exit_now, reason, exit_price = True, "TP", target_price
                elif signal == 1:
                    exit_now, reason = True, "signal"

            if exit_now:
                profit = (exit_price - entry_price) * units * position
                balance += profit
                trades.append(Trade(
                    direction=position,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    entry_date=entry_date,
                    exit_date=bar.date,
                    profit=profit,
                    reason=reason,
                ))
                position = 0

        # --- 2) Ochiq savdo yo'q va signal bor bo'lsa, kiramiz ---
        if position == 0 and signal != 0:
            position = signal
            entry_price = bar.close
            entry_date = bar.date

            if position == 1:  # LONG
                stop_price = entry_price * (1 - stop_loss_pct)
                target_price = entry_price * (1 + take_profit_pct)
            else:              # SHORT
                stop_price = entry_price * (1 + stop_loss_pct)
                target_price = entry_price * (1 - take_profit_pct)

            # Position sizing: faqat `risk_per_trade` qadar risk qilamiz.
            risk_amount = balance * risk_per_trade
            price_risk = abs(entry_price - stop_price)
            units = risk_amount / price_risk if price_risk > 0 else 0.0

        equity_curve.append((bar.date, balance))

    return BacktestResult(
        start_balance=start_balance,
        end_balance=balance,
        trades=trades,
        equity_curve=equity_curve,
    )
