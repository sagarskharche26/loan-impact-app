import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------
# Loan Amortization Functions
# ----------------------------

def amortization_schedule(P, r_annual, years, extra_annual=0):
    r = r_annual / 12 / 100          # monthly interest rate
    n = int(years * 12)              # number of payments
    EMI = P * r * (1 + r)**n / ((1 + r)**n - 1)

    balance = P
    schedule = []

    for month in range(1, n + 1):
        interest = balance * r
        principal = EMI - interest

        # Apply extra payment once per year (at year-end)
        if extra_annual > 0 and month % 12 == 0:
            principal += extra_annual

        balance -= principal

        if balance < 0:  # Loan fully paid early
            principal += balance
            balance = 0

        schedule.append([month, principal, interest, balance])

        if balance <= 0:
            break

    df = pd.DataFrame(schedule, columns=["Month", "Principal", "Interest", "Balance"])
    total_interest = df["Interest"].sum()
    total_months = int(df["Month"].iloc[-1])

    return df, total_interest, total_months

# ----------------------------
# Investment FV (annual contributions, compounded annually)
# ----------------------------
def future_value_annuity(annual_contrib, annual_return_pct, years):
    # ordinary annuity: contributions at end of each period
    r = annual_return_pct / 100.0
    n = years
    if n <= 0 or annual_contrib == 0:
        return 0.0
    if abs(r) < 1e-12:
        # no growth
        return annual_contrib * n
    fv = annual_contrib * ((1 + r)**n - 1) / r
    return fv

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("🏠 Home Loan Impact — Pay Extra vs Invest")
st.write("Compare the effect of making extra annual principal payments vs investing that same annual amount in a portfolio with a given annual return.")

st.sidebar.header("Loan Inputs")

# Sliders + manual input
P = st.sidebar.number_input("Principal Amount (₹)", min_value=100_000, max_value=100_000_000, value=5_000_000, step=50_000, format="%d")
r = st.sidebar.slider("Annual Interest Rate (%)", min_value=1.0, max_value=20.0, value=8.0, step=0.1)
years = st.sidebar.slider("Tenure (Years)", min_value=1, max_value=40, value=20)
extra = st.sidebar.number_input("Extra Annual Payment (₹)", min_value=0, max_value=5_000_000, value=50_000, step=10_000, format="%d")

st.sidebar.header("Investment Comparison")
annual_return = st.sidebar.slider("Annual Portfolio Return (%)", min_value=0.0, max_value=30.0, value=7.0, step=0.1)

# ----------------------------
# Compute amortization
# ----------------------------
df_base, interest_base, months_base = amortization_schedule(P, r, years, extra_annual=0)
df_extra, interest_extra, months_extra = amortization_schedule(P, r, years, extra_annual=extra)

# ----------------------------
# Comparison Metrics
# ----------------------------
interest_saved = max(0.0, interest_base - interest_extra)
years_saved = (months_base - months_extra) / 12.0

# Investment scenario: invest 'extra' annually while keeping loan at normal schedule
# Invest for the original loan tenure (months_base / 12)
years_invest = months_base / 12.0
fv_invest = future_value_annuity(extra, annual_return, years_invest)
total_invested = extra * years_invest
returns_earned = fv_invest - total_invested  # profit earned

st.subheader("📊 Results Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Interest (Normal)", f"₹{interest_base:,.0f}")
col2.metric("Interest (With Extra)", f"₹{interest_extra:,.0f}")
col3.metric("Interest Saved", f"₹{interest_saved:,.0f}")

col4, col5, col6 = st.columns(3)
col4.metric("Tenure (Normal)", f"{months_base/12:.1f} years")
col5.metric("Tenure (With Extra)", f"{months_extra/12:.2f} years")
col6.metric("Tenure Saved", f"{years_saved:.2f} years")

st.markdown("---")
st.subheader("💡 Investment vs Extra Payment (Default)")
c1, c2 = st.columns(2)
c1.metric("Annual Invest Amount", f"₹{extra:,.0f}")
c1.metric("Investment Horizon (Original Loan)", f"{years_invest:.1f} years")
c2.metric("Portfolio Annual Return", f"{annual_return:.2f}%")
c2.metric("Future Value (Invest, original horizon)", f"₹{fv_invest:,.0f}")

st.write(f"Total invested amount if invested annually for original loan tenure: ₹{total_invested:,.0f}")
st.write(f"Returns earned (profit) from investing for original loan tenure: ₹{returns_earned:,.0f}")

net_benefit = returns_earned - interest_saved
if net_benefit > 0:
    st.success(f"Net benefit (Investing for original tenure - Interest Saved): ₹{net_benefit:,.0f} → Investing (original horizon) yields more.")
