import streamlit as st
import pandas as pd
import json
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="Bears Performance Analysis", page_icon="", layout="wide")

col1, col2, col3 = st.columns([1.75, 1, 2])
with col1:
    st.write("")

with col2:
    logo = 'images/bears_logo.png'
    st.image(logo, width=300)

with col3:
    st.write("")

DATA_DIR = 'data_finland'


def load_match(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def get_batters(selected_matches, selected_team):
    batters = set()
    for match_file in selected_matches:
        match_data = load_match(os.path.join(DATA_DIR, match_file))
        for innings in match_data['innings']:
            if innings['team'] == selected_team:
                for over in innings['overs']:
                    for delivery in over['deliveries']:
                        batters.add(delivery['batter'])
    return list(batters)


def get_bowlers(selected_matches, selected_team):
    bowlers = set()
    for match_file in selected_matches:
        match_data = load_match(os.path.join(DATA_DIR, match_file))
        for innings in match_data['innings']:
            if innings['team'] != selected_team:
                for over in innings['overs']:
                    for delivery in over['deliveries']:
                        bowlers.add(delivery['bowler'])
    return list(bowlers)


def get_over_range(over_selection):
    if over_selection == 'Overs 1-6':
        return 1, 6
    elif over_selection == 'Overs 7-15':
        return 7, 15
    elif over_selection == 'Overs 16-20':
        return 16, 20
    else:
        return 1, 20


choice = st.sidebar.selectbox("Choose analysis type: ", ["Batting analysis", "Bowling analysis"])
match_outcome_selection = st.sidebar.selectbox("Match Outcome for Finland:", ["All", "won", "lost", "tied"], index=0)
toss_outcome_selection = st.sidebar.selectbox("Toss Outcome for Finland:", ["All", "won", "lost"], index=0)
venue_selection = st.sidebar.selectbox("Venue for Finland:", ["All", "Home", "Away"], index=0)


def filter_matches_by_selection(matches, match_outcome, toss_outcome, venue):
    filtered_matches = []
    for match_file in matches:
        match_data = load_match(os.path.join(DATA_DIR, match_file))

        if match_outcome != "All":
            if match_outcome == "won":
                outcome_matches = match_data["info"]["outcome"].get("winner", "").lower() == "finland"
            elif match_outcome == "lost":
                outcome_matches = "finland" not in match_data["info"]["outcome"].get("winner", "")
            elif match_outcome == "tied":
                outcome_matches = match_data["info"].get("outcome", {}).get("result", "") == "tie"
        else:
            outcome_matches = True  # Ignore filter if "All"

        if toss_outcome != "All":
            toss_matches = (match_data["info"]["toss"]["winner"].lower() == "finland" if toss_outcome == "won"
                            else match_data["info"]["toss"]["winner"].lower() != "finland")
        else:
            toss_matches = True  # Ignore filter if "All"

        if venue != "All":
            # Assuming 'Home' means Finland is listed first in "teams" and the venue city is in Finland
            is_home_game = match_data["info"]["city"].lower() in ["vantaa", "kerava"]
            venue_matches = (is_home_game if venue == "Home" else not is_home_game)
        else:
            venue_matches = True  # Ignore filter if "All"

        if outcome_matches and toss_matches and venue_matches:
            filtered_matches.append(match_file)

    return filtered_matches


def generate_match_summary_table(filtered_matches):
    match_summaries = []

    for match_file in filtered_matches:
        match_data = load_match(os.path.join(DATA_DIR, match_file))
        # Extracting necessary match info
        match_date = match_data["info"]["dates"][0]
        opponent = [team for team in match_data["info"]["teams"] if team.lower() != "finland"][0]

        # Determine match outcome and details
        if match_data["info"]["outcome"].get("winner", "").lower() == "finland":
            match_outcome = "won"
            if "runs" in match_data["info"]["outcome"]["by"]:
                outcome_detail = f'by {match_data["info"]["outcome"]["by"]["runs"]} runs'
            elif "wickets" in match_data["info"]["outcome"]["by"]:
                outcome_detail = f'by {match_data["info"]["outcome"]["by"]["wickets"]} wickets'
            else:
                outcome_detail = "N/A"
        elif "winner" in match_data["info"]["outcome"]:
            match_outcome = "lost"
            if "runs" in match_data["info"]["outcome"]["by"]:
                outcome_detail = f'by {match_data["info"]["outcome"]["by"]["runs"]} runs'
            elif "wickets" in match_data["info"]["outcome"]["by"]:
                outcome_detail = f'by {match_data["info"]["outcome"]["by"]["wickets"]} wickets'
            else:
                outcome_detail = "N/A"
        else:
            match_outcome = "tied"
            outcome_detail = "N/A"

        toss_winner = match_data["info"]["toss"]["winner"]
        toss_outcome = "won" if toss_winner.lower() == "finland" else "lost"
        city = match_data["info"]["city"]
        venue = "Home" if city.lower() in ["vantaa", "kerava"] else "Away"

        match_summaries.append([match_date, opponent, match_outcome, outcome_detail, toss_outcome, venue])

    # Creating a DataFrame
    columns = ["Date", "Opponent", "Match Outcome", "Outcome Detail", "Toss Outcome", "Venue"]
    match_summary_df = pd.DataFrame(match_summaries, columns=columns)

    return match_summary_df


if choice == "Batting analysis":
    def aggregate_info_batters(selected_matches, selected_deliveries, selected_team, selected_batters, over_selection):
        start_over, end_over = get_over_range(over_selection)
        total_deliveries = 20 * len(selected_matches)
        batter_data = {
            'delivery': [],
            'runs_scored': [],
            'dot_balls': [],
            'fours': [],
            'sixes': [],
            'wickets': [],
            'balls_faced': []
        }

        for match_file in selected_matches:
            match_data = load_match(os.path.join(DATA_DIR, match_file))
            for innings in match_data['innings']:
                if innings['team'] == selected_team:
                    for over in innings['overs']:
                        if start_over <= over['over'] + 1 <= end_over:
                            for delivery_index, delivery in enumerate(over['deliveries'], start=1):
                                if delivery_index in selected_deliveries and delivery['batter'] in selected_batters:
                                    runs = delivery['runs']['batter']
                                    # Initialize wicket as 0 (no wicket)
                                    wicket = 0
                                    # Safely check if 'wickets' key exists and if the batter is the one who got out
                                    if 'wickets' in delivery:
                                        for wicket_info in delivery['wickets']:
                                            if 'player_out' in wicket_info and wicket_info['player_out'] == delivery[
                                                'batter']:
                                                wicket = 1
                                                break  # Break if the batter is found to be out
                                    dots = 1 if runs == 0 else 0
                                    fours = 1 if runs == 4 else 0
                                    sixes = 1 if runs == 6 else 0
                                    batter_data['delivery'].append(delivery_index)
                                    batter_data['runs_scored'].append(runs)
                                    batter_data['dot_balls'].append(dots)
                                    batter_data['fours'].append(fours)
                                    batter_data['sixes'].append(sixes)
                                    batter_data['wickets'].append(wicket)
                                    batter_data['balls_faced'].append(1)

        df = pd.DataFrame(batter_data)
        return df.groupby('delivery').sum().reset_index()

    selected_team = 'Finland'

    col11, col12 = st.columns([1, 1])
    with col11:
        matches = [file for file in os.listdir(DATA_DIR) if file.endswith('.json')]
        selected_matches_user = filter_matches_by_selection(matches, match_outcome_selection, toss_outcome_selection,
                                                       venue_selection)
        selected_matches = st.multiselect('Select Match Files:', options=selected_matches_user, default=selected_matches_user)

    with col12:
        if selected_team and selected_matches:
            # batters = get_batters(selected_matches, selected_team)
            batters = get_batters(selected_matches, selected_team="Finland")
            selected_batters = st.multiselect('Select Batters:', options=batters, default=batters)

    col21, col22 = st.columns([1, 1])
    with col21:
        over_selection = st.selectbox(
            'Select Over Range:',
            options=['All', 'Overs 1-6', 'Overs 7-15', 'Overs 16-20'],
            index=0
        )
    with col22:
        selected_deliveries = st.multiselect('Select Deliveries:', options=list(range(1, 7)),
                                             format_func=lambda x: f"{x}th delivery")

    filtered_matches = filter_matches_by_selection(matches, match_outcome_selection, toss_outcome_selection,
                                                   venue_selection)
    match_summary_table = generate_match_summary_table(filtered_matches)
    st.table(match_summary_table)
    if st.button('Analyze Selected Deliveries for Batters'):
        if not selected_deliveries or not selected_matches or not selected_batters:
            st.error("Please select matches, deliveries, and batters.")
        else:
            batter_df = aggregate_info_batters(selected_matches, selected_deliveries, selected_team, selected_batters,
                                               over_selection)

            if not batter_df.empty:
                fig, axes = plt.subplots(1, 5, figsize=(25, 5))
                # metrics = ['runs_scored', 'dot_balls', 'fours', 'sixes', 'balls_faced']
                bars = axes[0].bar(batter_df['delivery'],
                                   round((batter_df['runs_scored'] * 100) / batter_df['balls_faced'], 1),
                                   color='lightblue')
                axes[0].bar_label(bars)
                axes[0].set_xlabel('Ball number')
                axes[0].set_ylabel('')
                axes[0].set_title(f'Batting innings strike-rate')

                bars = axes[1].bar(batter_df['delivery'], round(batter_df['dot_balls'], 1), color='lightgreen')
                axes[1].bar_label(bars)
                axes[1].set_xlabel('Ball number')
                axes[1].set_ylabel('')
                axes[1].set_title(f'No. of dot balls faced')

                bars = axes[2].bar(batter_df['delivery'], round(batter_df['fours'], 1), color='orange')
                axes[2].bar_label(bars)
                axes[2].set_xlabel('Ball number')
                axes[2].set_ylabel('')
                axes[2].set_title(f'No. of 4s scored')

                bars = axes[3].bar(batter_df['delivery'], round(batter_df['sixes'], 1), color='red')
                axes[3].bar_label(bars)
                axes[3].set_xlabel('Ball number')
                axes[3].set_ylabel('')
                axes[3].set_title(f'No. of 6s scored')

                bars = axes[4].bar(batter_df['delivery'], round(batter_df['wickets'], 1), color='purple')
                axes[4].bar_label(bars)
                axes[4].set_xlabel('Ball number')
                axes[4].set_ylabel('')
                axes[4].set_title(f'Wickets lost')

                # plt.tight_layout()
                st.pyplot(fig)
            else:
                st.write("No data available for the selected deliveries.")

elif choice == "Bowling analysis":
    def aggregate_and_average_info(selected_matches, selected_deliveries, selected_team, selected_bowlers,
                                   over_selection):
        start_over, end_over = get_over_range(over_selection)
        total_deliveries = 20 * len(selected_matches)
        aggregate_data = {
            'delivery': [],
            'runs': [],
            'wickets': [],
            'dots': [],
            'fours': [],
            'sixes': [],
            'balls_faced': []
        }

        for match_file in selected_matches:
            match_data = load_match(os.path.join(DATA_DIR, match_file))
            for innings in match_data['innings']:
                if innings['team'] != selected_team:  # Get deliveries faced by the selected team
                    for over in innings['overs']:
                        if start_over <= over['over'] + 1 <= end_over:
                            for delivery_index, delivery in enumerate(over['deliveries'], start=1):
                                if delivery_index in selected_deliveries and delivery['bowler'] in selected_bowlers:
                                    runs = delivery['runs']['total']
                                    wickets = 1 if 'wickets' in delivery else 0
                                    dots = 1 if runs == 0 else 0
                                    fours = 1 if runs == 4 else 0
                                    sixes = 1 if runs == 6 else 0

                                    aggregate_data['delivery'].append(delivery_index)
                                    aggregate_data['runs'].append(runs)
                                    aggregate_data['wickets'].append(wickets)
                                    aggregate_data['dots'].append(dots)
                                    aggregate_data['fours'].append(fours)
                                    aggregate_data['sixes'].append(sixes)
                                    aggregate_data['balls_faced'].append(1)

        df = pd.DataFrame(aggregate_data)
        if not df.empty:
            avg_df = df.groupby('delivery').sum().reset_index()

            for column in avg_df.columns:
                if column not in ['delivery', 'runs', 'wickets', 'dots', 'fours', 'sixes', 'balls_faced']:
                    avg_df[column] = avg_df[column] / total_deliveries
        else:
            avg_df = pd.DataFrame()
        return avg_df

    selected_team = 'Finland'

    row11, row12 = st.columns([1, 1])
    with row11:
        matches = [file for file in os.listdir(DATA_DIR) if file.endswith('.json')]
        selected_matches_user = filter_matches_by_selection(matches, match_outcome_selection, toss_outcome_selection,
                                                            venue_selection)
        selected_matches = st.multiselect('Select Match Files:', options=selected_matches_user,
                                          default=selected_matches_user)

    with row12:
        if selected_team and selected_matches:
            bowlers = get_bowlers(selected_matches, selected_team="Finland")
            selected_bowlers = st.multiselect('Select Bowlers:', options=bowlers, default=bowlers)

    row21, row22 = st.columns([1, 1])
    with row21:
        over_selection = st.selectbox(
            'Select Over Range:',
            options=['All', 'Overs 1-6', 'Overs 7-15', 'Overs 16-20'],
            index=0
        )
    with row22:
        selected_deliveries = st.multiselect('Select Deliveries:', options=list(range(1, 7)),
                                             format_func=lambda x: f"{x}th delivery")

    filtered_matches = filter_matches_by_selection(matches, match_outcome_selection, toss_outcome_selection,
                                                   venue_selection)
    match_summary_table = generate_match_summary_table(filtered_matches)
    st.table(match_summary_table)
    if st.button('Analyze Selected Deliveries for Team and Bowlers'):
        if not selected_deliveries or not selected_matches or not selected_team or not selected_bowlers:
            st.error("Please select matches, deliveries, a team, and bowlers.")
        else:
            avg_df = aggregate_and_average_info(selected_matches, selected_deliveries, selected_team,
                                                selected_bowlers, over_selection)

            if not avg_df.empty:
                fig, axes = plt.subplots(1, 5, figsize=(25, 5))

                bars = axes[0].bar(avg_df['delivery'], round((avg_df['runs'] * 100) / avg_df['balls_faced'], 1),
                                   color='lightblue')
                axes[0].bar_label(bars)
                axes[0].set_xlabel('Ball number')
                axes[0].set_ylabel('')
                axes[0].set_title(f'Bowling innings strike-rate')

                bars = axes[1].bar(avg_df['delivery'], round(avg_df['dots'], 1), color='lightgreen')
                axes[1].bar_label(bars)
                axes[1].set_xlabel('Ball number')
                axes[1].set_ylabel('')
                axes[1].set_title(f'Dot balls bowled')

                bars = axes[2].bar(avg_df['delivery'], round(avg_df['fours'], 1), color='orange')
                axes[2].bar_label(bars)
                axes[2].set_xlabel('Ball number')
                axes[2].set_ylabel('')
                axes[2].set_title(f'4s conceded')

                bars = axes[3].bar(avg_df['delivery'], round(avg_df['sixes'], 1), color='red')
                axes[3].bar_label(bars)
                axes[3].set_xlabel('Ball number')
                axes[3].set_ylabel('')
                axes[3].set_title(f'6s conceded')

                bars = axes[4].bar(avg_df['delivery'], round(avg_df['wickets'], 1), color='purple')
                axes[4].bar_label(bars)
                axes[4].set_xlabel('Ball number')
                axes[4].set_ylabel('')
                axes[4].set_title(f'Wickets taken')

                st.pyplot(fig)

            else:
                st.write("No data available for the selected options.")
