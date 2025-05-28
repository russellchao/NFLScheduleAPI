import requests 
import json
import csv


def formatDate(date):
    monthNumToName = {1: "January", 2: "February", 9: "September", 10: "October", 11: "November", 12: "December"}

    theMonth = str() 
    theDay = str() 
    theYear = str()

    for i in range(len(date)):
        if i <= 3:
            theYear += date[i]
        elif 3 < i <= 5:
            theMonth += date[i]
        else:
            theDay += date[i]

    theMonth = monthNumToName.get(int(theMonth))

    if theDay[0] == '0':
        theDay = theDay[1] # e.g. Changes September 04 to September 4

    return f"{theMonth} {theDay}, {theYear}"



def get_schedule_data(year, week, seasonType):

    # Call the unofficial ESPN API to Retrieve Schedule Data
    espn_api_url = f"https://cdn.espn.com/core/nfl/schedule?xhr=1&year={year}&week={week}&seasontype={seasonType}"
    response = requests.get(espn_api_url)

    if (response.status_code != 200):
        print(int(response.headers["Retry-After"]))
        raise Exception(f"Failed to load ESPN page ({response.status_code})")
    
    data = response.json()
    content = data.get("content", {})
    schedule = content.get("schedule", {})

    # Write the schedule to a .json file
    with open("ScheduleOutput.json", "w") as file:
        json.dump(schedule, file, indent=4)


    # Week numbers mapped to their respective rounds for the playoffs
    playoffKeys = {1: "Wild Card Round", 2: "Divisional Round", 3: "Conference Championships", 5: "Super Bowl"}


    # Testing Output
    if seasonType == 2:
        print(f"Week {week} {year} Schedule dates:\n")
    elif seasonType == 3:
        print(f"{playoffKeys.get(week)} {year} dates:\n")


    # Loop through the .json output to retreieve each matchup for the given week
    # each "date" follows the format of something like: YYYYMMDD (e.g. 20250904)
    allMatchupsThisWk = []
    for date in schedule:

        gamesThisDate = schedule[date]

        for matchup in gamesThisDate.get("games"):

            ###### Attributes for games ######

            # date only (exclude start time)
            fullDate = formatDate(date) # (e.g. 20250904 becomes September 4, 2025)


            # week number 
            weekNum = matchup.get("week").get("number")
            if seasonType == 3:
                # if it's the playoffs, retrieve the appropriate round given the week
                weekNum = playoffKeys.get(int(weekNum))


            # check if the status of a game is scheduled or finished (in the future I will try my best to scrape live games)
            status = matchup.get("competitions")[0].get("status").get("type").get("description")


            # home and away teams
            matchupNameSplit = matchup.get("name").split(" at ") # e.g. split "Buffalo Bills at New York Jets" to ['Buffalo Bills', 'New York Jets']
            awayTeam = matchupNameSplit[0]
            homeTeam = matchupNameSplit[1]


            # home and away team's regular season records 
            #NOTE: in the offseason, ESPN does not count records for teams, so the record will be defaulted to 0-0
            # I think once the regular season starts, each team's records will be available in Scheduled games
            awayTeamRecord = "0-0"
            homeTeamRecord = "0-0"

            if status == "Final":
                awayTeamRecord = matchup.get("competitions")[0].get("competitors")[1].get("records")[0].get("summary")
                homeTeamRecord = matchup.get("competitions")[0].get("competitors")[0].get("records")[0].get("summary")


            # venue info
            if (matchup.get("competitions")[0].get("venue") == None):
                # namely used for playoff games that are TBD
                fullVenue = "TBD"
            else:
                stadium = matchup.get("competitions")[0].get("venue").get("fullName")
                city = matchup.get("competitions")[0].get("venue").get("address").get("city")
                state = matchup.get("competitions")[0].get("venue").get("address").get("state")
                country = matchup.get("competitions")[0].get("venue").get("address").get("country")
                fullVenue = f"{stadium}, {city}, {state}, {country}"

            
            # broadcast channel
            broadcast = matchup.get("competitions")[0].get("broadcast")
            if broadcast == "":
                broadcast = "TBD"

            
            # Test output
            print(f"Date: {fullDate}")
            print(f"Week: {weekNum}")
            print(f"Matchup: {awayTeam} ({awayTeamRecord}) at {homeTeam} ({homeTeamRecord})")
            print(f"Venue: {fullVenue}")
            print(f"Broadcast: {broadcast}")
            print(f"Status: {status}\n")


            # Add this matchup to the matchups this week list
            matchup_data = {'Date': fullDate, 'WeekNum': weekNum, 'Status': status, 'AwayTeam': awayTeam, 
                            'AwayTeamRecord': awayTeamRecord, 'HomeTeam': homeTeam, 'HomeTeamRecord': homeTeamRecord, 
                            'Venue': fullVenue, 'Broadcast': broadcast, 'SeasonType': seasonType, 'WeekId': week}
            allMatchupsThisWk.append(matchup_data)
            

    # Write the header to the .csv file
    csvFilename = "schedule_data.csv"
    header = ['Date', 'WeekNum', 'Status', 'AwayTeam', 'AwayTeamRecord', 'HomeTeam', 'HomeTeamRecord', 
              'Venue', 'Broadcast', 'SeasonType', 'WeekId']
    try:
        with open(csvFilename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=header)
            writer.writeheader()
            writer.writerows(allMatchupsThisWk)
    except Exception as e:
        print(f"SCHEDULE DATA FILE WRITE ERROR:", e)

    print("------------------------------------------------------------------------\n")
        





    
if __name__ == "__main__":

    '''
    Examples extracting the schedule (for seasonType: 1=preseason, 2=regular season, 3=playoffs) 
        but honestly I don't care about preseason

      get_schedule_data(2025, 1, 2) for Week 1 of 2025, 
      get_schedule_data(2024, 15, 2) for Week 15 of 2024, 
      get_schedule_data(2024, 5, 3) for Super Bowl of 2024-25 (Eagles 40, Chiefs 22)
    '''

    playoffWeekMapping = {"wc": 1, "div": 2, "cc": 3, "sb": 5}

    while True: 
        year = input("Enter the year you want to see NFL matchups from: ")
        week = input ("Enter the week (1-18) you want to see the matchups from that year\n" \
        "(For playoffs, enter wc for Wild Card Round, div for Divisional Round, cc for Conf. Champs, or sb for Super Bowl): ")

        year = year.strip()
        week = week.lower().strip()

        if week in playoffWeekMapping.keys():
            get_schedule_data(year, playoffWeekMapping.get(week), 3)
        else:
            get_schedule_data(year, week, 2)
        