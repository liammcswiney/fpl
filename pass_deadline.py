import pandas as pd

def pass_deadline(gameweek):

    team_lineups = pd.read_csv('data/team_data.csv')
    leaderboard = pd.read_csv('data/team_leaderboard.csv')
    team_lineups.to_csv('data/gw_team_data.csv', index=False)

    transfer_data = pd.read_csv('data/gw_transfers.csv')

    if f'Gameweek {gameweek}' in leaderboard.keys().tolist():
        return 'Gameweek already entered!'

    team_gw_lineup = {}
    for row in team_lineups.values:
        played = []
        for i in row[1:]:
            played.append(i)
        team_gw_lineup[row[0]] = played

    gw_scores = {}
    for i in team_gw_lineup.keys():
        gw_score = 0
        gw_scores[i] = gw_score


    new_total = {}
    for i in transfer_data.values:
        team_name = i[0]
        total_score = leaderboard.loc[leaderboard['Team Name'] == team_name, 'Total Score'].values[0]
        gw_costs = transfer_data.loc[transfer_data['Team Name'] == team_name].iloc[:, -1].values[0]
        total_score += gw_costs
        new_total[team_name] = {'Team Name': team_name, 'Total Score': total_score}


    df = pd.DataFrame.from_dict(new_total, orient='index')
    df = df.reset_index(drop=True)

    leaderboard = leaderboard.drop(columns = 'Total Score')
    leaderboard = pd.merge(leaderboard, df, on='Team Name', how='outer')

    chip_data = pd.read_csv('data/team_chips.csv')
    limitless = pd.read_csv('data/limitless.csv')
    team_data = pd.read_csv('data/team_data.csv')

    for index, row in chip_data.iterrows():
        team_name = row[0] 

        if row[2] == 1:      #if limitless == 1
            limitless_row = limitless[limitless['Team Name'] == team_name].iloc[0]
            team_data_index = team_data[team_data['Team Name'] == team_name].index[0]
            team_data.loc[team_data_index] = limitless_row
            
    team_data.to_csv('data/team_data.csv', index=False)

    gw_chip_data = pd.read_csv('data/gw_team_chips.csv')

    rows_list = []

    for index, row in chip_data.iterrows():
        team_name = row[0] 
        chip_used = 'none'

        for col in chip_data.columns[1:]:
            if row[col] == 1:
                chip_used = col 
                break
        
        rows_list.append({'Team Name': team_name, f'Gameweek {gameweek} Chip Used': chip_used})

    chip_df = pd.DataFrame(rows_list)
    gw_chip_data = pd.merge(gw_chip_data, chip_df, on='Team Name')

    gw_chip_data.to_csv('data/gw_team_chips.csv', index=False)

    chip_data = pd.read_csv('data/team_chips.csv')
    condition = (chip_data[['Wildcard', 'Triple Captain', 'Bench Boost', 'Limitless']] == 1).any(axis=1)
    chip_data.loc[condition, ['Wildcard', 'Triple Captain', 'Bench Boost', 'Limitless']] = chip_data.loc[condition, ['Wildcard', 'Triple Captain', 'Bench Boost', 'Limitless']].replace(1, 2)
    chip_data.to_csv('data/team_chips.csv', index=False)

    score_df = pd.DataFrame(gw_scores.items(), columns=['Team Name', f'Gameweek {gameweek}'])
    lineup_df = pd.DataFrame(team_gw_lineup.items(), columns=['Team Name', f'Gameweek {gameweek} Team'])

    leaderboard = pd.merge(leaderboard, score_df, on='Team Name', how='outer')
    leaderboard = pd.merge(leaderboard, lineup_df, on='Team Name', how='outer')
    leaderboard = leaderboard[['Team Name', 'Total Score'] + [col for col in leaderboard.columns if col not in ['Team Name', 'Total Score']]]

    leaderboard.to_csv('data/team_leaderboard.csv', index=False)

    transfer_data = pd.read_csv('data/gw_transfers.csv')
    for index, row in transfer_data.iterrows():
        if row[1] < 2:
            transfer_data.at[index, transfer_data.columns[1]] += 1

    transfer_data = transfer_data.assign(**{f'Gameweek {gameweek + 1}': 0, f'Gameweek {gameweek + 1} Cost': 0})
    transfer_data.to_csv('data/gw_transfers.csv', index=False)

    transfer_data_temp = pd.read_csv('data/gw_transfers.csv')
    transfer_data_temp = transfer_data_temp.assign(**{f'Gameweek {gameweek + 1}': 0, f'Gameweek {gameweek + 1} Cost': 0})
    transfer_data_temp.to_csv('data/gw_transfers_temp.csv', index=False)

    player_score = pd.read_csv('data/player_score.csv')
    player_score = player_score.assign(**{f'Gameweek {gameweek}': 0})
    player_score.to_csv('data/player_score.csv', index=False)


    results_data = pd.read_csv('data/results.csv')
    new_results = {
        'Gameweek': gameweek,
        'Score': '-',
        'Team': [],
        'Goal Scorers': [],
        'Assists': [],
        'On Bench': {},
        'Saves': '-',
        'Penalty Saved': [],
        'Penalty Missed': [],
        'Yellow Cards': [],
        'Red Cards': [],
        'Own Goals': [],
        '3 Bonus': '-',
        '2 Bonus': '-',
        '1 Bonus': '-'
    }

    new_results_data = pd.DataFrame([new_results])
    results_data = pd.concat([results_data, new_results_data], ignore_index=True)
    results_data.to_csv('data/results.csv', index=False)


    player_scores_data = pd.read_csv('data/player_score.csv')
    players_df = player_scores_data[['Player', 'Position']]

    players_df["Minutes"] = 0
    players_df["Goals"] = 0
    players_df["Assists"] = 0
    players_df["Bonus"] = 0
    players_df["Clean Sheet"] = 0
    players_df["Conceded"] = 0
    players_df["Saves"] = 0
    players_df["Penalty Saved"] = 0
    players_df["Penalty Missed"] = 0
    players_df["Yellow Cards"] = 0
    players_df["Red Cards"] = 0
    players_df["Own Goals"] = 0

    players_df.to_csv(f"data/{gameweek}_player_stats.csv", index=False)

    return 'Players locked in!'