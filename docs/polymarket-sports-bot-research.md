# Polymarket Sports Bot: Quantitative Research Brief

**Scope**: NBA + EPL binary outcome markets on Polymarket CLOB
**Capital**: $25k staged ($1k → $3k → $7.5k → $25k)
**Infrastructure**: Standard VPS, no colo
**Style**: Maker-first, selective taker, low/medium frequency intraday

---

## 1. Strategy Archetypes

### Strategy A: Model-vs-Market Fair Value (Must-Have)

Build an independent implied-probability model; trade when your model disagrees with the CLOB mid by more than a threshold edge.

- **Entry**: Place limit order (maker) when `|P_model - P_market| > edge_threshold`
  - NBA: `edge_threshold >= 3.5 cents` (accounts for ~2c round-trip cost + margin)
  - EPL: `edge_threshold >= 4.0 cents` (wider spreads, less liquid)
- **Exit**: Cancel/replace when edge collapses below `1.5 cents`, or on fill + immediate hedge quote on opposite side
- **Model inputs**: Team ELO/SRS, injury reports, rest days, home/away, referee tendencies (NBA), xG/xGA rolling (EPL), recent form (last 5), line movement from sportsbooks (Pinnacle, Betfair as reference)
- **Position sizing**: Half-Kelly on estimated edge, capped at 2% of stage capital per market
- **Why it works here**: Polymarket sports markets are thin enough (~$10k–$100k total liquidity on game markets) that pricing lags sharp sportsbooks by minutes to hours, especially on injury/lineup news

### Strategy B: Cross-Venue Stale Quote Arbitrage (Must-Have)

Monitor sharp sportsbook lines (Pinnacle, Betfair exchange) and trade against stale Polymarket quotes that haven't adjusted.

- **Entry**: When reference sportsbook implied-prob moves > `5 cents` and Polymarket hasn't repriced within `T_stale` window (typically 30s–5min)
  - Taker order if edge > `6 cents` and size available
  - Maker order 1–2 cents inside the stale quote if edge is 4–6 cents
- **Exit**: Fill-and-forget (single-leg, directional), or cancel if Polymarket reprices before fill
- **Key requirement**: Fast polling of Polymarket orderbook (1–5s intervals) + sportsbook odds feed (API or scrape)
- **Capacity**: Low — these windows are infrequent (5–15/day across NBA+EPL) and small ($50–$500 per event)
- **Why it works here**: Polymarket has no native market-maker obligation, so quotes can go stale for minutes

### Strategy C: In-Play Momentum / Live Event Repricing (Nice-to-Have)

For markets with live resolution triggers (e.g., NBA game win market while game is in progress), reprice faster than the rest of the book.

- **Entry**: Consume live game data (score, time remaining, possession) → compute win probability via simple model (log5 or lookup table) → post maker orders at model price when book is > `4 cents` stale
- **Exit**: Lift/cancel as model converges toward market
- **Constraint**: Only viable if Polymarket lists in-play markets (currently limited for sports). Monitor for expansion.
- **Risk**: Fast-moving state; requires sub-10s pricing loop
- **Why it's nice-to-have**: Highest theoretical edge but requires the most infrastructure investment and is event-dependent

### Archetype Ranking by Viability

| Criteria | A: Fair Value | B: Stale Quote | C: In-Play |
|---|---|---|---|
| Edge durability | High | Medium | High |
| Capacity ($) | Medium | Low | Low-Medium |
| Infrastructure need | Low | Medium | High |
| Data complexity | Medium | Low | High |
| **Priority** | **#1** | **#2** | **#3 (defer)** |

---

## 2. Required Data Fields & API Availability

### Must-Have Data

| Field | Source | Available via Official API? | Notes |
|---|---|---|---|
| CLOB orderbook (bids/asks, depth) | Polymarket CLOB API | **Yes** — REST + WebSocket | `GET /book` endpoint, ~1s polling viable |
| Market metadata (question, outcomes, end date) | Polymarket Gamma API | **Yes** | `/markets` endpoint |
| Trade/fill history | Polymarket CLOB API | **Yes** — `/trades` endpoint | Needed for spread/slippage estimation |
| Your order status + fills | Polymarket CLOB API | **Yes** — authenticated endpoints | Via API key + HMAC signing |
| Mid-market price / last trade | Polymarket CLOB API | **Yes** — `/price` and `/trades` | |
| USDC balance / positions | Polymarket CLOB API | **Yes** — `/positions` | On Polygon |
| Sportsbook reference odds (Pinnacle) | Pinnacle API / The Odds API | **No** — external, paid ($50–$150/mo) | Critical for Strategy B |
| NBA box scores / injury reports | NBA API / ESPN API / basketball-reference | **No** — external, free/cheap | For Strategy A model |
| EPL fixtures / xG data | football-data.org / FBref / Understat | **No** — external, free | For Strategy A model |

