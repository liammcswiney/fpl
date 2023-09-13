import csv

def add_injury(player, injury_colour, injury_type, return_date):

    file_name='data/injuries.csv'

    with open(file_name, mode='r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)
    
    for row in data:
        if row[0] == player:
            row[1] = injury_colour
            row[2] = injury_type
            row[3] = return_date
            break

    with open(file_name, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)
