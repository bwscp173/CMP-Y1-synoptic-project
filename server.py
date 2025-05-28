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
import threading
from datetime import datetime
from datetime import timedelta
import json
import socket
import sys

def get_datetime() -> str:
  """returns yy:mm:dd hr:min:sec
  will be used for logging.
  get_datetime()[:10] -> for just the date
  get_datetime()[11:] -> for just the time"""
  return str(datetime.now())[:-7]

class RequestInvalid(Exception):
  def __init__(self, errorMessage):
    super().__init__(errorMessage)

class ThreadedClientConnection:
    def __init__(self,clientSocket:socket):
        self.clientSocket = clientSocket
        self.__DAYS_TO_LOOK_AHEAD = 7  # leave this at 7
    
    def get_coords_from_client(self) -> tuple[float,float]:
        """this function will use the socket connection to get the latitude and longitude from the client.
        expects a request like this '59.123,22.423' from the client
        TODO futher testing to see if it would be logical to return a tuple with strings
        TODO error checking"""
        data:str = self.clientSocket.recv(1024).decode()  # TODO limit the number of bytes we will recieve
        
        #doing the  '.replace('\x00').replace('\x0e')' as the java client is using a zero padded buffer 
        data = data.replace('\x00','').replace('\x0e','').split(",")
        client_location = (data[0],data[1])  # using a tuple as it is faster then a list and safer as its immutable
        return client_location

    def handle_client(self):
        """this is the main function of this class
        it will take inputs from the client and call the api and send back
        the correct information while updating a database along the way for the most
        recent weather reports to send out."""
        print("["+get_datetime()+"]{threadId:",threading.get_ident(),"} is active")
        print("["+get_datetime()+"]{threadId:",threading.get_ident(),"} getting client coords")
        client_location = self.get_coords_from_client()

        print("["+get_datetime()+"]{threadId:",threading.get_ident(),"} calling api")
        api_json_data = self.call_api(client_location[0],client_location[1])

        print("["+get_datetime()+"]{threadId:",threading.get_ident(),"} keeping the imporant information")
        self.get_important_information_from_api(api_json_data)

        print("["+get_datetime()+"]{threadId:",threading.get_ident(),"} sending client data")

        print("["+get_datetime()+"]{threadId:",threading.get_ident(),"} is now free")

    def call_api(self,latitude, longitude):
        current_date = get_datetime()[:10]
        current_date_obj:datetime = datetime.strptime(current_date, "%Y-%m-%d")

        end_date = str(current_date_obj + timedelta(days=self.__DAYS_TO_LOOK_AHEAD))[:10]

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

    def get_important_information_from_api(self,json_reponse:json) -> None:
       """will talk about this with the group about what information is important"""
       print("json_response: ",json_reponse)

    def send_client_weather_report(self) -> None:
       self.clientSocket.send("close your self NOW!".encode())

    def end_thread(self):
       """will sys.exit() the thread to close it"""
       sys.exit()




if __name__ == "__main__":
    port = 4545
    host = "127.0.0.1"
    HOW_MANY_CLIENTS_AT_ONCE = 5  # 1 thread per active client so dont make this number super high like 100

    server_socket = socket.socket()
    server_socket.bind((host, port))

    server_socket.listen(HOW_MANY_CLIENTS_AT_ONCE)

    conn:socket
    all_possible_threads = []  # storing each thread so i can close them if a error from a higher scope happens

    for _ in range(5):
        try:
            print("waiting for client")
            conn, address = server_socket.accept()
            print(f"accepted client on ip {address}")

            client_connection = ThreadedClientConnection(conn)
            
            server_thread = threading.Thread(target=client_connection.handle_client)
            all_possible_threads.append(server_thread)
            server_thread.start()

        except Exception as e:
           print(f"[{get_datetime()}]an error has occured: {e}")

           print(f"[{get_datetime()}]closing all possible threads")
           for i in range(len(all_possible_threads)):
                try:
                    all_possible_threads[i].end_thread()
                except:
                 pass