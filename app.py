import streamlit as st
import pandas as pd
import math
import plotly.express as px

st.set_page_config(
    page_title="Brock's CFB Model",
    page_icon="🏈",
    layout="wide"
)

# ==================================================
# DATA
# ==================================================

ratings = pd.read_csv("ratings_dataset.csv")
games = pd.read_csv("games.csv")

HOME_FIELD = 2.5
RATING_SCALE = 17

team_lookup = {}

for _, row in ratings.iterrows():
    team_lookup[row["Team"]] = row

teams = sorted(
    ratings["Team"].tolist()
)

# ==================================================
# FUNCTIONS
# ==================================================

def matchup_adjustment(team_a, team_b):

    sr_edge = (
        team_a["Off_SR"]
        - team_b["Def_SR"]
    )

    explosive_edge = (
        team_a["Off_Explosive"]
        - team_b["Def_Explosive"]
    )

    havoc_edge = (
        team_a["Def_Havoc"]
        - team_b["Off_Havoc"]
    )

    return (
        sr_edge * 3
        + explosive_edge * 2
        + havoc_edge * 2
    )


def predict_game(home_team, away_team):

    team_a = team_lookup[home_team]
    team_b = team_lookup[away_team]

    rating_diff = (
        team_a["Rating"]
        - team_b["Rating"]
    ) * RATING_SCALE

    matchup = matchup_adjustment(
        team_a,
        team_b
    )

    spread = (
        rating_diff
        + matchup
        + HOME_FIELD
    )

    probability = (
        1 /
        (1 + math.exp(-spread / 6))
    )

    return (
        spread,
        probability,
        rating_diff,
        matchup
    )


def format_spread(
    home_team,
    away_team,
    spread
):

    if spread >= 0:

        return (
            f"{home_team} "
            f"-{abs(spread):.1f}"
        )

    return (
        f"{away_team} "
        f"-{abs(spread):.1f}"
    )


# ==================================================
# APP
# ==================================================

st.title("🏈 Brock's CFB Model")

page = st.sidebar.selectbox(
    "Navigation",
    [
        "Home",
        "Team Dashboard",
        "Power Rankings",
        "Game Predictor",
        "Team Schedule",
        "Expected Wins"
    ]
)

# ==================================================
# HOME
# ==================================================