### Nice-to-Have Data

| Field | Source | Available? | Notes |
|---|---|---|---|
| Polymarket historical CLOB data | Polymarket (no official historical endpoint) | **Partial** — must self-collect or use community archives | Critical for backtest; start recording now |
| Betfair exchange prices | Betfair API | External, free tier available | Sharpest reference for EPL |
| Live game state (score, clock) | ESPN/NBA API / Sportradar | External, $0–$500/mo | Strategy C only |
| On-chain settlement data | Polygon RPC | Yes (public blockchain) | For verifying resolution mechanics |
| Social/news sentiment | Twitter API / news APIs | External | Low signal-to-noise; skip initially |

### Critical Gap

Polymarket does **not** provide official historical orderbook or trade-level data via API. You must:
1. Self-collect starting now (record orderbook snapshots + trades every 5–15s)
2. Use on-chain transaction history as partial substitute (settlement prices, volumes)
3. Acknowledge backtest will be limited to forward-collected data or synthetic replay

---

## 3. Backtest Design

### Avoiding Leakage

- **Strict train/test temporal split**: Train on months M1–M3, test on M4. Never retrain on test data.
- **No future information in features**: All sportsbook odds, injury data, and game stats must be timestamped and joined as-of (point-in-time). Use `as_of_join`, never a standard merge on game_id.
- **Orderbook simulation**: Replay actual recorded orderbook states. Never assume you can fill at mid; simulate queue position for maker orders (see slippage model below).
- **Market selection bias**: Include ALL markets that existed during the period, not just ones that had interesting outcomes. Pull the full market list per day from your recorded data.

### Avoiding Survivorship Bias

- **Include voided/resolved-early markets**: Some Polymarket sports markets get voided (game postponed, rule change). These must appear in your backtest as zero-return or small-loss trades (gas/spread cost).
- **Include illiquid markets you would have skipped**: Track markets you filtered out due to low liquidity — compute what would have happened to confirm your filter is additive.
- **Walk-forward validation**: Retrain model monthly on expanding window, test on next month. Report walk-forward Sharpe, not in-sample Sharpe.

### Minimum Backtest Requirements

- **Duration**: >= 60 NBA game-days + >= 30 EPL match-days of recorded data before trusting results
- **Sample size**: >= 200 trades in the test set for statistical significance
- **Significance**: Strategy Sharpe > 0 at p < 0.05 (one-tailed t-test on daily returns)

---

## 4. Slippage & Fees Model

### Fee Structure (Polymarket as of 2024–2025)

| Component | Value | Notes |
|---|---|---|
| Maker fee | **0 bps** (0%) | Polymarket currently charges 0 maker fees |
| Taker fee | **0 bps** (0%) | Polymarket currently charges 0 taker fees (was previously ~1-2%) |
| Gas (Polygon) | **$0.001–$0.01 per tx** | Negligible; model as $0.005 flat |
| Spread cost (half-spread) | **1.0–3.0 cents** | NBA liquid markets ~1c; EPL ~2–3c |
| USDC deposit/withdraw | **Variable** | Bridge costs if moving from Ethereum; ~$1–5 |

**Important**: Fee structure can change. Model a **conservative 1% round-trip fee** in backtests as buffer, even if current fees are 0. This protects against fee reintroduction.

### Slippage Model for Maker Orders

- **Fill probability**: Model as function of (distance from mid, time-in-force, volatility)
  - Orders at mid: ~40–60% fill rate within 5 minutes (thin books)
  - Orders 1c inside best bid/ask: ~70–85% fill rate
  - Orders 2c+ inside: ~90%+ but negative edge
- **Adverse selection**: Assume 15–25% of maker fills are adversely selected (filled because the market moved against you). Deduct this from expected PnL.
- **Queue priority**: You are NOT first in queue on a standard VPS. Assume you are in the back 50% of queue at any price level.

### Slippage Model for Taker Orders

- **Market impact**: For orders < $200, assume 0–1 cent impact. For $200–$1000, assume 1–3 cents. For > $1000, walk the book explicitly.
- **Latency slippage**: On standard VPS (~50–200ms to Polymarket), assume 0.5–1.5 cents of adverse price movement on time-sensitive taker orders (Strategy B).

### Conservative Backtest Assumptions

```
round_trip_cost = max(0.01, spread_cost) + gas + adverse_selection_haircut
                = 0.02 (spread) + 0.005 (gas) + 0.01 (adverse selection)
                = 0.035 per contract (3.5 cents)
```

Use **3.5 cents per contract round-trip** as the baseline friction assumption. If your strategy's average edge per trade is < 3.5 cents, it is not viable.

---

## 5. KPI Pass/Fail Gates Per Capital Stage

### Stage 1: $1,000 (Proof of Concept)

