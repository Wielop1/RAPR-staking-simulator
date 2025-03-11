import streamlit as st
import pandas as pd

# --- Funkcje pomocnicze ---
def calculate_staking(initial_stake, daily_rate, days=7, accumulated_rewards=0.0):
    """
    Oblicza nagrody w stakingu na 'days' dni (domyślnie 7 = 1 cykl).
    Zarobki dzienne są stałe, a sumują się do accumulated_rewards.
    """
    daily_earnings = initial_stake * (daily_rate / 100)
    total_earnings = accumulated_rewards
    history = []

    for d in range(1, days + 1):
        total_earnings += daily_earnings
        history.append({
            "Dzień": d,
            "Saldo stakowane (RAPR)": round(initial_stake, 4),
            "Zarobki dzienne (RAPR)": round(daily_earnings, 4),
            "Suma nagród (RAPR)": round(total_earnings, 4)
        })

    return history

def calculate_min_profitable_rate(current_daily_earnings, new_stake):
    """
    Oblicza minimalne APR (w %) potrzebne w nowym stakingu, by zarabiać >= current_daily_earnings.
    """
    if new_stake <= 0:
        return 999.99
    return (current_daily_earnings / new_stake) * 100

# --- Inicjalizacja stanu aplikacji (Session State) ---
if "cycle" not in st.session_state:
    st.session_state.cycle = 1  # numer aktualnego cyklu
if "max_cycles" not in st.session_state:
    st.session_state.max_cycles = 5  # maksymalna liczba cykli
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

# --- Interfejs główny ---
st.title("Symulator Stakingu RAPR — krok po kroku (bez experimental_rerun)")

# 1. Ustawienia początkowe (tylko przed pierwszym cyklem)
if st.session_state.cycle == 1:
    st.subheader("Ustawienia początkowe")
    st.session_state.initial_stake = st.number_input(
        "Początkowy staking (RAPR):",
        min_value=1.0,
        value=st.session_state.initial_stake,
        key="initial_stake_input"
    )
    st.session_state.daily_rate = st.number_input(
        "Obecne dzienne oprocentowanie (%):",
        min_value=0.01,
        value=st.session_state.daily_rate,
        key="daily_rate_input"
    )
    st.session_state.max_cycles = st.number_input(
        "Maksymalna liczba cykli:",
        min_value=1,
        value=st.session_state.max_cycles,
        key="max_cycles_input"
    )

    if st.button("Rozpocznij symulację"):
        # Obliczenia dla pierwszego cyklu
        result = calculate_staking(
            st.session_state.initial_stake,
            st.session_state.daily_rate,
            7,
            st.session_state.acc_rewards
        )
        last_row = result[-1]
        st.session_state.acc_rewards = last_row["Suma nagród (RAPR)"]
        st.session_state.current_daily_earnings = last_row["Zarobki dzienne (RAPR)"]
        st.session_state.history.append(result)
        st.session_state.cycle = 2

        # Zamiast st.experimental_rerun() -> komunikat
        st.success("Pierwszy cykl obliczony! Odśwież stronę lub kliknij Rerun w menu, by zobaczyć kolejny krok.")

# 2. Jeśli jesteśmy w trakcie cykli i nie przekroczyliśmy max_cycles
elif 1 < st.session_state.cycle <= st.session_state.max_cycles:
    cycle_index = st.session_state.cycle - 1

    # Wyświetlamy dane z poprzedniego cyklu
    st.subheader(f"Zakończony Cykl {cycle_index}")
    last_cycle_data = st.session_state.history[-1]
    df = pd.DataFrame(last_cycle_data)
    st.dataframe(df)

    # Obliczenia do wyświetlenia
    stake_amount = st.session_state.initial_stake
    total_rewards = st.session_state.acc_rewards
    total_balance = stake_amount  # w starym stakingu nie łączymy automatycznie stake + rewards
    current_daily_earnings = st.session_state.current_daily_earnings

    st.write(f"Aktualnie stakowałeś **{stake_amount} RAPR** przy oprocentowaniu **{st.session_state.daily_rate}%**.")
    st.write(f"Suma nagród po ostatnim cyklu: **{round(total_rewards, 2)} RAPR**.")
    st.write(f"Twoje zarobki dzienne wynoszą: **{round(current_daily_earnings, 2)} RAPR**.")

    # Minimalne oprocentowanie, by opłacało się restake
    new_stake_possible = stake_amount + total_rewards  # jeśli byśmy reinwestowali całość
    min_rate = calculate_min_profitable_rate(current_daily_earnings, new_stake_possible)
    st.write(f"**Minimalne oprocentowanie** nowego stakingu, aby zarabiać więcej: {round(min_rate, 2)}%.")

    choice = st.radio(
        f"Czy chcesz robić unstake i restake w Cyklu {st.session_state.cycle}?",
        ["Nie, kontynuuję stary staking", "Tak, restakuję z nową stawką"],
        key=f"choice_cycle_{st.session_state.cycle}"
    )

    if choice == "Nie, kontynuuję stary staking":
        st.info("Kontynuujesz staking na tych samych warunkach...")
        if st.button("Przejdź do kolejnego cyklu"):
            result = calculate_staking(
                stake_amount,
                st.session_state.daily_rate,
                7,
                total_rewards
            )
            last_row = result[-1]
            st.session_state.acc_rewards = last_row["Suma nagród (RAPR)"]
            st.session_state.current_daily_earnings = last_row["Zarobki dzienne (RAPR)"]
            st.session_state.history.append(result)

            st.session_state.cycle += 1
            st.warning("Nowy cykl obliczony! Odśwież stronę lub kliknij Rerun w menu, by przejść dalej.")

    else:
        st.success("Robisz unstake i restake — wrzucasz stake + nagrody.")
        new_rate = st.number_input(
            "Na jaki procent udało Ci się zastakować?",
            min_value=0.01,
            value=max(min_rate, st.session_state.daily_rate),
            key=f"new_rate_cycle_{st.session_state.cycle}"
        )

        if st.button("Zatwierdź i przejdź do kolejnego cyklu"):
            # Sumujemy stake + rewards
            new_stake_amount = stake_amount + total_rewards
            st.session_state.initial_stake = new_stake_amount
            st.session_state.daily_rate = new_rate
            # Zerujemy poprzednie nagrody
            st.session_state.acc_rewards = 0.0

            # Obliczamy nowy cykl
            result = calculate_staking(
                st.session_state.initial_stake,
                st.session_state.daily_rate,
                7,
                0.0
            )
            last_row = result[-1]
            st.session_state.acc_rewards = last_row["Suma nagród (RAPR)"]
            st.session_state.current_daily_earnings = last_row["Zarobki dzienne (RAPR)"]
            st.session_state.history.append(result)

            st.session_state.cycle += 1
            st.success("Nowy staking rozpoczęty! Odśwież stronę lub kliknij Rerun w menu, by przejść dalej.")

# 3. Jeśli przekroczyliśmy max_cycles
else:
    st.warning("Osiągnąłeś maksymalną liczbę cykli. Koniec symulacji!")