if page == "Home":

    st.header("🏈 Brock's CFB Model")

    rating_df = ratings.sort_values(
        by="Rating",
        ascending=False
    )

    top_team = rating_df.iloc[0]["Team"]

    best_offense = ratings.loc[
        ratings["Off_SR"].idxmax()
    ]["Team"]

    best_defense = ratings.loc[
        ratings["Def_SR"].idxmin()
    ]["Team"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Teams Loaded",
            len(ratings)
        )

    with col2:

        st.metric(
            "Games Loaded",
            len(games)
        )

    with col3:

        st.metric(
            "#1 Rated Team",
            top_team
        )

    with col4:

        st.metric(
            "Best Offense",
            best_offense
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Best Defense",
            best_defense
        )

    with col2:

        st.metric(
            "Average Team Rating",
            f"{ratings['Rating'].mean():.3f}"
        )

    st.divider()

    st.subheader(
        "Top 25 Power Ratings"
    )

    chart_df = (
        rating_df.head(25)
        .sort_values("Rating")
    )

    fig = px.bar(
        chart_df,
        x="Rating",
        y="Team",
        orientation="h",
        title="Top 25 Power Ratings"
    )

    fig.update_layout(
        height=700
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    st.markdown("""
    ### Features

    🏈 Game Predictor

    📅 Team Schedule Projections

    📈 Expected Wins

    🏆 Power Rankings

    Built using Brock's custom college football rating system.
    """)

# ==================================================
# TEAM DASHBOARD
# ==================================================

elif page == "Team Dashboard":

    st.header("📊 Team Dashboard")

    team = st.selectbox(
        "Select Team",
        teams
    )

    team_row = ratings[
        ratings["Team"] == team
    ].iloc[0]

    team_games = games[
        (
            (games["homeTeam"] == team)
            |
            (games["awayTeam"] == team)
        )
    ]

    completed_games = team_games[
        team_games["completed"] == True
    ]

    current_wins = 0

    for _, game in completed_games.iterrows():

        if game["homeTeam"] == team:

            if game["homePoints"] > game["awayPoints"]:
                current_wins += 1

        else:

            if game["awayPoints"] > game["homePoints"]:
                current_wins += 1

    current_losses = (
        len(completed_games)
        - current_wins
    )

    future_games = team_games[
        team_games["completed"] == False
    ]

    expected_remaining_wins = 0

    for _, game in future_games.iterrows():

        home_team = game["homeTeam"]
        away_team = game["awayTeam"]

        spread, probability, _, _ = (
            predict_game(
                home_team,
                away_team
            )
        )

        if team == home_team:

            expected_remaining_wins += (
                probability
            )

        else:

            expected_remaining_wins += (
                1 - probability
            )

    projected_wins = (
        current_wins
        + expected_remaining_wins
    )

    projected_losses = (
        12 - projected_wins
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Record",
            f"{current_wins}-{current_losses}"
        )

    with col2:

        st.metric(
            "Rating",
            f"{team_row['Rating']:.3f}"
        )

    with col3:

        st.metric(
            "Projected Record",
            f"{projected_wins:.1f}-{projected_losses:.1f}"
        )

    with col4:

        st.metric(
            "Expected Remaining Wins",
            f"{expected_remaining_wins:.2f}"
        )

    st.divider()

    st.subheader("Team Metrics")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Off Success Rate",
            f"{team_row['Off_SR']:.3f}"
        )

        st.metric(
            "Off Explosiveness",
            f"{team_row['Off_Explosive']:.3f}"
        )

        st.metric(
            "Off Havoc Allowed",
            f"{team_row['Off_Havoc']:.3f}"
        )

    with col2:

        st.metric(
            "Def Success Rate",
            f"{team_row['Def_SR']:.3f}"
        )

        st.metric(
            "Def Explosiveness",
            f"{team_row['Def_Explosive']:.3f}"
        )

        st.metric(
            "Def Havoc",
            f"{team_row['Def_Havoc']:.3f}"
        )

    st.divider()

    st.subheader(
        "Remaining Schedule"
    )

    rows = []

    for _, game in future_games.iterrows():

        home_team = game["homeTeam"]
        away_team = game["awayTeam"]

        spread, probability, _, _ = (
            predict_game(
                home_team,
                away_team
            )
        )

        if team == home_team:

            rows.append({

                "Week":
                    game["week"],

                "Opponent":
                    away_team,

                "Location":
                    "vs",

                "Win %":
                    f"{probability:.1%}",

                "Spread":
                    format_spread(
                        home_team,
                        away_team,
                        spread
                    )
            })

        else:

            rows.append({

                "Week":
                    game["week"],

                "Opponent":
                    home_team,

                "Location":
                    "@",

                "Win %":
                    f"{(1-probability):.1%}",

                "Spread":
                    format_spread(
                        home_team,
                        away_team,
                        spread
                    )
            })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True
    )

# ==================================================
# POWER RANKINGS
# ==================================================

elif page == "Power Rankings":

    st.header("🏆 Power Rankings")

    ranking_df = ratings.sort_values(
        by="Rating",
        ascending=False
    ).reset_index(drop=True)

    ranking_df.insert(
        0,
        "Rank",
        range(
            1,
            len(ranking_df) + 1
        )
    )

    st.dataframe(
        ranking_df,
        use_container_width=True
    )

# ==================================================
# GAME PREDICTOR
# ==================================================

elif page == "Game Predictor":

    st.header("🏈 Game Predictor")

    home_team = st.selectbox(
        "Home Team",
        teams
    )

    away_team = st.selectbox(
        "Away Team",
        teams,
        index=1
    )

    if st.button("Predict Game"):

        spread, probability, rating_diff, matchup = (
            predict_game(
                home_team,
                away_team
            )
        )

        st.subheader("Prediction")

        st.success(
            f"Projected Spread: "
            f"{format_spread(home_team, away_team, spread)}"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                home_team,
                f"{probability:.1%}"
            )

            st.progress(
                float(probability)
            )

        with col2:

            st.metric(
                away_team,
                f"{(1-probability):.1%}"
            )

            st.progress(
                float(1-probability)
            )

        st.subheader(
            "Model Breakdown"
        )

        st.write(
            f"Rating Difference: "
            f"{rating_diff:.2f}"
        )

        st.write(
            f"Matchup Adjustment: "
            f"{matchup:.2f}"
        )

        st.write(
            f"Home Field Advantage: "
            f"{HOME_FIELD:.2f}"
        )

# ==================================================
# TEAM SCHEDULE
# ==================================================

