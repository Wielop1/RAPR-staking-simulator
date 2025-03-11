import streamlit as st
import pandas as pd

# --- Helper Functions ---
def calculate_staking(initial_stake, daily_rate, days=7, accumulated_rewards=0.0):
    """
    Calculates staking rewards for 'days' days (7 by default = 1 cycle).
    Daily earnings are constant and are added to accumulated_rewards.
    """
    daily_earnings = initial_stake * (daily_rate / 100)
    total_earnings = accumulated_rewards
    history = []

    for d in range(1, days + 1):
        total_earnings += daily_earnings
        history.append({
            "Day": d,
            "Staked balance (RAPR)": round(initial_stake, 4),
            "Daily earnings (RAPR)": round(daily_earnings, 4),
            "Total rewards (RAPR)": round(total_earnings, 4)
        })

    return history

def calculate_min_profitable_rate(current_daily_earnings, new_stake):
    """
    Calculates the minimum APR (%) required in the new staking
    to earn at least 'current_daily_earnings'.
    """
    if new_stake <= 0:
        return 999.99
    return (current_daily_earnings / new_stake) * 100

# --- Initial App State (Session State) ---
if "cycle" not in st.session_state:
    st.session_state.cycle = 1  # the current cycle number
if "max_cycles" not in st.session_state:
    st.session_state.max_cycles = 5  # maximum number of cycles
if "initial_stake" not in st.session_state:
    st.session_state.initial_stake = 100.0
if "daily_rate" not in st.session_state:
    st.session_state.daily_rate = 1.50
if "acc_rewards" not in st.session_state:
    st.session_state.acc_rewards = 0.0
if "history" not in st.session_state:
    st.session_state.history = []
if "current_daily_earnings" not in st.session_state:
    st.session_state.current_daily_earnings = st.session_state.initial_stake * (st.session_state.daily_rate / 100)

# --- Main Interface ---
st.title("RAPR Staking Simulator")

# 1. Initial Settings (only before the first cycle)
if st.session_state.cycle == 1:
    st.subheader("Initial Settings")
    st.session_state.initial_stake = st.number_input(
        "Initial staking (RAPR):",
        min_value=1.0,
        value=st.session_state.initial_stake,
        key="initial_stake_input"
    )
    st.session_state.daily_rate = st.number_input(
        "Current daily APR (%):",
        min_value=0.01,
        value=st.session_state.daily_rate,
        key="daily_rate_input"
    )
    st.session_state.max_cycles = st.number_input(
        "Maximum number of cycles:",
        min_value=1,
        value=st.session_state.max_cycles,
        key="max_cycles_input"
    )

    if st.button("Start simulation"):
        # Calculate the first cycle (7 days)
        result = calculate_staking(
            st.session_state.initial_stake,
            st.session_state.daily_rate,
            7,
            st.session_state.acc_rewards
        )
        last_row = result[-1]
        st.session_state.acc_rewards = last_row["Total rewards (RAPR)"]
        st.session_state.current_daily_earnings = last_row["Daily earnings (RAPR)"]
        st.session_state.history.append(result)
        st.session_state.cycle = 2

        # Instead of st.experimental_rerun() -> show message
        st.success("First cycle calculated! Rerun in the menu to proceed.")

# 2. If we are in the middle of cycles and have not exceeded max_cycles
elif 1 < st.session_state.cycle <= st.session_state.max_cycles:
    cycle_index = st.session_state.cycle - 1

    # Show data from the previous cycle
    st.subheader(f"Completed Cycle {cycle_index}")
    last_cycle_data = st.session_state.history[-1]
    df = pd.DataFrame(last_cycle_data)
    st.dataframe(df)

    # Display info
    stake_amount = st.session_state.initial_stake
    total_rewards = st.session_state.acc_rewards
    total_balance = stake_amount  # in the old staking, we do not automatically merge stake + rewards
    current_daily_earnings = st.session_state.current_daily_earnings

    st.write(f"You currently have **{stake_amount} RAPR** staked at **{st.session_state.daily_rate}%** APR.")
    st.write(f"Total rewards after the last cycle: **{round(total_rewards, 2)} RAPR**.")
    st.write(f"Your daily earnings: **{round(current_daily_earnings, 2)} RAPR**.")

    # Minimum APR to make a new stake profitable
    new_stake_possible = stake_amount + total_rewards  # if we reinvest everything
    min_rate = calculate_min_profitable_rate(current_daily_earnings, new_stake_possible)
    st.write(f"**Minimum APR** for the new staking to earn more than now: {round(min_rate, 2)}%.")

    choice = st.radio(
        f"Do you want to unstake and restake in Cycle {st.session_state.cycle}?",
        ["No, continue old staking", "Yes, restake with a new rate"],
        key=f"choice_cycle_{st.session_state.cycle}"
    )

    if choice == "No, continue old staking":
        st.info("You continue staking with the same conditions...")
        if st.button("Proceed to the next cycle"):
            result = calculate_staking(
                stake_amount,
                st.session_state.daily_rate,
                7,
                total_rewards
            )
            last_row = result[-1]
            st.session_state.acc_rewards = last_row["Total rewards (RAPR)"]
            st.session_state.current_daily_earnings = last_row["Daily earnings (RAPR)"]
            st.session_state.history.append(result)

            st.session_state.cycle += 1
            st.warning("New cycle calculated! click Rerun in the menu to continue.")

    else:
        st.success("You are doing unstake and restake — combining stake + rewards.")
        new_rate = st.number_input(
            "At what percentage did you manage to restake?",
            min_value=0.01,
            value=max(min_rate, st.session_state.daily_rate),
            key=f"new_rate_cycle_{st.session_state.cycle}"
        )

        if st.button("Confirm and proceed to the next cycle"):
            # Combine stake + rewards
            new_stake_amount = stake_amount + total_rewards
            st.session_state.initial_stake = new_stake_amount
            st.session_state.daily_rate = new_rate
            # Reset old rewards
            st.session_state.acc_rewards = 0.0

            # Calculate a new cycle
            result = calculate_staking(
                st.session_state.initial_stake,
                st.session_state.daily_rate,
                7,
                0.0
            )
            last_row = result[-1]
            st.session_state.acc_rewards = last_row["Total rewards (RAPR)"]
            st.session_state.current_daily_earnings = last_row["Daily earnings (RAPR)"]
            st.session_state.history.append(result)

            st.session_state.cycle += 1
            st.success("New staking started! click Rerun in the menu to continue.")

# 3. If we have exceeded max_cycles
else:
    st.warning("You have reached the maximum number of cycles. The simulation has ended!")
