import pandas as pd
import numpy as np

def add_gameweek_score(gameweek, fixture, score, team, goal_scorers, assists, bonus_3, bonus_2, bonus_1):

    results_data = pd.read_csv('data/results.csv')
    player_scores_data = pd.read_csv('data/player_score.csv')
    player_scores_data = player_scores_data.drop(columns = f'Gameweek {gameweek}')
    player_stats = pd.read_csv('data/player_database.csv')
    player_goals = pd.read_csv('data/goals.csv')
    player_assists = pd.read_csv('data/assists.csv')

    if gameweek in results_data['Gameweek'].tolist():
        return 'Gameweek already entered!'

    new_results = {
        'Gameweek': gameweek,
        'Fixture': fixture,
        'Score': score,
        'Team': team,
        'Goal Scorers': goal_scorers,
        'Assists': assists,
        '3 Bonus': bonus_3,
        '2 Bonus': bonus_2,
        '1 Bonus': bonus_1,
    }
    new_results_data = pd.DataFrame([new_results])
    results_data = pd.concat([results_data, new_results_data], ignore_index=True)

    gw_scores = {}
    goals_scored = int(score.split('-')[0])
    goals_conceded = int(score.split('-')[1])

    new_player_total_dict = {}
    new_player_form_dict = {}
    new_player_goals_dict = {}
    new_player_assists_dict = {}
    new_player_matches_dict = {}

    concede_lost = (goals_conceded // 2) * -1

    for player in player_scores_data['Player']:
        player_score = 0
        gw_goals = 0
        gw_assists = 0
        
        if player_scores_data.loc[player_scores_data['Player'] == player, 'Position'].item() in ['GK', 'DEF']:
            if player in team:
                if goals_conceded == 0:
                    player_score += 4
                player_score += concede_lost
            

        if player_scores_data.loc[player_scores_data['Player'] == player, 'Position'].item() == 'MID':
            if player in team:
                if goals_conceded == 0:
                    player_score += 1

        if player in team:
            player_score += 2
            gw_played = 1
                
        for k in goal_scorers:
            if player == k:
                if player_scores_data.loc[player_scores_data['Player'] == player, 'Position'].item() == 'GK':
                    player_score += 6
                elif player_scores_data.loc[player_scores_data['Player'] == player, 'Position'].item() == 'DEF':
                    player_score += 6
                elif player_scores_data.loc[player_scores_data['Player'] == player, 'Position'].item() == 'MID':
                    player_score += 5
                elif player_scores_data.loc[player_scores_data['Player'] == player, 'Position'].item() == 'FWD':
                    player_score += 4
                gw_goals += 1
                    
        for k in assists:
            if player == k:
                player_score += 3
                gw_assists += 1
                
        if player == bonus_3:
            player_score += 3
        if player == bonus_2:
            player_score += 2
        if player == bonus_1:
            player_score += 1
            
        gw_scores[player] = player_score

        new_player_total = player_stats.loc[player_stats['Player'] == player, 'Total Points'].item() + player_score
        new_player_total_dict[player] = new_player_total

        new_player_goals = player_goals.loc[player_goals['Player'] == player, 'Goals'].item() + gw_goals
        new_player_goals_dict[player] = new_player_goals

        new_player_matches = player_goals.loc[player_goals['Player'] == player, 'Matches'].item() + gw_played
        new_player_matches_dict[player] = new_player_matches

        new_player_assists = player_assists.loc[player_assists['Player'] == player, 'Assists'].item() + gw_assists
        new_player_assists_dict[player] = new_player_assists
    
    gw_column_name = f"Gameweek {gameweek}"
    
    gw_player_list = []
    for key in gw_scores.keys():
        gw_player_list.append(key)

    gw_score_list = []
    for value in gw_scores.values():
        gw_score_list.append(value)

    gw_data = {'Player': gw_player_list, gw_column_name: gw_score_list}
    gw_df = pd.DataFrame(gw_data)

    player_scores_data = pd.merge(player_scores_data, gw_df, on='Player', how='outer')

    for player in player_scores_data['Player']:
        form = 0
        form_matches = 0
        for i in player_scores_data.columns[-3:]:
            if isinstance(player_scores_data.loc[player_scores_data['Player'] == player, i].values[0], np.int64):
                form_matches += 1
                form += player_scores_data.loc[player_scores_data['Player'] == player, i].values[0]
        new_player_form_dict[player] = round(form/form_matches, 1)

    player_stats.drop('Form', axis=1, inplace=True)
    player_stats['Form'] = player_stats['Player'].map(new_player_form_dict)

    player_stats.drop('Total Points', axis=1, inplace=True)
    player_stats['Total Points'] = player_stats['Player'].map(new_player_total_dict)

    player_goals.drop('Matches', axis=1, inplace=True)
    player_goals.drop('Goals', axis=1, inplace=True)
    player_goals['Matches'] = player_goals['Player'].map(new_player_matches_dict)
    player_goals['Goals'] = player_goals['Player'].map(new_player_goals_dict)

    player_assists.drop('Matches', axis=1, inplace=True)
    player_assists.drop('Assists', axis=1, inplace=True)
    player_assists['Matches'] = player_assists['Player'].map(new_player_matches_dict)
    player_assists['Assists'] = player_assists['Player'].map(new_player_assists_dict)

    results_data.to_csv('data/results.csv', index=False)
    player_scores_data.to_csv('data/player_score.csv', index=False)
    player_stats.to_csv('data/player_database.csv', index=False)
    player_goals.to_csv('data/goals.csv', index=False)
    player_assists.to_csv('data/assists.csv', index=False)

    player_scores = pd.read_csv('data/player_score.csv')
    team_lineups = pd.read_csv('data/gw_team_data.csv')
    leaderboard = pd.read_csv('data/team_leaderboard.csv')

    team_gw_lineup = {}
    for row in team_lineups.values:
        played = []
        for i in row[1:]:
            if i != row[8]:                            #in future import team from team_laederboard, and compare it against played input, and implement auto subs
                played.append(i)
        team_gw_lineup[row[0]] = played

    team_gw_lineup_lead = {}
    for row in team_lineups.values:
        played = []
        for i in row[1:]:                           #in future import team from team_laederboard, and compare it against played input, and implement auto subs
            played.append(i)
        team_gw_lineup_lead[row[0]] = played

    gw_scores = {}
    new_total = {}
    for i, j in team_gw_lineup.items():
        gw_score = 0
        total_score = leaderboard.loc[leaderboard['Team Name'] == i, 'Total Score'].values[0]
        for k in j:
            gw_score += player_scores.loc[player_scores['Player'] == k, f'Gameweek {gameweek}'].values[0]
        gw_scores[i] = gw_score
        total_score += gw_score
        new_total[i] = total_score



    score_df = pd.DataFrame(gw_scores.items(), columns=['Team Name', f'Gameweek {gameweek}'])
    lineup_df_lead = pd.DataFrame(team_gw_lineup_lead.items(), columns=['Team Name', f'Gameweek {gameweek} Team'])
    leaderboard = leaderboard.drop(columns = 'Total Score')
    new_leaderboard = pd.DataFrame(new_total.items(), columns=['Team Name', 'Total Score'])
    leaderboard= pd.merge(leaderboard, new_leaderboard, on='Team Name', how='outer')

    leaderboard = leaderboard.drop(columns = [f'Gameweek {gameweek}', f'Gameweek {gameweek} Team'])

    leaderboard = pd.merge(leaderboard, score_df, on='Team Name', how='outer')
    leaderboard = pd.merge(leaderboard, lineup_df_lead, on='Team Name', how='outer')
    leaderboard = leaderboard[['Team Name', 'Total Score'] + [col for col in leaderboard.columns if col not in ['Team Name', 'Total Score']]]

    leaderboard.to_csv('data/team_leaderboard.csv', index=False)


    fixtures_data = pd.read_csv('data/fixtures.csv')
    fixtures_data.loc[fixtures_data['Gameweek'] == gameweek, 'Score'] = score
    if goals_scored > goals_conceded:
        result = 'win'
    elif goals_scored < goals_conceded:
        result = 'loss'
    else:
        result = 'draw'
    fixtures_data.loc[fixtures_data['Gameweek'] == gameweek, 'Result'] = result
    fixtures_data.to_csv('data/fixtures.csv', index=False)

    return 'Scores Added!'