elif page == "Team Schedule":

    st.header("📅 Team Schedule")

    team = st.selectbox(
        "Choose Team",
        teams
    )

    team_games = games[
        (
            (games["homeTeam"] == team)
            |
            (games["awayTeam"] == team)
        )
    ]

    completed_games = team_games[
        team_games["completed"] == True
    ]

    future_games = team_games[
        team_games["completed"] == False
    ]

    future_games = future_games.sort_values(
        by="week"
    )

    current_wins = 0

    for _, game in completed_games.iterrows():

        if game["homeTeam"] == team:

            if (
                game["homePoints"]
                >
                game["awayPoints"]
            ):
                current_wins += 1

        else:

            if (
                game["awayPoints"]
                >
                game["homePoints"]
            ):
                current_wins += 1

    current_losses = (
        len(completed_games)
        - current_wins
    )

    expected_wins = 0

    st.metric(
        "Current Record",
        f"{current_wins}-{current_losses}"
    )

    rows = []

    for _, game in future_games.iterrows():

        home_team = game["homeTeam"]
        away_team = game["awayTeam"]

        if (
            home_team not in team_lookup
            or away_team not in team_lookup
        ):
            continue

        spread, probability, _, _ = (
            predict_game(
                home_team,
                away_team
            )
        )

        if team == home_team:

            team_win_prob = probability

            rows.append({

                "Week":
                    game["week"],

                "Opponent":
                    away_team,

                "Location":
                    "vs",

                "Win %":
                    f"{team_win_prob:.1%}",

                "Spread":
                    format_spread(
                        home_team,
                        away_team,
                        spread
                    )
            })

        else:

            team_win_prob = (
                1 - probability
            )

            rows.append({

                "Week":
                    game["week"],

                "Opponent":
                    home_team,

                "Location":
                    "@",

                "Win %":
                    f"{team_win_prob:.1%}",

                "Spread":
                    format_spread(
                        home_team,
                        away_team,
                        spread
                    )
            })

        expected_wins += team_win_prob

    schedule_df = pd.DataFrame(rows)

    st.dataframe(
        schedule_df,
        use_container_width=True
    )

    projected_wins = (
        current_wins
        + expected_wins
    )

    projected_losses = (
        12 - projected_wins
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Expected Remaining Wins",
            f"{expected_wins:.2f}"
        )

    with col2:

        st.metric(
            "Projected Record",
            f"{projected_wins:.1f}-{projected_losses:.1f}"
        )

# ==================================================
# EXPECTED WINS
# ==================================================

elif page == "Expected Wins":

    st.header("📈 Expected Wins")

    results = []

    def home_win_probability(
        home_team,
        away_team
    ):

        team_a = team_lookup[home_team]
        team_b = team_lookup[away_team]

        rating_diff = (
            team_a["Rating"]
            - team_b["Rating"]
        ) * RATING_SCALE

        matchup = matchup_adjustment(
            team_a,
            team_b
        )

        spread = (
            rating_diff
            + matchup
            + HOME_FIELD
        )

        return (
            1 /
            (1 + math.exp(-spread / 6))
        )

    for team in ratings["Team"]:

        team_games = games[
            (games["homeTeam"] == team)
            |
            (games["awayTeam"] == team)
        ]

        current_wins = 0
        current_losses = 0
        expected_remaining_wins = 0

        for _, game in team_games.iterrows():

            home_team = game["homeTeam"]
            away_team = game["awayTeam"]

            if game["completed"]:

                if home_team == team:

                    if game["homePoints"] > game["awayPoints"]:
                        current_wins += 1
                    else:
                        current_losses += 1

                else:

                    if game["awayPoints"] > game["homePoints"]:
                        current_wins += 1
                    else:
                        current_losses += 1

            else:

                if (
                    home_team not in team_lookup
                    or away_team not in team_lookup
                ):
                    continue

                home_prob = home_win_probability(
                    home_team,
                    away_team
                )

                if team == home_team:

                    expected_remaining_wins += home_prob

                else:

                    expected_remaining_wins += (
                        1 - home_prob
                    )

        projected_wins = (
            current_wins
            + expected_remaining_wins
        )

        projected_losses = (
            current_losses
            + (
                len(
                    team_games[
                        team_games["completed"] == False
                    ]
                )
                - expected_remaining_wins
            )
        )

        results.append({

            "Team":
                team,

            "Current Wins":
                current_wins,

            "Current Losses":
                current_losses,

            "Expected Remaining Wins":
                round(
                    expected_remaining_wins,
                    2
                ),

            "Projected Wins":
                round(
                    projected_wins,
                    2
                ),

            "Projected Losses":
                round(
                    projected_losses,
                    2
                )
        })

    expected_df = pd.DataFrame(
        results
    )

    expected_df = expected_df.sort_values(
        by="Projected Wins",
        ascending=False
    )

    expected_df = expected_df.reset_index(
        drop=True
    )

    expected_df.insert(
        0,
        "Rank",
        range(
            1,
            len(expected_df) + 1
        )
    )

    st.subheader(
        "Top 25 Projected Teams"
    )

    st.dataframe(
        expected_df.head(25),
        use_container_width=True
    )

    st.divider()

    st.subheader(
        "All Teams"
    )

    st.dataframe(
        expected_df,
        use_container_width=True
    )