| KPI | Pass Threshold | Fail / Kill |
|---|---|---|
| Duration | >= 30 calendar days | — |
| Number of trades | >= 50 | < 30 trades (insufficient signal) |
| Net PnL | > $0 (profitable after fees) | < -$50 (5% drawdown) |
| Win rate | > 52% on binary outcomes | < 48% |
| Sharpe (daily, annualized) | > 1.0 | < 0.3 |
| Max drawdown | < 3% ($30) | > 5% ($50) → kill |
| System uptime | > 95% of intended trading hours | < 80% → fix infra first |
| Largest single loss | < $20 (2%) | > $30 (3%) → review sizing |

### Stage 2: $3,000 (Validation)

| KPI | Pass Threshold | Fail / Kill |
|---|---|---|
| Duration | >= 45 calendar days | — |
| Number of trades | >= 120 | < 80 |
| Monthly net return | > 2.5% | < 0% for any 30-day rolling window |
| Sharpe (daily, annualized) | > 1.2 | < 0.5 |
| Max drawdown | < 4% ($120) | > 6% ($180) → kill |
| Profit factor | > 1.3 | < 1.1 |
| Edge decay monitoring | Model edge per trade stable or improving | Edge declining > 1c/month → investigate |
| Daily hard stop breaches | 0 | Any breach → review risk system |

### Stage 3: $7,500 (Scaling Test)

| KPI | Pass Threshold | Fail / Kill |
|---|---|---|
| Duration | >= 60 calendar days | — |
| Monthly net return | > 3.5% | < 1.5% (capacity ceiling) |
| Sharpe | > 1.5 | < 0.8 |
| Max drawdown | < 5% ($375) | > 7% ($525) → kill |
| Market impact | No measurable increase in spread cost as size doubles | Cost increase > 1c → capacity limit reached |
| Fill rate degradation | < 10% decline vs Stage 2 | > 20% decline → capacity issue |
| Correlation to reference book | < 0.3 to S&P / BTC | > 0.5 → hidden factor exposure |

### Stage 4: $25,000 (Full Deployment)

| KPI | Pass Threshold | Ongoing Monitor |
|---|---|---|
| Monthly net return | > 4% target | < 2% for 2 consecutive months → reduce size |
| Sharpe | > 1.5 | < 1.0 → reduce to Stage 3 capital |
| Max drawdown | < 5% ($1,250) | > 8% ($2,000) → halt and review |
| Annual target | 48–72% gross, 35–55% net of costs | — |

### Mandatory Hold Period Between Stages

- **Minimum 2 weeks** of passing all KPIs before scaling up
- **Must pass on walk-forward (live) data**, not just backtest

---

## 6. Failure Modes & Kill-Switch Rules

### Automated Kill Switches (Must-Have)

| Trigger | Action | Reset Condition |
|---|---|---|
| Daily PnL < -1.0% of capital | Halt all new orders, cancel open orders | Manual review + next trading day |
| Weekly PnL < -3.5% of capital | Halt all trading for remainder of week | Manual review + new week |
| Single trade loss > 0.5% of capital | Flag + reduce position sizing by 50% | Review sizing model |
| 5 consecutive losing trades | Pause 1 hour, re-evaluate model signals | Auto-resume after pause |
| Orderbook depth < $500 on target market | Skip market (do not trade illiquid) | Depth recovers > $1,000 |
| API error rate > 10% in 5-min window | Halt trading, alert | API recovers for 5 min |
| Position in single market > 5% of capital | Block new orders in that market | Position reduced below 3% |
| Unfilled maker orders > 80% for 1 day | Flag potential model staleness | Review model calibration |

### Structural Failure Modes

| Failure Mode | Indicators | Response |
|---|---|---|
| **Edge erosion** | Declining Sharpe over 30-day rolling, edge per trade compressing | Reduce capital to prior stage; investigate if more sophisticated competitors entered |
| **Liquidity withdrawal** | Orderbook depth declining >50%, spreads widening | Reduce position sizes; may need to exit market entirely |
| **Polymarket fee change** | Fee announcement | Immediately re-run backtest with new fees; halt if strategy breaks even |
| **Regulatory action** | US regulatory pressure on prediction markets | Accelerate withdrawal timeline; do not add new capital |
| **Oracle/resolution risk** | Disputed outcomes, delayed resolution, UMA oracle issues | Cap exposure per market; diversify across resolution sources |
| **Adverse selection spiral** | Win rate on maker fills declining below 45% | Widen spread requirements; you're getting picked off by faster participants |
| **API deprecation/change** | Endpoint changes, rate limit tightening | Maintain abstraction layer; budget 1–2 days for migration |
| **Correlated loss event** | All 8 concurrent positions lose simultaneously | Review correlation assumptions; likely means model has hidden factor |

### Manual Review Triggers

