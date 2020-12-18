import numpy as np
import urllib.request
from urllib.request import urlopen
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re

###########################
# code to predict german bundesliga results
# I only predict a winner, no draws
# based on xGoals
# Author: Christoph Riess, November 2020
###########################


#### SETTINGS
randomness = 0.3 # standard dev of prediction randomness of scored goals
home_advantage = 0.02 # home advantage in goals

### DATA
# dictionary with names for teams from both websites
name_conv = {
'FC Bayern München'         :   'Bayern Munich',
'RB Leipzig'                :   'RB Leipzig',
'Borussia Mönchengladbach'  :   "M'Gladbach",
'Borussia Dortmund'         :   'Dortmund',
'Bayer 04 Leverkusen'       :   'Leverkusen',
'FC Schalke 04'             :   'Schalke 04',
'VfL Wolfsburg'             :   'Wolfsburg',
'TSG Hoffenheim'            :   'Hoffenheim',
'Sport-Club Freiburg'       :   'Freiburg',
'1. FC Köln'                :   'Köln',
'1. FC Union Berlin'        :   'Union Berlin',
'Eintracht Frankfurt'       :   'Eint Frankfurt',
'FC Augsburg'               :   'Augsburg',
'Hertha Berlin'             :   'Hertha BSC',
'1. FSV Mainz 05'           :   'Mainz 05',
'VfB Stuttgart'             :   'Stuttgart',
'SV Werder Bremen'          :   'Werder Bremen',
'DSC Arminia Bielefeld'     :   'Arminia',
}

#### FUNCTIONS
def parse_html_table(table):
    n_columns = 0
    n_rows=0
    column_names = []
    # Find number of rows and columns
    # we also find the column titles if we can
    for row in table.find_all('tr'):
        # Determine the number of rows in the table
        td_tags = row.find_all('td')
        if len(td_tags) > 0:
            n_rows+=1
            if n_columns == 0:
                # Set the number of columns for our table
                n_columns = len(td_tags)
        # Handle column names if we find them
        th_tags = row.find_all('th')
        if len(th_tags) > 0 and len(column_names) == 0:
            i=1
            while i < len(th_tags):
                column_names.append(th_tags[i].get_text())
                i+=1
    columns = column_names if len(column_names) > 0 else range(0,n_columns)
    df = pd.DataFrame(columns = columns,
                      index= range(0,n_rows))
    row_marker = 0
    for row in table.find_all('tr'):
        column_marker = 0
        columns = row.find_all('td')
        for column in columns:
            df.iat[row_marker,column_marker] = column.get_text()
            column_marker += 1
        if len(columns) > 0:
            row_marker += 1
    # Convert to float if possible
    for col in df:
        try:
            df[col] = df[col].astype(float)
        except ValueError:
            pass

    return df

# return xG of given team
def give_xG(df,teamname):
    alias = name_conv[teamname]
    xg = df[df['Squad']==alias]['xG'].values[0]
    xga = df[df['Squad']==alias]['xGA'].values[0]
    games =  df[df['Squad']==alias]['MP'].values[0]
    return xg/games,xga/games


### COMPUTATION


#read xGoals table from web
# Set headers
headers = requests.utils.default_headers()
headers.update({ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'})
url = "https://fbref.com/en/comps/20/10737/2020-2021-Bundesliga-Stats"
req = requests.get(url, headers)
soup = BeautifulSoup(req.content, 'html.parser')
#print(soup.prettify())
table = soup.find_all('table')[0]


df =parse_html_table(table)
df['Squad'] = df['Squad'].str.strip()
#print(df)


#read games from web
headers = requests.utils.default_headers()
headers.update({ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'})
url = 'https://www.bundesliga.com/en/bundesliga/matchday'
req = requests.get(url, headers)
soup = BeautifulSoup(req.content, 'html.parser')
#print(soup.prettify())
hometeams = soup.find_all(class_ = 'teamHome' )
awayteams = soup.find_all(class_ = 'teamAway' )
games =[[0 for x in range(2)] for y in range(len(hometeams))]
for i in range(len(hometeams)):
    games[i][0] =re.search('alt=\"(.*?)\"',str(hometeams[i])).group(1)
    games[i][1] =re.search('alt=\"(.*?)\"',str(awayteams[i])).group(1)

# loop over games and predict outcome
for i in range(len(games)):
    # randomness and bonus for hometeam
    rand_a = np.random.normal(home_advantage,randomness)
    rand_b = np.random.normal(0,randomness)


    xg_0,xga_0 = give_xG(df,games[i][0])
    xg_1,xga_1 = give_xG(df,games[i][1])

    result_a = (xg_0 + xga_1)/2 +rand_a
    result_b = (xg_1+xga_1)/2+rand_b
    # no draws
    #print(result_a-result_b)
    if round(result_a) == round(result_b):
        if result_a<result_b:
            if round(result_a)>0:
                result_a -=1
            else:
                result_b +=1
        else:
            if round(result_b)>0:
                result_b -=1
            else:
                result_a +=1
    # make result more clear
    elif abs(round(result_a)-round(result_b))==1:
        if abs(result_a-result_b)>0.6 and abs(result_a-result_b)<2:
            if result_a<result_b:
                if round(result_a)>0:
                    result_a -=1
                else:
                    result_b +=1
            else:
                if round(result_b)>0:
                    result_b -=1
                else:
                    result_a +=1
    result = str(int(round(result_a)))+":"+str(int(round(result_b)))
    print(f"{games[i][0]:30}:  {games[i][1]:30} = "+result)
