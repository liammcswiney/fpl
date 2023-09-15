from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
# import traceback
import csv
# import urllib.parse
import json
import pass_deadline
import add_results
import add_injury

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    return app

app = create_app()

app.config['ENV'] = 'production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///players.db'

db = SQLAlchemy(app)

#############################################################################################################################

@app.route('/')
def index():
    return render_template('index.html')

#############################################################################################################################

@app.route('/create_team', methods=['GET', 'POST'])
def create_team():
    if request.method == 'POST':
        team_name = request.form['team_name']
        with open('data/team_data.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row and row[0] == team_name:
                    error_message = f"The team '{team_name}' already exists. Please enter a different team name."
                    return render_template('create_team.html', error_message=error_message)

        player_columns = ['0'] * 7

        with open('data/team_data.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([team_name] + player_columns)

        with open('data/team_leaderboard.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Read the header row to extract column names
            columns = header[-2].split()[-1]
            team_columns = [['No Player', 'No Player', 'No Player', 'No Player', 'No Player', 'No Player', 'No Player', 'No Player']]
            new_row = [team_name] + [0]
            
            if columns != 'Name':
                for i in range(1, int(columns) + 1):
                    new_row = new_row + ['-'] + team_columns

        with open('data/team_leaderboard.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(new_row)


        with open('data/gw_transfers.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            first_row = next(reader)
            num_columns = len(first_row)

        row_values = [team_name] + [0] * (num_columns - 1)

        with open('data/gw_transfers.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(row_values)


        with open('data/gw_transfers_temp.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            first_row = next(reader)
            num_columns = len(first_row)

        row_values = [team_name] + [0] * (num_columns - 1)

        with open('data/gw_transfers_temp.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(row_values)

        return redirect(url_for('team_management', team_name=team_name))

    return render_template('create_team.html')


#############################################################################################################################

@app.route('/load_team', methods=['GET', 'POST'])
def load_team():
    if request.method == 'POST':
        team_name = request.form['team_name']

        with open('data/team_data.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row and row[0] == team_name:
                    return redirect(url_for('team_management', team_name=team_name))
        error_message = f"The team '{team_name}' does not exist."
        return render_template('load_team.html', error_message=error_message)
    return render_template('load_team.html')


#############################################################################################################################

@app.route('/team_management/<team_name>', methods=['GET', 'POST'])
def team_management(team_name):

    leaderboard_data = pd.read_csv('data/team_leaderboard.csv')

    gw_info = leaderboard_data.loc[leaderboard_data['Team Name'] == team_name]
    gw_info = gw_info.iloc[:, :-1]
    index_tm = gw_info.iloc[:, :-1].index[0]

    if gw_info.iloc[:, -1][index_tm] == '-':
        max_gw = int(gw_info.columns[-1][-1])
    else:
        max_gw = 0


    gw_info = gw_info.to_dict(orient='records')

    if leaderboard_data.columns[-2] == 'Team Name':
        avg_score = '-'
        highest_score = '-'
    else:
        filtered_scores = leaderboard_data[leaderboard_data.iloc[:, -2] != '-']
        filtered_scores[leaderboard_data.columns[-2]] = pd.to_numeric(filtered_scores[leaderboard_data.columns[-2]])
        avg_score = int(filtered_scores[leaderboard_data.columns[-2]].mean())
        highest_score = int(filtered_scores[leaderboard_data.columns[-2]].max())

    if request.method == 'POST':
        # Check if the team is already built
        is_team_built = check_team_built(team_name)  # Implement the logic to check if the team is built

        if is_team_built:    

            return redirect(url_for('gameweek_points', team_name=team_name))

        else:
            # Team is not built, redirect to the build team page
            return redirect(url_for('build_team', team_name=team_name))
        
    else:
        # Render the team management page
        is_team_built = check_team_built(team_name)  # Implement the logic to check if the team is built
        return render_template('team_management.html', team_name=team_name, is_team_built=is_team_built, gw_info=gw_info
                               , highest_score=highest_score, avg_score=avg_score
                               , max_gw=max_gw)


#############################################################################################################################

@app.route('/handle_team_management/<team_name>', methods=['POST'])
def handle_team_management(team_name):
    # Handle form submissions or perform any necessary actions
    return redirect(url_for('team_management', team_name=team_name))


#############################################################################################################################

def check_team_built(team_name):
    with open('data/team_data.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Team Name'] == team_name:
                # Check if any player columns are empty or have a value of 0
                players = [row[f'Player {i}'] for i in range(1, 7)]
                if '0' in players or '' in players:
                    return False
                else:
                    return True
    return False  # Team not found in the CSV file


#############################################################################################################################

@app.route('/build_team/<team_name>', methods=['GET', 'POST'])
def build_team(team_name):
    team_data = {}
    player_databases = {}

    injury_data = pd.read_csv('data/injuries.csv')
    injury_data = injury_data.to_dict(orient='records')

    # Read team data from CSV file
    with open('data/team_data.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Team Name'] == team_name:
                team_data = row
                break

    reader = pd.read_csv('data/player_database.csv')
    for i in reader['Player']:
        player_databases[i] = reader[reader['Player'] == i]['Price'].values[0]

    player_index = int(request.args.get('playerIndex', default=1))

    if not team_data:
        # Team not found in CSV file
        return render_template('team_not_found.html', team_name=team_name)

    if request.method == 'POST':
        player1 = request.form.get('player1')
        player2 = request.form.get('player2', 'player2')  # Set default value
        player3 = request.form.get('player3')
        player4 = request.form.get('player4')
        player5 = request.form.get('player5')
        player6 = request.form.get('player6')

        # Check if all players have been selected
        if all([player1, player2, player3, player4, player5, player6]):

            # Convert the team_data values to the appropriate types
            team_data = {
                'Team Name': team_data['Team Name'],
                'Player 1': player1,
                'Player 2': player2,
                'Player 3': player3,
                'Player 4': player4,
                'Player 5': player5,
                'Player 6': player6,
                'Bench': 'player2',  # Set default value
                'Bench Position': 'DEF',  # Set default value
            }

            # Update the team_data.csv file with new player data
            with open('data/team_data.csv', 'w', newline='') as csvfile:
                fieldnames = team_data.keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(team_data)

            # Redirect to the team management page
            return redirect(url_for('team_management', team_name=team_name))

        else:
            # Handle the case when not all players have been selected
            error_message = "Please select all players before submitting."
            return render_template('build_team.html', team_name=team_name, error_message=error_message,
                                   team_data=team_data, player_index=player_index
                                   , player_databases=player_databases, injury_data=injury_data)

    else:
        # Render the build team page with a form to select players
        return render_template('build_team.html', team_name=team_name, team_data=team_data,
                               player_index=player_index, player_databases=player_databases, injury_data=injury_data)



#############################################################################################################################

import csv

@app.route('/init_build/<team_name>', methods=['GET', 'POST'])
def init_build(team_name):
    with open('data/team_data.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    for row in reader.values:
        if row[0] == team_name:
            reader.loc[reader['Team Name'] == team_name, 'Bench'] = reader.loc[reader['Team Name'] == team_name, 'Player 2'].values[0]
            reader.loc[reader['Team Name'] == team_name, 'Captain'] = reader.loc[reader['Team Name'] == team_name, 'Player 6'].values[0]

    reader.to_csv('data/team_data.csv', index=False)
    reader.to_csv('data/team_data_temp.csv', index=False)

    return redirect(url_for('team_management', team_name=team_name))




#############################################################################################################################

@app.route('/load_transfers/<team_name>', methods=['GET', 'POST'])
def load_transfers(team_name):
    
    team_data = {}
    player_databases = {}

    injury_data = pd.read_csv('data/injuries.csv')
    injury_data = injury_data.to_dict(orient='records')

    with open('data/team_data.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    with open('data/team_data_temp.csv', 'r') as csvfile:
        temp = pd.read_csv(csvfile)

    reader = reader.loc[reader['Team Name'] == team_name]
    temp.loc[temp['Team Name'] == team_name] = reader.loc[reader['Team Name'] == team_name].values
    temp.to_csv('data/team_data_temp.csv', index=False)


    with open('data/gw_transfers.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    with open('data/gw_transfers_temp.csv', 'r') as csvfile:
        temp = pd.read_csv(csvfile)

    temp = temp.loc[temp['Team Name'] == team_name]
    temp.loc[temp['Team Name'] == team_name, 'Free Transfers'] = reader.loc[reader['Team Name'] == team_name, 'Free Transfers'].values
    temp.loc[temp['Team Name'] == team_name, temp.columns[-2]] = 0 
    temp.loc[temp['Team Name'] == team_name, temp.columns[-1]] = 0

    reader.loc[reader['Team Name'] == team_name] = temp.loc[temp['Team Name'] == team_name].values
    reader.to_csv('data/gw_transfers_temp.csv', index=False)
    
    with open('data/gw_transfers_temp.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Team Name'] == team_name:
                transfer_data = row
                break


    # Read team data from CSV file
    with open('data/team_data_temp.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Team Name'] == team_name:
                team_data = row
                break


    reader = pd.read_csv('data/player_database.csv')
    for i in reader['Player']:
        player_databases[i] = reader[reader['Player'] == i]['Price'].values[0]

    player_index = int(request.args.get('playerIndex', default=1))

    if not team_data:
        # Team not found in CSV file
        return render_template('team_not_found.html', team_name=team_name)
    
    return render_template('transfers.html', team_name=team_name, team_data=team_data, player_index=player_index
                           , player_databases=player_databases, transfer_data = transfer_data, injury_data=injury_data)

#############################################################################################################################


@app.route('/transfers/<team_name>', methods=['GET', 'POST'])
def transfers(team_name):
    team_data = {}
    player_databases = {}

    injury_data = pd.read_csv('data/injuries.csv')
    injury_data = injury_data.to_dict(orient='records')

    with open('data/team_data_temp.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Team Name'] == team_name:
                team_data = row
                break

    with open('data/gw_transfers_temp.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Team Name'] == team_name:
                transfer_data = row
                break

    reader = pd.read_csv('data/player_database.csv')
    for i in reader['Player']:
        player_databases[i] = reader[reader['Player'] == i]['Price'].values[0]

    player_index = int(request.args.get('playerIndex', default=1))

    if not team_data:
        # Team not found in CSV file
        return render_template('team_not_found.html', team_name=team_name)

    if request.method == 'POST':
        player1 = request.form.get('player1')
        player2 = request.form.get('player2')
        player3 = request.form.get('player3')
        player4 = request.form.get('player4')
        player5 = request.form.get('player5')
        player6 = request.form.get('player6')

        # Check if all players have been selected
        if all([player1, player2, player3, player4, player5, player6]):
            # Update the team_data dictionary with new player data
            team_data['Player 1'] = player1
            team_data['Player 2'] = player2
            team_data['Player 3'] = player3
            team_data['Player 4'] = player4
            team_data['Player 5'] = player5
            team_data['Player 6'] = player6
            

            # Update the team_data.csv file with new player data
            with open('data/team_data_temp.csv', 'w', newline='') as csvfile:
                fieldnames = team_data.keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(team_data)

            # Redirect to the team management page
            return redirect(url_for('team_management', team_name=team_name))
        else:
            # Handle the case when not all players have been selected
            error_message = "Please select all players before submitting."
            return render_template('transfers.html', team_name=team_name, error_message=error_message
                                   , team_data=team_data, player_index=player_index, player_databases=player_databases
                                   , transfer_data=transfer_data, injury_data=injury_data)

    else:
        # Render the build team page with a form to select players
        return render_template('transfers.html', team_name=team_name, team_data=team_data
                               , player_index=player_index, player_databases=player_databases
                               , transfer_data=transfer_data, injury_data=injury_data)


#############################################################################################################################


@app.route('/pick_team/<team_name>', methods=['GET', 'POST'])
def pick_team(team_name):
    team_data = {}
    player_databases = {}
    player_data = read_csv('data/player_database.csv')

    leaderboard_data = pd.read_csv('data/team_leaderboard.csv')
    gw_info = leaderboard_data.iloc[:, :-1]
    next_gw = gw_info.columns[-1].split(' ')[1]
    if next_gw != 'Name':
        next_gw_int = int(next_gw) + 1
        next_gw = 'Gameweek ' + str(next_gw_int)
    else:
        next_gw = 'Gameweek 1'
        next_gw_int = 1

    # Read team data from CSV file
    with open('data/team_data.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Team Name'] == team_name:
                team_data = row
                break

    reader = pd.read_csv('data/player_database.csv')
    for i in reader['Player']:
        player_databases[i] = reader[reader['Player'] == i]['Price'].values[0]

    fixtures_data = pd.read_csv('data/fixtures.csv')

    injury_data = pd.read_csv('data/injuries.csv')
    injury_data = injury_data.to_dict(orient='records')

    player_index = int(request.args.get('playerIndex', default=1))

    if not team_data:
        # Team not found in CSV file
        return render_template('team_not_found.html', team_name=team_name)

    if request.method == 'POST':
        player1 = request.form.get('player1')
        player2 = request.form.get('player2')
        player3 = request.form.get('player3')
        player4 = request.form.get('player4')
        player5 = request.form.get('player5')
        player6 = request.form.get('player6')

        # Check if all players have been selected
        if all([player1, player2, player3, player4, player5, player6]):
            # Update the team_data dictionary with new player data
            team_data['Player 1'] = player1
            team_data['Player 2'] = player2
            team_data['Player 3'] = player3
            team_data['Player 4'] = player4
            team_data['Player 5'] = player5
            team_data['Player 6'] = player6

            # Redirect to the team management page
            return redirect(url_for('team_management', team_name=team_name))
        else:
            # Handle the case when not all players have been selected
            error_message = "Please select all players before submitting."
            return render_template('pick_team.html', team_name=team_name, error_message=error_message, team_data=team_data
                                   , player_index=player_index, player_databases=player_databases, next_gw_int=next_gw_int
                                   , player_data=player_data, next_gw=next_gw, fixtures_data=fixtures_data, injury_data=injury_data)

    else:
        # Render the build team page with a form to select players
        return render_template('pick_team.html', team_name=team_name, team_data=team_data, player_index=player_index
                               , player_databases=player_databases, fixtures_data=fixtures_data
                               , player_data=player_data, next_gw=next_gw
                               , next_gw_int=next_gw_int, injury_data=injury_data)


#############################################################################################################################

@app.route('/update_team_data/<team_name>/<player_name>', methods=['POST'])
def update_team_data(team_name, player_name):
    # Read the existing team_data from the CSV file
    with open('data/team_data.csv', 'r') as csvfile:
            reader = pd.read_csv(csvfile)

    for row in reader.values:
        if row[0] == team_name:
            if reader.loc[reader['Team Name'] == team_name, 'Captain'].values == player_name:
                reader.loc[reader['Team Name'] == team_name, 'Captain'] = reader.loc[reader['Team Name'] == team_name, 'Bench'].values

    for row in reader.values:
        if row[0] == team_name:
            reader.loc[reader['Team Name'] == team_name, 'Bench'] = player_name

    reader.to_csv('data/team_data.csv', index=False)

    return redirect(url_for('pick_team', team_name=team_name))


#############################################################################################################################

@app.route('/update_captain/<team_name>/<player_name>', methods=['POST'])
def update_captain(team_name, player_name):
    # Read the existing team_data from the CSV file
    with open('data/team_data.csv', 'r') as csvfile:
            reader = pd.read_csv(csvfile)

    for row in reader.values:
        if row[0] == team_name:
            reader.loc[reader['Team Name'] == team_name, 'Captain'] = player_name

    reader.to_csv('data/team_data.csv', index=False)

    return redirect(url_for('pick_team', team_name=team_name))

#############################################################################################################################

@app.route('/save_transfers/<team_name>', methods=['GET', 'POST'])
def save_transfers(team_name):
    with open('data/team_data_temp.csv', 'r') as csvfile:
        temp = pd.read_csv(csvfile)

    with open('data/team_data.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    for row in temp.values:
        if row[0] == team_name:
            if row[7] not in [row[1], row[2], row[3], row[4], row[5]]:
                temp.loc[temp['Team Name'] == team_name, 'Captain'] = temp.loc[temp['Team Name'] == team_name, 'Player 1'].values

    for row in temp.values:
        if row[0] == team_name:
            if row[8] not in [row[1], row[2], row[3], row[4], row[5]]:
                temp.loc[temp['Team Name'] == team_name, 'Bench'] = temp.loc[temp['Team Name'] == team_name, 'Player 2'].values


    temp = temp.loc[temp['Team Name'] == team_name]
    reader.loc[reader['Team Name'] == team_name] = temp.loc[temp['Team Name'] == team_name].values
    reader.to_csv('data/team_data.csv', index=False)


    with open('data/gw_transfers_temp.csv', 'r') as csvfile:
        temp = pd.read_csv(csvfile)

    with open('data/gw_transfers.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)



    temp = temp.loc[temp['Team Name'] == team_name]

    reader.loc[reader['Team Name'] == team_name, 'Free Transfers'] = temp.loc[temp['Team Name'] == team_name, 'Free Transfers'].values

    reader.loc[reader['Team Name'] == team_name, reader.columns[-2]] = int(reader.loc[reader['Team Name'] == team_name, reader.columns[-2]])
    temp.loc[reader['Team Name'] == team_name, reader.columns[-2]] = int(temp.loc[reader['Team Name'] == team_name, reader.columns[-2]])

    reader.loc[reader['Team Name'] == team_name, reader.columns[-2]] += temp.loc[reader['Team Name'] == team_name, reader.columns[-2]] 
    reader.loc[reader['Team Name'] == team_name, reader.columns[-1]] += temp.loc[reader['Team Name'] == team_name, reader.columns[-1]]
    
    reader.to_csv('data/gw_transfers.csv', index=False)

    return redirect(url_for('team_management', team_name=team_name))


#############################################################################################################################
@app.route('/gameweek_points/<team_name>', methods=['GET', 'POST'])
def gameweek_points(team_name):

    leaderboard_data = pd.read_csv('data/team_leaderboard.csv')

    gw_info = leaderboard_data.loc[leaderboard_data['Team Name'] == team_name]

    gw_info = leaderboard_data.loc[leaderboard_data['Team Name'] == team_name]
    for i in gw_info.columns[3::2]:
        x = eval((gw_info[i].values[0]))
        gw_info[i] = [x]
    gw_team_data1 = gw_info.iloc[:, 2:]
    index1 = gw_team_data1.index[0]

    with open('data/player_score.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    first_column = reader.iloc[:, 0]
    last_column = reader.iloc[:, -1]

    new_gw = pd.DataFrame(columns=[reader.columns[0], reader.columns[-1]])
    new_gw[reader.columns[0]] = first_column
    new_gw[reader.columns[-1]] = last_column

    gw = int(new_gw.columns[1].split(' ')[1])

    fixtures_data = pd.read_csv('data/fixtures.csv')

    if gw_team_data1.iloc[:, -2][index1] != '-':

        match = gw
        index = match - 1

        score_data = pd.read_csv('data/player_score.csv')

        new_df = pd.DataFrame([{'Player': item} for item in gw_team_data1[f'Gameweek {match} Team'][index1]])
        for index, row in new_df.iterrows():
            if index != new_df.index[-1]:
                if row.equals(new_df.loc[7]):
                    new_df = new_df.drop(index)
        new_df = new_df.drop(6)
        new_df = new_df.reset_index(drop=True)
        new_merged_df = new_df.merge(score_data[['Player', 'Position', f'Gameweek {gw}']], on='Player', how='inner')[['Player', 'Position', f'Gameweek {gw}']]

        new_merged_df = new_merged_df.rename(columns={f'Gameweek {gw}': 'Score'})

        new_merged_df = new_merged_df.merge(score_data, on=['Player', 'Position'], how='left')

        df1 = pd.read_csv(f'data/{gw}_player_stats.csv')
        df1.index = df1.index.astype(str)

        new_player_scores_breakdown = new_merged_df.merge(df1, on=['Player', 'Position'], how='left')

        new_player_scores_breakdown = new_player_scores_breakdown.to_dict(orient='list')

        return render_template('gameweek_points.html', team_name=team_name
                                , new_gw=new_gw
                                , gw=gw
                                , gw_team_data1=gw_team_data1
                                , index=index1
                                , fixtures_data=fixtures_data
                                , player_scores_breakdown=new_player_scores_breakdown
        )
    else:
        return None


#############################################################################################################################

@app.route('/scroll_down/<team_name>/<gw>', methods=['GET', 'POST'])
def scroll_down(team_name, gw):

    leaderboard_data = pd.read_csv('data/team_leaderboard.csv')

    gw_info = leaderboard_data.loc[leaderboard_data['Team Name'] == team_name]
    gw_info1 = gw_info.iloc[:, :-1]
    index_tm = gw_info1.iloc[:, :-1].index[0]

    gw = int(gw)

    if gw > 1:
        if gw_info1[f'Gameweek {gw -1}'][index_tm] != '-':
            gw = gw - 1
    
    for i in gw_info.columns[3::2]:
        x = eval((gw_info[i].values[0]))
        gw_info[i] = [x]
    gw_team_data1 = gw_info.iloc[:, 2:]
    index1 = gw_team_data1.index[0]

    with open('data/player_score.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    first_column = reader.iloc[:, 0]
    last_column = reader.iloc[:, gw+1]

    # Create a new DataFrame
    new_gw = pd.DataFrame(columns=[reader.columns[0], reader.columns[gw+1]])
    new_gw[reader.columns[0]] = first_column
    new_gw[reader.columns[gw+1]] = last_column

    fixtures_data = pd.read_csv('data/fixtures.csv')

    match = gw
    index = match - 1

    score_data = pd.read_csv('data/player_score.csv')

    new_df = pd.DataFrame([{'Player': item} for item in gw_team_data1[f'Gameweek {match} Team'][index1]])
    for index, row in new_df.iterrows():
        if index != new_df.index[-1]:
            if row.equals(new_df.loc[7]):
                new_df = new_df.drop(index)
    new_df = new_df.drop(6)
    new_df = new_df.reset_index(drop=True)
    new_merged_df = new_df.merge(score_data[['Player', 'Position', f'Gameweek {gw}']], on='Player', how='inner')[['Player', 'Position', f'Gameweek {gw}']]

    new_merged_df = new_merged_df.rename(columns={f'Gameweek {gw}': 'Score'})

    new_merged_df = new_merged_df.merge(score_data, on=['Player', 'Position'], how='left')

    df1 = pd.read_csv(f'data/{gw}_player_stats.csv')
    df1.index = df1.index.astype(str)

    new_player_scores_breakdown = new_merged_df.merge(df1, on=['Player', 'Position'], how='left')

    new_player_scores_breakdown = new_player_scores_breakdown.to_dict(orient='list')


    return render_template('gameweek_points.html', team_name=team_name
                            , new_gw=new_gw
                            , gw=gw
                            , gw_team_data1=gw_team_data1
                            , index=index1
                            , fixtures_data=fixtures_data
                            , player_scores_breakdown=new_player_scores_breakdown
                            )

#############################################################################################################################


@app.route('/scroll_up/<team_name>/<gw>', methods=['GET', 'POST'])
def scroll_up(team_name, gw):
    
    leaderboard_data = pd.read_csv('data/team_leaderboard.csv')
    max_gw = int(leaderboard_data.columns[-2].split()[-1])
    
    gw = int(gw)
    if gw < max_gw:
        gw = gw + 1
    
    gw_info = leaderboard_data.loc[leaderboard_data['Team Name'] == team_name]
    for i in gw_info.columns[3::2]:
        x = eval((gw_info[i].values[0]))
        gw_info[i] = [x]
    gw_team_data1 = gw_info.iloc[:, 2:]
    index1 = gw_team_data1.index[0]

    with open('data/player_score.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    first_column = reader.iloc[:, 0]
    last_column = reader.iloc[:, gw+1]

    new_gw = pd.DataFrame(columns=[reader.columns[0], reader.columns[gw+1]])
    new_gw[reader.columns[0]] = first_column
    new_gw[reader.columns[gw+1]] = last_column

    fixtures_data = pd.read_csv('data/fixtures.csv')

    match = gw
    index = match - 1

    score_data = pd.read_csv('data/player_score.csv')

    new_df = pd.DataFrame([{'Player': item} for item in gw_team_data1[f'Gameweek {match} Team'][index1]])
    for index, row in new_df.iterrows():
        if index != new_df.index[-1]:
            if row.equals(new_df.loc[7]):
                new_df = new_df.drop(index)
    new_df = new_df.drop(6)
    new_df = new_df.reset_index(drop=True)
    new_merged_df = new_df.merge(score_data[['Player', 'Position', f'Gameweek {gw}']], on='Player', how='inner')[['Player', 'Position', f'Gameweek {gw}']]

    new_merged_df = new_merged_df.rename(columns={f'Gameweek {gw}': 'Score'})

    new_merged_df = new_merged_df.merge(score_data, on=['Player', 'Position'], how='left')

    df1 = pd.read_csv(f'data/{gw}_player_stats.csv')
    df1.index = df1.index.astype(str)

    new_player_scores_breakdown = new_merged_df.merge(df1, on=['Player', 'Position'], how='left')

    new_player_scores_breakdown = new_player_scores_breakdown.to_dict(orient='list')


    return render_template('gameweek_points.html', team_name=team_name
                            , new_gw=new_gw
                            , gw=gw
                            , gw_team_data1=gw_team_data1
                            , index=index1
                            , fixtures_data=fixtures_data
                            , player_scores_breakdown=new_player_scores_breakdown
                            )


#############################################################################################################################

@app.route('/view_gameweek_points/<team_name>/<view_team_name>', methods=['GET', 'POST'])
def view_gameweek_points(team_name, view_team_name):

    leaderboard_data = pd.read_csv('data/team_leaderboard.csv')
    
    gw_info = leaderboard_data.loc[leaderboard_data['Team Name'] == view_team_name]
    for i in gw_info.columns[3::2]:
        x = eval((gw_info[i].values[0]))
        gw_info[i] = [x]
    gw_team_data1 = gw_info.iloc[:, 2:]
    index1 = gw_team_data1.index[0]

    with open('data/player_score.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    first_column = reader.iloc[:, 0]
    last_column = reader.iloc[:, -1]

    new_gw = pd.DataFrame(columns=[reader.columns[0], reader.columns[-1]])
    new_gw[reader.columns[0]] = first_column
    new_gw[reader.columns[-1]] = last_column

    gw = int(new_gw.columns[1].split(' ')[1])

    fixtures_data = pd.read_csv('data/fixtures.csv')

    match = gw
    index = match - 1

    score_data = pd.read_csv('data/player_score.csv')

    new_df = pd.DataFrame([{'Player': item} for item in gw_team_data1[f'Gameweek {match} Team'][index1]])
    for index, row in new_df.iterrows():
        if index != new_df.index[-1]:
            if row.equals(new_df.loc[7]):
                new_df = new_df.drop(index)
    new_df = new_df.drop(6)
    new_df = new_df.reset_index(drop=True)
    new_merged_df = new_df.merge(score_data[['Player', 'Position', f'Gameweek {gw}']], on='Player', how='inner')[['Player', 'Position', f'Gameweek {gw}']]

    new_merged_df = new_merged_df.rename(columns={f'Gameweek {gw}': 'Score'})

    new_merged_df = new_merged_df.merge(score_data, on=['Player', 'Position'], how='left')

    df1 = pd.read_csv(f'data/{gw}_player_stats.csv')
    df1.index = df1.index.astype(str)

    new_player_scores_breakdown = new_merged_df.merge(df1, on=['Player', 'Position'], how='left')

    new_player_scores_breakdown = new_player_scores_breakdown.to_dict(orient='list')

    return render_template('view_gameweek_points.html', team_name=team_name
                            , new_gw=new_gw
                            , gw=gw
                            , gw_team_data1=gw_team_data1
                            , index=index1
                            , fixtures_data=fixtures_data
                            , view_team_name=view_team_name
                            , player_scores_breakdown=new_player_scores_breakdown
                            )



#############################################################################################################################

@app.route('/view_scroll_down/<team_name>/<view_team_name>/<gw>', methods=['GET', 'POST'])
def view_scroll_down(team_name, view_team_name, gw):

    leaderboard_data = pd.read_csv('data/team_leaderboard.csv')

    gw_info = leaderboard_data.loc[leaderboard_data['Team Name'] == view_team_name]
    gw_info1 = gw_info.iloc[:, :-1]
    index_tm = gw_info1.iloc[:, :-1].index[0]

    gw = int(gw)

    if gw > 1:
        if gw_info1[f'Gameweek {gw -1}'][index_tm] != '-':
            gw = gw - 1

    for i in gw_info.columns[3::2]:
        x = eval((gw_info[i].values[0]))
        gw_info[i] = [x]
    gw_team_data1 = gw_info.iloc[:, 2:]
    index1 = gw_team_data1.index[0]

    with open('data/player_score.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    first_column = reader.iloc[:, 0]
    last_column = reader.iloc[:, gw+1]

    # Create a new DataFrame
    new_gw = pd.DataFrame(columns=[reader.columns[0], reader.columns[gw+1]])
    new_gw[reader.columns[0]] = first_column
    new_gw[reader.columns[gw+1]] = last_column

    fixtures_data = pd.read_csv('data/fixtures.csv')

    match = gw
    index = match - 1

    score_data = pd.read_csv('data/player_score.csv')

    new_df = pd.DataFrame([{'Player': item} for item in gw_team_data1[f'Gameweek {match} Team'][index1]])
    for index, row in new_df.iterrows():
        if index != new_df.index[-1]:
            if row.equals(new_df.loc[7]):
                new_df = new_df.drop(index)
    new_df = new_df.drop(6)
    new_df = new_df.reset_index(drop=True)
    new_merged_df = new_df.merge(score_data[['Player', 'Position', f'Gameweek {gw}']], on='Player', how='inner')[['Player', 'Position', f'Gameweek {gw}']]

    new_merged_df = new_merged_df.rename(columns={f'Gameweek {gw}': 'Score'})

    new_merged_df = new_merged_df.merge(score_data, on=['Player', 'Position'], how='left')

    df1 = pd.read_csv(f'data/{gw}_player_stats.csv')
    df1.index = df1.index.astype(str)

    new_player_scores_breakdown = new_merged_df.merge(df1, on=['Player', 'Position'], how='left')

    new_player_scores_breakdown = new_player_scores_breakdown.to_dict(orient='list')

    return render_template('view_gameweek_points.html', team_name=team_name
                            , new_gw=new_gw
                            , gw=gw
                            , gw_team_data1=gw_team_data1
                            , index=index1
                            , fixtures_data=fixtures_data
                            , view_team_name=view_team_name
                            , player_scores_breakdown=new_player_scores_breakdown
                            )



#############################################################################################################################

@app.route('/view_scroll_up/<team_name>/<view_team_name>/<gw>', methods=['GET', 'POST'])
def view_scroll_up(team_name, view_team_name, gw):
    
    leaderboard_data = pd.read_csv('data/team_leaderboard.csv')
    max_gw = int(leaderboard_data.columns[-2].split()[-1])
    
    gw = int(gw)
    if gw < max_gw:
        gw = gw + 1
    
    gw_info = leaderboard_data.loc[leaderboard_data['Team Name'] == view_team_name]
    for i in gw_info.columns[3::2]:
        x = eval((gw_info[i].values[0]))
        gw_info[i] = [x]
    gw_team_data1 = gw_info.iloc[:, 2:]
    index1 = gw_team_data1.index[0]

    with open('data/player_score.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    first_column = reader.iloc[:, 0]
    last_column = reader.iloc[:, gw+1]

    new_gw = pd.DataFrame(columns=[reader.columns[0], reader.columns[gw+1]])
    new_gw[reader.columns[0]] = first_column
    new_gw[reader.columns[gw+1]] = last_column

    fixtures_data = pd.read_csv('data/fixtures.csv')

    match = gw
    index = match - 1

    score_data = pd.read_csv('data/player_score.csv')

    new_df = pd.DataFrame([{'Player': item} for item in gw_team_data1[f'Gameweek {match} Team'][index1]])
    for index, row in new_df.iterrows():
        if index != new_df.index[-1]:
            if row.equals(new_df.loc[7]):
                new_df = new_df.drop(index)
    new_df = new_df.drop(6)
    new_df = new_df.reset_index(drop=True)
    new_merged_df = new_df.merge(score_data[['Player', 'Position', f'Gameweek {gw}']], on='Player', how='inner')[['Player', 'Position', f'Gameweek {gw}']]

    new_merged_df = new_merged_df.rename(columns={f'Gameweek {gw}': 'Score'})

    new_merged_df = new_merged_df.merge(score_data, on=['Player', 'Position'], how='left')

    df1 = pd.read_csv(f'data/{gw}_player_stats.csv')
    df1.index = df1.index.astype(str)

    new_player_scores_breakdown = new_merged_df.merge(df1, on=['Player', 'Position'], how='left')

    new_player_scores_breakdown = new_player_scores_breakdown.to_dict(orient='list')


    return render_template('view_gameweek_points.html', team_name=team_name
                            , new_gw=new_gw
                            , gw=gw
                            , gw_team_data1=gw_team_data1
                            , index=index1
                            , fixtures_data=fixtures_data
                            , view_team_name=view_team_name
                            , player_scores_breakdown=new_player_scores_breakdown
                            )


#############################################################################################################################

@app.route('/team_of_the_week/<team_name>/<match>', methods=['GET', 'POST'])
def team_of_the_week(team_name, match):

    results = pd.read_csv('data/results.csv')
    score_data = pd.read_csv('data/player_score.csv')
    match = int(match)
    index = match - 1

    fixtures = pd.read_csv('data/fixtures.csv')
    opponent = fixtures['Fixture'][index]
    score = fixtures['Score'][index]
    goals_for = (score.split('-')[0])
    goals_against = (score.split('-')[1])


    played = results.loc[results['Gameweek'] == match, 'Team'][index]
    df = pd.DataFrame({'Player': eval(played)})

    week_scores = score_data[['Player', 'Position', f'Gameweek {match}']]

    played_scores = week_scores.merge(df, on='Player', how='inner')

    sorted_df = played_scores.sort_values(f'Gameweek {match}', ascending=False)

    player_of_week = sorted_df['Player'].iloc[0]

    empty_df = pd.DataFrame(columns=sorted_df.columns)

    for _, row in sorted_df.iterrows():
        position = row['Position']

        if (position == 'DEF' and empty_df['Position'].eq('DEF').sum() < 2) or \
        (position == 'MID' and empty_df['Position'].eq('MID').sum() < 2) or \
        (position == 'FWD' and empty_df['Position'].eq('FWD').sum() < 1):
            
            empty_df = pd.concat([empty_df, row.to_frame().T], ignore_index=True)
        
        if len(empty_df) >= 4:
            break

    for _, row in sorted_df.iterrows():
        position = row['Position']
        if position == 'GK' and empty_df['Position'].eq('GK').sum() < 1:
                empty_df = pd.concat([empty_df, row.to_frame().T], ignore_index=True)
                break
        
    empty_df = empty_df.sort_values(f'Gameweek {match}', ascending=False)

    position_order = ['GK', 'DEF', 'MID', 'FWD']

    empty_df = empty_df.sort_values('Position', key=lambda x: x.map({pos: i for i, pos in enumerate(position_order)}))

    remaining_players = pd.merge(sorted_df, empty_df['Player'], on='Player', how='left', indicator=True)
    remaining_players = remaining_players[remaining_players['_merge'] == 'left_only']
    remaining_players = remaining_players.drop(columns='_merge')

    sorted_player_scores = pd.concat([empty_df, remaining_players])
    sorted_player_scores = sorted_player_scores.rename(columns={f'Gameweek {match}': 'Score'})
    sorted_player_scores = sorted_player_scores.reset_index(drop=True)

    position_counts = empty_df['Position'].value_counts()
    if 'FWD' not in position_counts:
        formation = 1
    elif position_counts['MID'] == 1:
        formation = 2
    elif position_counts['DEF'] == 1:
        formation = 3

    gw = match
    index = match - 1

    score_data = pd.read_csv('data/player_score.csv')

    new_merged_df = sorted_player_scores.rename(columns={f'Gameweek {gw}': 'Score'})

    new_merged_df = new_merged_df.merge(score_data, on=['Player', 'Position'], how='left')

    df1 = pd.read_csv(f'data/{gw}_player_stats.csv')
    df1.index = df1.index.astype(str)

    new_player_scores_breakdown = new_merged_df.merge(df1, on=['Player', 'Position'], how='left')
    new_player_scores_breakdown_bonus_ordered = new_player_scores_breakdown.sort_values(by='Bonus', ascending=False)

    new_player_scores_breakdown = new_player_scores_breakdown.to_dict(orient='list')
    new_player_scores_breakdown_bonus_ordered = new_player_scores_breakdown_bonus_ordered.to_dict(orient='list')

    return render_template('team_of_the_week.html', team_name=team_name
                            , sorted_player_scores=sorted_player_scores
                            , formation=formation
                            , match=match
                            , player_scores_breakdown=new_player_scores_breakdown
                            , man_of_match = player_of_week
                            , goals_for=goals_for
                            , goals_against=goals_against
                            , opponent=opponent
                            , bonus_ordered=new_player_scores_breakdown_bonus_ordered
    )

#############################################################################################################################



@app.route('/change_player_build')
def change_player_build():
    player_index = int(request.args.get('playerIndex'))
    team_name = request.args.get('teamName')  # Get the team_name from the URL parameter
    new_team_name = team_name.replace('%20', ' ')

    player_data = pd.read_csv('data/player_database.csv')

    fixture_data = pd.read_csv('data/fixtures.csv')
    fixture_data['Gameweek'] = fixture_data['Gameweek'].astype(int)
    fixture_data = fixture_data.drop('Result', axis=1)
    fixture_data = fixture_data.to_dict(orient='list')

    # Read the existing team data from team_data.csv
    with open('data/team_data.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    team_data = []
    for row in reader.itertuples(index=False):
        if row[0] == new_team_name:
            team_data.extend(row[1:7])  # Append individual player names to team_data

    player_score = pd.read_csv('data/player_score.csv')
    player_score = player_score.merge(player_data, on=['Player', 'Position'])

    if player_index == 1:
        filtered_players = player_score[player_score['Position'] == 'GK']
    elif player_index in [2, 3]:
        filtered_players = player_score[player_score['Position'] == 'DEF']
    elif player_index in [4, 5]:
        filtered_players = player_score[player_score['Position'] == 'MID']
    elif player_index == 6:
        filtered_players = player_score[player_score['Position'] == 'FWD']

    filtered_players = filtered_players.sort_values('Total Points', ascending=False)
    players = filtered_players.to_dict('list')

    if player_index == 1:
        player_data = player_data[player_data['Position'] == 'GK']
    elif player_index in [2, 3]:
        player_data = player_data[player_data['Position'] == 'DEF']
    elif player_index in [4, 5]:
        player_data = player_data[player_data['Position'] == 'MID']
    elif player_index == 6:
        player_data = player_data[player_data['Position'] == 'FWD']

    player_data = player_data.sort_values('Total Points', ascending=False)
    player_data = player_data.to_dict(orient='list')

    injury_data = pd.read_csv('data/injuries.csv')
    injury_data = injury_data.to_dict(orient='records')
    
    return render_template('change_player_build.html', player_index=player_index
                           , players=players, team_name=team_name, team_data=team_data
                           , fixture_data=fixture_data, player_data=player_data
                           , injury_data=injury_data)

#############################################################################################################################

@app.route('/change_player_transfer')
def change_player_transfer():
    player_index = int(request.args.get('playerIndex'))
    team_name = request.args.get('teamName')  # Get the team_name from the URL parameter
    new_team_name = team_name.replace('%20', ' ')

    # Read the player data from player_database.csv
    player_data = pd.read_csv('data/player_database.csv')

    fixture_data = pd.read_csv('data/fixtures.csv')
    fixture_data['Gameweek'] = fixture_data['Gameweek'].astype(int)
    fixture_data = fixture_data.drop('Result', axis=1)
    fixture_data = fixture_data.to_dict(orient='list')

    # Read the existing team data from team_data.csv
    with open('data/team_data_temp.csv', 'r') as csvfile:
        reader = pd.read_csv(csvfile)

    team_data = []
    for row in reader.itertuples(index=False):
        if row[0] == new_team_name:
            team_data.extend(row[1:7])

    player_score = pd.read_csv('data/player_score.csv')
    player_score = player_score.merge(player_data, on=['Player', 'Position'])

    if player_index == 1:
        filtered_players = player_score[player_score['Position'] == 'GK']
    elif player_index in [2, 3]:
        filtered_players = player_score[player_score['Position'] == 'DEF']
    elif player_index in [4, 5]:
        filtered_players = player_score[player_score['Position'] == 'MID']
    elif player_index == 6:
        filtered_players = player_score[player_score['Position'] == 'FWD']

    filtered_players = filtered_players.sort_values('Total Points', ascending=False)

    players = filtered_players.to_dict('list')

    if player_index == 1:
        player_data = player_data[player_data['Position'] == 'GK']
    elif player_index in [2, 3]:
        player_data = player_data[player_data['Position'] == 'DEF']
    elif player_index in [4, 5]:
        player_data = player_data[player_data['Position'] == 'MID']
    elif player_index == 6:
        player_data = player_data[player_data['Position'] == 'FWD']

    player_data = player_data.sort_values('Total Points', ascending=False)
    player_data = player_data.to_dict(orient='list')

    injury_data = pd.read_csv('data/injuries.csv')
    injury_data = injury_data.to_dict(orient='records')
    
    return render_template('change_player_transfer.html', player_index=player_index
                           , players=players, team_name=team_name, team_data=team_data
                           , fixture_data=fixture_data, player_data=player_data
                           , injury_data=injury_data)

#############################################################################################################################

@app.route('/add_player_build', methods=['POST'])
def add_player_build():
    player_index = int(request.args.get('playerIndex'))
    team_name = request.args.get('teamName')
    new_team_name = team_name
    new_team_name = new_team_name.split('%20')
    new_team_name = ' '.join(new_team_name)
    player_name = request.form.get('playerName')
    
    # Read the existing team data from team_data.csv
    with open('data/team_data.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        team_data = list(reader)
    
    # Update the corresponding player column in team_data
    for row in team_data:
        if row[0] == new_team_name:
            row[player_index] = player_name
            break

    # Write the updated team data back to team_data.csv
    with open('data/team_data.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(team_data)
    
    # Redirect back to the build team page
    return redirect(url_for('build_team', team_name=team_name))

#############################################################################################################################

@app.route('/add_player_transfer', methods=['POST'])
def add_player_transfer():
    player_index = int(request.args.get('playerIndex'))
    team_name = request.args.get('teamName')
    new_team_name = team_name
    new_team_name = new_team_name.split('%20')
    new_team_name = ' '.join(new_team_name)
    player_name = request.form.get('playerName')
    
    # Read the existing team data from team_data.csv
    with open('data/team_data_temp.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        team_data = list(reader)
    
    # Update the corresponding player column in team_data
    for row in team_data:
        if row[0] == new_team_name:
            row[player_index] = player_name
            break

    # Write the updated team data back to team_data.csv
    with open('data/team_data_temp.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(team_data)


    # Read the existing team data from team_data.csv
    with open('data/gw_transfers_temp.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        transfers_data = list(reader)
    
    # Update the corresponding player column in team_data
    for row in transfers_data:
        if row[0] == new_team_name:       #lining up team name row
            row[-2] = int(row[-2])
            row[-1] = int(row[-1])
            row[1] = int(row[1])

            row[-2] += 1

            if row[1] == 0 and transfers_data[0][-1] != 'Gameweek 1 Cost':                    #if free transfers == 0
                row[-1] = int(row[-1])
                row[-1] -= 4

            if row[1] > 0:                                  #if free transfers greater than 0, deduct
                row[1] = int(row[1])
                row[1] -= 1
                
            break
            
    # Write the updated team data back to team_data.csv
    with open('data/gw_transfers_temp.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(transfers_data)
    
    # Redirect back to the build team page
    return redirect(url_for('transfers', team_name=team_name))

#############################################################################################################################


def read_team_data(team_name):
    team_data = {}
    # new_team_name = team_name
    # new_team_name = new_team_name.split('%20')
    # new_team_name = ' '.join(new_team_name)
    with open('data/team_data.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Team Name'] == team_name:
                team_data = row
                break
    return team_data

#############################################################################################################################

# The code for read_csv() function
def read_csv(file_path):
    data = {}
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            for key, value in row.items():
                if key not in data:
                    data[key] = []
                data[key].append(value)
    return data

#############################################################################################################################

@app.route('/player_statistics/<team_name>')
def player_statistics(team_name):
    
    player_data = pd.read_csv('data/player_database.csv')

    goals_data = pd.read_csv('data/goals.csv')
    goals_data = goals_data.sort_values('Goals', ascending=False)
    goals_data = goals_data[goals_data['Goals'] > 0]
    goals_data = goals_data.to_dict(orient='list')
    
    assists_data = pd.read_csv('data/assists.csv')
    assists_data = assists_data.sort_values('Assists', ascending=False)
    assists_data = assists_data[assists_data['Assists'] > 0]
    assists_data = assists_data.to_dict(orient='list')

    player_score = pd.read_csv('data/player_score.csv')
    player_score = player_score.merge(player_data, on=['Player', 'Position'])
    player_score = player_score.sort_values('Total Points', ascending=False)
    player_score = player_score.drop(columns = ['Price', 'Form', 'Total Points'])
    player_score = player_score.to_dict(orient='list')

    player_data = player_data.sort_values('Total Points', ascending=False)
    player_data = player_data.to_dict(orient='list')

    fixture_data = pd.read_csv('data/fixtures.csv')
    fixture_data['Gameweek'] = fixture_data['Gameweek'].astype(int)
    fixture_data = fixture_data.drop('Result', axis=1)
    fixture_data = fixture_data.to_dict(orient='list')


    return render_template('player_statistics.html', player_data=player_data, goals_data=goals_data
                           , assists_data=assists_data, team_name=team_name
                           , player_score=player_score, fixture_data=fixture_data)

#############################################################################################################################

@app.route('/leaderboard/<team_name>')
def leaderboard(team_name):
    leaderboard_data = pd.read_csv('data/team_leaderboard.csv')
    leaderboard_data = leaderboard_data.sort_values('Total Score', ascending=False)

    keys = leaderboard_data.columns[:1].values[0]
    keys1 = leaderboard_data.columns[1:2].values[0]
    keys2 = leaderboard_data.columns[-2:-1].values[0]

    values = leaderboard_data.iloc[:, :1].values.flatten().tolist()
    values1 = leaderboard_data.iloc[:, 1:2].values.flatten().tolist()
    values2 = leaderboard_data.iloc[:, -2:-1].values.flatten().tolist()

    leaderboard_data = {}
    leaderboard_data1 = {}
    leaderboard_data2 = {}

    leaderboard_data[keys] = values
    leaderboard_data[keys1] = values1
    leaderboard_data2[keys2] = values2
    
    leaderboard_data.update(leaderboard_data2)
    leaderboard_data.update(leaderboard_data1)
    return render_template('leaderboard.html', team_name=team_name, leaderboard_data=leaderboard_data)

#############################################################################################################################

@app.route('/fixtures/<team_name>')
def fixture(team_name):

    fixture_data = pd.read_csv('data/fixtures.csv')

    return render_template('fixtures.html', team_name=team_name, fixture_data=fixture_data)

#############################################################################################################################

@app.route('/admin/<team_name>/<current_gw>')
def admin(team_name, current_gw):

    next_gw = int(current_gw[len('Gameweek '):]) + 1

    return render_template('admin.html', team_name=team_name, next_gw=next_gw)

#############################################################################################################################

@app.route('/pass_next_deadline', methods=['POST'])
def pass_next_deadline():

    team_name = request.args.get('teamName')
    next_gw = request.args.get('nextGW')
    next_gw = int(next_gw)

    current_gw = f'Gameweek {next_gw -1}'

    pass_deadline.pass_deadline(gameweek = next_gw)

    return redirect(url_for('admin', team_name=team_name, current_gw=current_gw))

#############################################################################################################################

@app.route('/add_next_results', methods=['POST'])
def add_next_results():

    team_name = request.args.get('teamName')
    next_gw = request.args.get('nextGW')
    next_gw = int(next_gw) - 1
    current_gw = f'Gameweek {next_gw}'

    score = request.form['score']
    team = json.loads(request.form['team'])
    goal_scorers = json.loads(request.form['goalScorers'])
    assists = json.loads(request.form['assists'])
    bonuses = json.loads(request.form['bonuses'])
    saves = int(request.form['saves'])
    yellow_cards = json.loads(request.form['yellow_cards'])
    red_cards = json.loads(request.form['red_cards'])
    own_goals = json.loads(request.form['own_goals'])

    bonus_3, bonus_2, bonus_1 = bonuses[:3]

    add_results.add_gameweek_score(gameweek=next_gw, score=score, team=team
                                   , goal_scorers=goal_scorers, assists=assists
                                   , bonus_1=bonus_1, bonus_2=bonus_2, bonus_3=bonus_3, saves=saves
                                   , yellow_cards=yellow_cards, red_cards=red_cards, own_goals=own_goals)

    return redirect(url_for('admin', team_name=team_name, current_gw=current_gw))


#############################################################################################################################

@app.route('/add_next_injury', methods=['POST'])
def add_next_injury():

    team_name = request.args.get('teamName')
    next_gw = request.args.get('nextGW')
    next_gw = int(next_gw) - 1
    current_gw = f'Gameweek {next_gw}'

    player = request.form.get('player')
    injury_type = request.form.get('injury_type')
    injury_colour = request.form.get('injury_colour')
    return_date = request.form.get('return_date')

    print(player, injury_type, injury_colour, return_date)

    add_injury.add_injury(player = player
                          , injury_colour = injury_colour
                          , injury_type = injury_type
                          , return_date = return_date)


    return redirect(url_for('admin', team_name=team_name, current_gw=current_gw))


#############################################################################################################################

from urllib.parse import quote

@app.template_filter('urlencode')
def urlencode_filter(s):
    return quote(s)

#############################################################################################################################

@app.route('/team_not_found/<team_name>')
def team_not_found(team_name):
    return render_template('team_not_found.html', team_name=team_name)

#############################################################################################################################

# The code to create the database tables and run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
