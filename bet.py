import numpy as np
import urllib.request
from urllib.request import urlopen
import pandas as pd
from bs4 import BeautifulSoup
import requests


###########################
# code to predict german bundesliga results
# I only predict a winner, no draws
# based on xGoals
# Author: Christoph Riess, November 2020
###########################

# settings
randomness = 0.3 # standard dev of prediction randomness of scored goals
home_advantage = 0.02 # home advantage in goals

# start computation

#read xGoals from web
# Set headers
headers = requests.utils.default_headers()
headers.update({ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'})
url = "https://fbref.com/en/comps/20/10737/2020-2021-Bundesliga-Stats"
req = requests.get(url, headers)
soup = BeautifulSoup(req.content, 'html.parser')
#print(soup.prettify())
table = soup.find_all('table')[0]

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

    # Safeguard on Column Titles
    # if len(column_names) > 0 and len(column_names) != n_columns:
    #     raise Exception("Column titles do not match the number of columns")

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

def give_short(dict,search_name):
    for short,long in dict.items():
        if long == search_name:
            return short

def give_xG(df,short):
    long = name_conv[short]
    xg = df[df['Squad']==long]['xG'].values[0]
    xga = df[df['Squad']==long]['xGA'].values[0]
    games =  df[df['Squad']==long]['MP'].values[0]
    return xg/games,xga/games

df =parse_html_table(table)
df['Squad'] = df['Squad'].str.strip()
#print(df)

# dictionary with short names for teams
name_conv = {
"FCB"   :   'Bayern Munich',
"RBL"   :   'RB Leipzig',
"BMG"   :   "M'Gladbach",
"BVB"   :   'Dortmund',
"B04"   :   'Leverkusen',
"S04"   :   'Schalke 04',
"WOB"   :   'Wolfsburg',
"HOF"   :   'Hoffenheim',
"SCF"   :   'Freiburg',
"FCK"   :   'Köln',
"FCU"   :   'Union Berlin',
"SGE"   :   'Eint Frankfurt',
"FCA"   :   'Augsburg',
"BSC"   :   'Hertha BSC',
"FSV"   :   'Mainz 05',
"VFB"   :   'Stuttgart',
"BRE"   :   'Werder Bremen',
"DSC"   :   'Arminia',
}

#print(give_short(xG,'Leverkusen'))

# games to predict
games = {
"1" :   ("S04","WOB"),
"2" :   ("HOF","VFB"),
"3" :   ("BMG","FCA"),
"4" :   ("FCB","BRE"),
"5" :   ("DSC","B04"),
"6" :   ("SGE","RBL"),
"7" :   ("BSC","BVB"),
"8" :   ("SCF","FSV"),
"9" :   ("FCK","FCU"),
}


for i in range (1,10):
    # randomness and bonus for hometeam
    rand_a = np.random.normal(home_advantage,randomness)
    rand_b = np.random.normal(0,randomness)


    xg_0,xga_0 = give_xG(df,games[str(i)][0])
    xg_1,xga_1 = give_xG(df,games[str(i)][1])

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
    print("Result  "+games[str(i)][0]+":"+games[str(i)][1]+" = "+result)
