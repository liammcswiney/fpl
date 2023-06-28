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

    return 'Players locked in!'