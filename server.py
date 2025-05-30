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


from datetime import datetime
from datetime import timedelta
import time
import sqlite3  # for the databse of the most recent API call, moved away from pgadmin as this import allows just the .db file without any login information
import requests
import database_handler
from flask import Flask, request, render_template

app = Flask(__name__)
__DAYS_TO_LOOK_AHEAD = 7  # leave this at 7


TABLE_COLUMNS = ["latitude","longitude","last_time_updated","raw_api_data"]


class RequestInvalid(Exception):
  def __init__(self, errorMessage):
    super().__init__(errorMessage)


def get_datetime() -> str:
  """returns yy:mm:dd hr:min:sec
  will be used for logging.
  get_datetime()[:10] -> for just the date
  get_datetime()[11:] -> for just the time"""
  return str(datetime.now())[:-7]

def call_api(latitude:float, longitude:float):
    """will assume that the database has already been checked.
    this just calls a weather API and returns the json."""
    current_date = get_datetime()[:10]
    current_date_obj:datetime = datetime.strptime(current_date, "%Y-%m-%d")

    end_date = str(current_date_obj + timedelta(days=__DAYS_TO_LOOK_AHEAD))[:10]

    url = "http://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
        "timezone": "auto",
        "start_date": current_date,
        "end_date": end_date,
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch forecast")
        print(response.__dict__)  # very verbous logging can remove
        raise RequestInvalid(f"Invalid request sent, status code: {response.status_code}")

@app.route("/", methods = ["GET","POST"])
def main_page():
    #try to use as many try and excepts as possible as its vital for the server not to crash
    # if a error happens 'skip' will go True and then the client should be given the basic index.html
    skip = False

    if request.method == "POST":
        try:
            client_latitude:float = request.form.get("latitude")
            client_longitude:float = request.form.get("longitude")
        except:
            skip = True
            print(f"[{get_datetime()}]client sent a invalid packet, serving basic page")
        
        if not skip:
            try:
                api_response = call_api(client_latitude,client_longitude)
            except:
                skip = True
                print(f"[{get_datetime()}]something went wrong with the api call, serving basic page")
        
        if not skip:
            return api_response

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
    

    app.run()