- Any single day with > 20 trades (possible runaway loop)
- Any market where your position > 10% of total market open interest
- Any 7-day period where realized edge < 50% of backtested edge

---

## 7. Probability-Weighted Return Expectations

### Monthly Net Return Scenarios

| Scenario | Probability | Monthly Net | Annualized | Assumptions |
|---|---|---|---|---|
| **Bear** | 30% | -1.0% to +1.5% | -12% to +18% | Edge exists but is thin (2–3c); adverse selection eats 40% of gross; liquidity is lower than expected; capacity ceiling at ~$5k deployed |
| **Base** | 45% | +2.5% to +4.5% | +30% to +54% | Model edge of 3.5–5c per trade; fill rate ~50% on maker; 100–200 trades/month; slippage in line with model; able to deploy $15–20k |
| **Bull** | 25% | +5.0% to +8.0% | +60% to +96% | Market is inefficient and slow to correct; few sophisticated competitors; fill rates >60%; edge >5c per trade; full $25k deployable |

### Expected Value Calculation

```
E[monthly] = 0.30 * 0.25% + 0.45 * 3.5% + 0.25 * 6.5%
           = 0.075% + 1.575% + 1.625%
           = 3.275% monthly expected (before capital staging friction)
```

### Reality Adjustments

- **Capital staging friction**: During months 1–4, you're running at $1k–$3k, not $25k. Absolute returns will be small. Budget 4–6 months before reaching full capital deployment.
- **Decay factor**: Assume 10–20% annual edge decay as market matures and more participants enter.
- **Survivorship of strategy**: ~60% probability the strategy is still viable at month 12; ~40% at month 24.

### Is 4–6% Monthly Net Realistic?

**Conditionally yes**, but with caveats:
- Achievable in the **base-to-bull** range (70% of scenarios include 4%+ in at least some months)
- **Not consistently achievable** every month — expect 2–3 months per year below target even in bull scenario
- **Capacity-constrained**: At $25k you may be fine, but this likely does not scale to $100k+ without significant edge compression
- **Time-limited**: This edge profile is characteristic of immature markets. Budget 12–24 months of viability.

---

## 8. What Makes This Untradeable Despite Positive Backtest

### Definite Kill Conditions

1. **Backtest-to-live degradation > 60%**: If live Sharpe is < 40% of backtested Sharpe after 50+ trades, the backtest is overfit or the market regime has shifted. Do not continue.

2. **Effective capacity < $2k**: If market impact analysis shows you cannot deploy more than $2k without moving prices, the absolute return potential ($80–$120/month) does not justify the operational overhead.

3. **Fill rate on maker orders < 25%**: Your capital sits idle and opportunity cost (even in T-bills at ~4.5%) dominates. The strategy becomes worse than passive.

4. **Polymarket re-introduces > 2% round-trip fees**: Combined with spread and adverse selection, total friction would likely exceed 5 cents — eliminating viable edge for most trades.

5. **Regulatory shutdown risk becomes material**: If CFTC takes enforcement action against Polymarket (not just warning letters), exit entirely regardless of PnL.

6. **Orderbook is dominated by 1–2 sophisticated market makers**: If you observe consistent sub-second repricing after reference sportsbook moves, you cannot compete on a standard VPS. Strategy B dies; Strategy A edge compresses to < 2 cents.

7. **Resolution disputes > 5% of markets traded**: Oracle risk makes position sizing impossible to calibrate. You're not trading sports outcomes anymore; you're trading resolution mechanism risk.

8. **Your model's out-of-sample Brier score is worse than the market's**: If the market is better calibrated than your model, you have no edge. Specifically: if `brier_score_model > brier_score_market + 0.02`, stop.

### Warning Signs (Investigate, Don't Auto-Kill)

- Median time-to-fill on maker orders increasing month-over-month
- Concentration of PnL: >50% of profits from <10% of trades (fragile)
- Edge only present in one sport (NBA or EPL but not both) — halves your capacity
- Systematic loss on high-profile games (market is efficient when attention is high)

---

## Appendix: Implementation Priority Order

| Week | Task | Deliverable |
|---|---|---|
| 1–2 | Data collection infrastructure | Orderbook recorder running 24/7; sportsbook odds feed live |
| 3–4 | Strategy A model (fair value) | NBA + EPL probability model with Brier score < market |
| 5–6 | Paper trading system | Full order management on testnet/paper with realistic fills |
| 7–8 | Strategy B implementation | Cross-venue stale quote detector + execution logic |
| 9–10 | Backtest framework | Walk-forward backtest on 30+ days of collected data |
| 11–12 | Stage 1 live ($1k) | Deploy with full kill-switch infrastructure |

---

*This document is a research brief, not financial advice. Prediction market trading involves substantial risk of loss. All return projections are estimates based on stated assumptions and may not reflect actual results.*
