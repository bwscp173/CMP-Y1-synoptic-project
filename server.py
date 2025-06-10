"""====================================================================================================

File                     :  server.py

date                     :  2/6/2025

Description              :  will host the flask server

History                  :  

                            4/6/2025 - now uses the dictionary in 'weather_code_lookup.py'

===================================================================================================="""




#will attempt to make the server.java in this file as working with python for requests
#is soo much easier and more portable. and the benefits of using java for portibility go down
#when we assume that if someone wants to set up one of these servers, they can install python. 
#description will get the latitude and longitude from the client, maybe the city name.
#and this server will fetch the data from API's like "https://wttr.in/norwich" and give only the needed
#information to the client
#
#so a client server interaction will look something like:
#client: my location is 59.123,22.423
#server: *TODO check a database for the most recent API calls*
#        *if the last API call was made 15> then make another API call to fetch a weeks worth of data and saves it to a database*
#        here is the most recent 7 day forcast
#client and server: ends connection.
#client: *saves the data from the server, and will display that data when its impossible to connect to the server*
#
#the minimal communication between the client/server is a priority
#
# i dont think i can set up a static IP on uni wifi so for the project we will have to type in some numbers for the client


import requests
from datetime import datetime, timedelta
from flask import Flask, request, render_template
import sqlite3  # for the databse of the most recent API call, moved away from pgadmin as this import allows just the .db file without any login information
import os
#custom imports
import database_handler
import weather_code_lookup


# if os.path.exists("weather_api_logs.db"):
#   os.remove("weather_api_logs.db")

APP = Flask(__name__)
conn = database_handler.setup_conn("weather_api_logs.db")
if conn == None:
    print("cannot connect to the database")
    exit(-1)
DATABASE_HANDL= database_handler.database_handler(conn)
DATABASE_HANDL.first_time_install()

DAYS_TO_LOOK_AHEAD = 7  # leave this at 7
TABLE_COLUMNS = ["latitude","longitude","last_time_updated","raw_api_data"]


class RequestInvalid(Exception):
  def __init__(self, errorMessage):
    super().__init__(errorMessage)

def get_datetime() -> str:
  """returns yy:mm:dd hr:min:sec
  will be used for logging.\n
  get_datetime()[:10] -> for just the date
  get_datetime()[11:] -> for just the time"""
  return str(datetime.now())[:-7]

def call_api(latitude:float, longitude:float) -> dict:
    """will assume that the database has already been checked.
    this just calls a weather API and returns the json."""
    current_date = get_datetime()[:10]
    current_date_obj:datetime = datetime.strptime(current_date, "%Y-%m-%d")

    end_date = str(current_date_obj + timedelta(days=DAYS_TO_LOOK_AHEAD))[:10]

    url = "http://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "weathercode",
            "windspeed_10m_max"
        ],
        "hourly": ["visibility"],
        "timezone": "auto",
        "start_date": current_date,
        "end_date": end_date
    }
    # can add this for unix timestamp instead of datetime stuff
    # "timeformat": "unixtime",

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch forecast")
        print(response.__dict__)  # very verbous logging can remove
        raise RequestInvalid(f"Invalid request sent, status code: {response.status_code}")

