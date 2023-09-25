import pandas as pd

def update_league_table(*results):
    league_table = pd.read_csv('data/league_table.csv', index_col='Team')
    
    # Process each match result
    for result in results:
        if len(result) != 2:
            print("Each result must have exactly two teams.")
            continue
            
        # Extract team names and goals
        (team1, goals1), (team2, goals2) = result.items()
        
        if team1 not in league_table.index or team2 not in league_table.index:
            print(f"One or both teams {team1} and {team2} not found in league table.")
            continue
        
        # Update goals for and against
        league_table.at[team1, 'F'] += goals1
        league_table.at[team2, 'A'] += goals1
        league_table.at[team2, 'F'] += goals2
        league_table.at[team1, 'A'] += goals2
        
        # Update matches played
        league_table.at[team1, 'P'] += 1
        league_table.at[team2, 'P'] += 1
        
        # Update wins, losses, draws, and points
        if goals1 > goals2:
            league_table.at[team1, 'W'] += 1
            league_table.at[team1, 'Pts'] += 3
            league_table.at[team2, 'L'] += 1
        elif goals1 < goals2:
            league_table.at[team2, 'W'] += 1
            league_table.at[team2, 'Pts'] += 3
            league_table.at[team1, 'L'] += 1
        else:  # Draw
            league_table.at[team1, 'D'] += 1
            league_table.at[team2, 'D'] += 1
            league_table.at[team1, 'Pts'] += 1
            league_table.at[team2, 'Pts'] += 1
        
        # Update goal difference
        league_table.at[team1, 'GD'] = league_table.at[team1, 'F'] - league_table.at[team1, 'A']
        league_table.at[team2, 'GD'] = league_table.at[team2, 'F'] - league_table.at[team2, 'A']
    
    # Sort the league table by Pts, GD, and F, and save to CSV
    league_table = league_table.sort_values(by=['Pts', 'GD', 'F'], ascending=[False, False, False])
    league_table.to_csv('data/league_table.csv')