elif net_benefit < 0:
    st.error(f"Net benefit (Investing for original tenure - Interest Saved): ₹{net_benefit:,.0f} → Paying extra yields more interest-savings.")
else:
    st.info(f"Net benefit: ₹{net_benefit:,.0f} → Both options roughly equal.")

# ----------------------------
# Graph 1: Interest vs Principal Breakdown
# ----------------------------
st.subheader("📈 Cumulative Interest & Principal over Time")

fig1, ax1 = plt.subplots(figsize=(10, 5))

ax1.plot(df_base["Month"], df_base["Interest"].cumsum(), label="Interest (Normal)", linewidth=2)
ax1.plot(df_extra["Month"], df_extra["Interest"].cumsum(), label="Interest (With Extra)", linewidth=2)
ax1.plot(df_base["Month"], df_base["Principal"].cumsum(), label="Principal (Normal)", linestyle="--")
ax1.plot(df_extra["Month"], df_extra["Principal"].cumsum(), label="Principal (With Extra)", linestyle="--")

ax1.set_xlabel("Month")
ax1.set_ylabel("Cumulative Amount (₹)")
ax1.legend()
ax1.grid(True)

st.pyplot(fig1)

# ----------------------------
# Graph 2: Interest Saved vs Returns Earned (Investing Same Annual Amount)
# ----------------------------
st.subheader("📊 Interest Saved vs Returns Earned (Investing Same Annual Amount)")

labels = ["Interest Saved (₹)", "Returns Earned (₹)"]
values = [interest_saved, returns_earned]

fig2, ax2 = plt.subplots(figsize=(8, 4))
bars = ax2.bar(labels, values)
ax2.set_ylabel("Amount (₹)")
ax2.set_title("Interest Saved vs Returns Earned (original horizon)")
ax2.grid(axis="y", linestyle="--", alpha=0.4)

# Annotate bars with values
for bar in bars:
    height = bar.get_height()
    ax2.annotate(f"₹{height:,.0f}",
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 6),
                 textcoords="offset points",
                 ha='center', va='bottom')

ax2.axhline(0, color='black', linewidth=0.8)
st.pyplot(fig2)

# ----------------------------
# Optional comparison for shortened loan period (button)
# ----------------------------
st.markdown("---")
if st.button("Compare investing for shortened loan period (optional)"):
    st.subheader("🔁 Investing only for the shortened loan period (Optional)")

    # Investment horizon: shortened loan period (months_extra / 12)
    years_short = months_extra / 12.0
    fv_invest_short = future_value_annuity(extra, annual_return, years_short)
    total_invested_short = extra * years_short
    returns_earned_short = fv_invest_short - total_invested_short

    st.write(f"Shortened loan period (with extra payments): {years_short:.2f} years ({months_extra} months).")
    st.write(f"Future Value if invested annually for shortened period: ₹{fv_invest_short:,.0f}")
    st.write(f"Total invested (shortened period): ₹{total_invested_short:,.0f}")
    st.write(f"Returns earned (shortened period): ₹{returns_earned_short:,.0f}")

    net_benefit_short = returns_earned_short - interest_saved
    if net_benefit_short > 0:
        st.success(f"Net benefit (Investing for shortened period - Interest Saved): ₹{net_benefit_short:,.0f} → Investing while loan lasts (shortened) yields more.")
    elif net_benefit_short < 0:
        st.error(f"Net benefit (Investing for shortened period - Interest Saved): ₹{net_benefit_short:,.0f} → Paying extra yields more interest-savings.")
    else:
        st.info(f"Net benefit: ₹{net_benefit_short:,.0f} → Both options roughly equal for shortened horizon.")

    # Enhanced bar chart: 3 bars (Interest saved, Returns original horizon, Returns shortened horizon)
    labels3 = ["Interest Saved (₹)", "Returns (orig horizon)", "Returns (short horizon)"]
    values3 = [interest_saved, returns_earned, returns_earned_short]

    fig4, ax4 = plt.subplots(figsize=(9, 4))
    bars3 = ax4.bar(labels3, values3)
    ax4.set_ylabel("Amount (₹)")
    ax4.set_title("Interest Saved vs Returns (original vs shortened horizon)")
    ax4.grid(axis="y", linestyle="--", alpha=0.4)

    for bar in bars3:
        h = bar.get_height()
        ax4.annotate(f"₹{h:,.0f}",
                     xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 6),
                     textcoords="offset points",
                     ha='center', va='bottom')

    ax4.axhline(0, color='black', linewidth=0.8)
    st.pyplot(fig4)

else:
    st.info("Click the button above to compare investing only for the shortened loan period (optional).")

st.markdown("---")
st.subheader("📄 Amortization Table (With Extra Payments)")
st.dataframe(df_extra)
