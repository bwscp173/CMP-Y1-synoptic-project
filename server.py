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

#custom imports
import database_handler
import weather_code_lookup

APP = Flask(__name__)
conn = database_handler.setup_conn("weather_api_logs.db")
if conn == None:
    print("cannot connect to the database")
    exit(-1)
DATABASE_HANDL= database_handler.database_handler(conn)
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

def call_api(latitude:float, longitude:float):
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
        #daily_visibility = hourly_visibility / len(hourly_visibility)
        avg_temp = api_data["daily"]["temperature_2m_max"][i] + api_data["daily"]["temperature_2m_min"][i] / 2  # in Celcius
        precipitation_sum = daily["precipitation_sum"][i]  # in mm
        day = daily["time"][i]
        weather_code = daily["weathercode"][i]
        weather_desc = weather_code_lookup.weather_codes[weather_code]
        daily_avg_visibility = sum(total_day_vis[i]) / len(total_day_vis[i])
        print(f"\nday {day}")
        print("avg temp:",avg_temp)
        print(f"Weather Code: {weather_code}")  # https://www.meteomatics.com/en/api/available-parameters/weather-parameter/general-weather-state/
        print(f"Weather Desc: {weather_desc}")
        print(f"Precipitation: {precipitation_sum} mm")
        print("daily_avg_visibility:",daily_avg_visibility)
        cleaned_data.append({"day":day,"avg_temp":avg_temp,"weather_desc":weather_desc,"precipitation_sum":precipitation_sum,"daily_avg_visibility":daily_avg_visibility})
    
    return cleaned_data

@APP.route("/", methods = ["GET","POST"])
def main_page():
    #try to use as many try and excepts as possible as its vital for the server not to crash
    # if a error happens 'skip' will go True and then the client should be given the basic index.html
    skip = False

    if request.method == "POST":
        try:
            client_latitude:float = min(max(float(request.form.get("latitude")),-90),90)
            client_longitude:float = min(max(float(request.form.get("longitude")),-180),180)
        except:
            skip = True
            print(f"[{get_datetime()}]client sent a invalid packet, serving basic page")
        
        if not skip:
            api_response = call_api(client_latitude, client_longitude)
            data = get_usefull_information_from_api(client_latitude, client_longitude, api_response)
            try:
                pass
            except:
                skip = True
                print(f"[{get_datetime()}]something went wrong with the api call, serving basic page")
        
        if not skip:
            return data

    if request.method == "GET" or skip:
        return render_template("index.html")
      

if __name__ == "__main__":
    print(f"[{get_datetime()}]connecting to database")
    conn = database_handler.setup_conn("weather_api_logs.db")
    if conn == None:
        print("cannot connect to the database")
        exit(-1)


    database_handl = database_handler.database_handler(conn)
    #database_handl.set_up_database()

    print("all data from db:")
    database_handl.database_cursor.execute(f"SELECT * FROM weather_api_logs;")
    print(database_handl.database_cursor.fetchall())

    #print("deleting the table for fresh db")  # CAN REMOVE THIS LINE
    #database_handl.database_cursor.execute("DROP TABLE IF EXISTS weather_api_logs;")  # CAN REMOVE THIS LINE

    #database_handl.first_time_install()  # first time set up stuff like creating the trigger functions and ddl

    lat = 26.2056
    long = 28.0337

    print("all data from db:")
    database_handl.database_cursor.execute(f"SELECT * FROM weather_api_logs;")
    print(database_handl.database_cursor.fetchall())

    should_api_call:bool = database_handl.check_if_api_call(lat, long)
    print("should_api_call: ", should_api_call)
    

    APP.run()