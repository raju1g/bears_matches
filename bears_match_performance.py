import streamlit as st
import pandas as pd
import json
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="Bears Performance Analysis", page_icon=":cricket_game:", layout="wide")

col1, col2, col3 = st.columns([1.75, 1, 2])
with col1:
    # Intentionally left blank for spacing
    st.write("")

with col2:
    logo = 'images/bears_logo.png'  # Replace with the path to your logo
    st.image(logo, width=300)

with col3:
    # Intentionally left blank for spacing
    st.write("")

DATA_DIR = 'data_finland'  # Update this path according to your directory structure


# Function to load a match file
def load_match(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


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


# Revised function to get unique bowlers for the selected team across selected matches
def get_bowlers(selected_matches, selected_team):
    bowlers = set()
    for match_file in selected_matches:
        match_data = load_match(os.path.join(DATA_DIR, match_file))
        for innings in match_data['innings']:
            # Get bowlers from the innings where the team is not the selected team
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
    else:  # 'All'
        return 1, 20  # Assuming T20 match for maximum overs


choice = st.sidebar.selectbox("Choose analysis type: ", ["Batting analysis", "Bowling analysis"])

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


    # # UI Components
    # title_html = """
    #     <style>
    #         .title {
    #             font-family: "Arial", sans-serif;
    #             font-size: 24px;
    #             font-weight: bold;
    #             color: black;  # Change to your desired color
    #             text-align: justify;
    #         }
    #     </style>
    #     <div class="title">Bears Batting Analysis</div>
    # """
    # st.markdown(title_html, unsafe_allow_html=True)
    #st.title('Bears Batting Analysis')
    selected_team = 'Finland'
    #st.write(f'Team {selected_team}')

    col11, col12 = st.columns([1, 1])
    with col11:
        matches = [file for file in os.listdir(DATA_DIR) if file.endswith('.json')]
        selected_matches = st.multiselect('Select Match Files:', options=matches, default=matches)
    with col12:
        if selected_team and selected_matches:
            batters = get_batters(selected_matches, selected_team)
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
            # st.table(avg_df)
        else:
            avg_df = pd.DataFrame()  # Return an empty dataframe if no data was aggregated

        # Return both the averaged DataFrame and the total runs DataFrame
        return avg_df


    # Streamlit UI Components
    # st.title('Bears Bowling Analysis')

    selected_team = 'Finland'  # This could be dynamically generated
    #st.write(f'Team {selected_team}')

    row11, row12 = st.columns([1, 1])
    with row11:
        matches = os.listdir(DATA_DIR)
        selected_matches = st.multiselect('Select Match Files:', options=matches, default=matches)

    with row12:
        if selected_team and selected_matches:
            bowlers = get_bowlers(selected_matches, selected_team)
            selected_bowlers = st.multiselect('Select Bowlers:', options=bowlers, default=bowlers)

    row21, row22 = st.columns([1, 1])
    with row21:
        over_selection = st.selectbox(
            'Select Over Range:',
            options=['All', 'Overs 1-6', 'Overs 7-15', 'Overs 16-20'],
            index=0  # Default selection is 'All'
        )
    with row22:
        selected_deliveries = st.multiselect('Select Deliveries:', options=list(range(1, 7)),
                                             format_func=lambda x: f"{x}th delivery")

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
                axes[0].set_title(f'Opposition strike-rate')

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

                # plt.tight_layout()
                st.pyplot(fig)

            else:
                st.write("No data available for the selected options.")
