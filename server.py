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
import psycopg2  # for the databse of the most recent API call
import requests
from flask import Flask, request, jsonify, redirect, url_for, render_template, session, make_response

app = Flask(__name__)
__DAYS_TO_LOOK_AHEAD = 7  # leave this at 7


def get_datetime() -> str:
  """returns yy:mm:dd hr:min:sec
  will be used for logging.
  get_datetime()[:10] -> for just the date
  get_datetime()[11:] -> for just the time"""
  return str(datetime.now())[:-7]

class RequestInvalid(Exception):
  def __init__(self, errorMessage):
    super().__init__(errorMessage)

def call_api(latitude:float, longitude:float):
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
        "end_date": end_date
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
    if request.method == "POST":
        client_latitude:float = request.form.get("latitude")
        client_longitude:float = request.form.get("longitude")
        return call_api(client_latitude,client_longitude)

    if request.method == "GET":
        return render_template("index.html")
      

if __name__ == "__main__":
    app.run()