def get_usefull_information_from_api(latitude, longitude, api_data:dict) -> list[dict]:
    daily = api_data["daily"]
    hourly_visibility = api_data["hourly"]["visibility"]
    print(f"{DAYS_TO_LOOK_AHEAD}-Day Forecast for lat={latitude}, lon={longitude}")

    cleaned_data = []

    data_day = None
    total_day_vis = []
    current_day_vis = []
    for i in range(len(hourly_visibility)):
        if data_day is None:
            data_day = api_data["hourly"]["time"][i][8:10]

        elif data_day != api_data["hourly"]["time"][i][8:10]:
            #when a differnt day is detected
            data_day = api_data["hourly"]["time"][i][8:10]
            total_day_vis.append(current_day_vis)
            current_day_vis = []

        current_day_vis.append(hourly_visibility[i])
        
        if i == 0:
            total_day_vis.append(current_day_vis)

    for i in range(len(daily["time"])):
        avg_temp = round(api_data["daily"]["temperature_2m_max"][i] + api_data["daily"]["temperature_2m_min"][i] / 2,2)  # in F, rounds to 2dp
        precipitation_sum = daily["precipitation_sum"][i]  # in mm
        day = daily["time"][i]
        weather_code = daily["weathercode"][i]
        weather_desc = weather_code_lookup.weather_codes[weather_code]
        daily_avg_visibility = sum(total_day_vis[i]) / len(total_day_vis[i])
        cleaned_data.append({"day":day,"avg_temp":avg_temp,"weather_desc":weather_desc,"precipitation_sum":precipitation_sum,"daily_avg_visibility":daily_avg_visibility})
    
    return cleaned_data

@APP.route("/", methods = ["GET","POST"])
def main_page():
    #try to use as many try and excepts as possible as its vital for the server not to crash
    # if a error happens 'skip' will go True and then the client should be given the basic index.html
    skip = False

    if request.method == "POST":
        try:
            #print("this to dict: ",request.form.to_dict()) for all given keys/values
            client_latitude:float = min(max(float(request.form["latitude"]),-90),90)
            client_longitude:float = min(max(float(request.form["longitude"]),-180),180)
        except:
            skip = True
            print(request.__dict__)
            print(f"[{get_datetime()}]client sent a invalid packet, serving basic page")
        
        if not skip:
            print("0")
            should_api_call:bool = DATABASE_HANDL.check_if_api_call(client_latitude, client_longitude)
            print("THIS should_api_call",should_api_call)
            if should_api_call:
                print("1 - calling api")
                api_response = call_api(client_latitude, client_longitude)
                print("2 - get_usefull_information_from_api")
                
                try:
                    data = get_usefull_information_from_api(client_latitude, client_longitude, api_response)
                except Exception as e:
                    print("something wrong with filtering the  raw_api data:",e)
                    print("serving basic page to user")
                    skip = True

                if not skip:
                    print("3 - save_data")

                    print("data looks like",data)
                    DATABASE_HANDL.save_data(data,client_latitude,client_longitude)
                    print("4 - saved data")
                    print("big boy results - ",DATABASE_HANDL.run_sql_command("SELECT * FROM weather_api_logs;"))
            
            else:  # getting the data
                dictionary_saved_data = {}

                all_days_columns = []

                for i in range(DATABASE_HANDL.days_to_store):
                    for j in range(len(database_handler.EXPECTED_COLUMNS)):
                        column_with_day = f"day_{i}_{database_handler.EXPECTED_COLUMNS[j]}"
                        all_days_columns.append(column_with_day)


                saved_data = DATABASE_HANDL.run_sql_command(f"SELECT {','.join(all_days_columns)} FROM weather_api_logs WHERE latitude={client_latitude} and longitude={client_longitude};")[0]

                # doing all this so the returned data is always list[dict]
                print("THE SAVED DATA:",saved_data)
                print("DATABASE_HANDL.days_to_store:",DATABASE_HANDL.days_to_store)
                data = []
                total_index = 0
                for i in range(DATABASE_HANDL.days_to_store):
                    print("i:",i)
                    dictionary_saved_data={}
                    for j in range(len(database_handler.EXPECTED_COLUMNS)):
                        print("j:",j)
                        columns = database_handler.EXPECTED_COLUMNS[j]
                        dictionary_saved_data[columns] = saved_data[total_index]
                        print(dictionary_saved_data)
                        total_index += 1
                    data.append(dictionary_saved_data)

                print("dictionary_saved_data: ", dictionary_saved_data)

        if not skip:
            return data

    if request.method == "GET" or skip:
        return render_template("index.html")
      

if __name__ == "__main__":
    APP.run()