import sqlite3
from datetime import datetime
from datetime import timedelta
import time

TABLE_COLUMNS = ["latitude","longitude","last_time_updated","raw_api_data"]


def setup_conn(fileName:set = "weather_api_logs.db") -> sqlite3.Connection | None:
    try:
        conn = sqlite3.Connection(fileName)
        print(f"successfully connected to the db named 'weather_api_logs.db'!")
    except FileNotFoundError:
        conn = None
    return conn

def get_datetime() -> str:
  """returns yy:mm:dd hr:min:sec
  will be used for logging.
  get_datetime()[:10] -> for just the date
  get_datetime()[11:] -> for just the time"""
  return str(datetime.now())[:-7]

class database_handler():
    def __init__(self, conn:sqlite3.Connection):
        self.conn = conn
        self.database_cursor = self.conn.cursor()
        self.api_call_freq = 60 * 10  # stores seconds. currently 10min

    def first_time_install(self):
        self.set_up_database()
        self.remove_current_triggers()
        self.create_update_trigger()

    def remove_current_triggers(self):
        """as sqlite3 does not allow 'CREATE OR REPLACE TRIGGER'
        we must delete and create the TRIGGER each time its run to ensure
        the TRIGGER function is upto date"""
        self.database_cursor.execute("DROP TRIGGER IF EXISTS auto_update_time;")

    def set_up_database(self) -> None:

        table_columns_checks = f"""
    {TABLE_COLUMNS[0]} REAL NOT NULL CHECK(90 > latitude > -90),
    {TABLE_COLUMNS[1]} REAL NOT NULL CHECK(180 > latitude > -180),
    {TABLE_COLUMNS[2]} FLOAT NOT NULL,
    {TABLE_COLUMNS[3]} TEXT,
    PRIMARY KEY (latitude, longitude)"""
        print(table_columns_checks)
        input()

        self.database_cursor.execute(f"CREATE TABLE IF NOT EXISTS weather_api_logs({table_columns_checks});")
        self.conn.commit()
        print("created the db's table")
    
    def create_update_trigger(self):
        """when ever a UPDATE statement happens on the db, the 
        'last_time_updated' gets updated"""
        self.database_cursor.execute(f"""CREATE TRIGGER auto_update_time BEFORE UPDATE
    on weather_api_logs
    BEGIN
        INSERT INTO auto_update_time
        VALUES (OLD.latitude, OLD.longitude, datetime('now'), NEW.raw_api_data);
    END;""")
        self.conn.commit()

    def run_sql_command(self, query: str):
        """runs any SQL command given onto the db only checks
        if there is a connection to the db.
        
        returns -1 if error
        returns False if nothing to return
        returns List if item(s) are found"""
        if self.conn is not None:

            try:
                self.database_cursor.execute(query)
            except Exception as e:
                print(f"error with sql command '{query}'")
                return -1

            self.conn.commit()
            
            print("fetching results:")
            try:
                return self.database_cursor.fetchall()
            except Exception:
                print("no results to fetch from that command")  # there is no need for a GUI error here
                return False


    def check_if_api_call(self, latitude: float|str, longitude: float|str):
        """checks the database for the 'last_time_updated' with latitude, longitude
        and returns True/False if the """
        self.database_cursor.execute(f"SELECT last_time_updated FROM weather_api_logs WHERE latitude={latitude} and longitude={longitude};")
        db_results = self.database_cursor.fetchone()

        try:
            db_results = float(db_results[0])  # indexing here as fetchone() returns a list
        except TypeError: # if the db is empty then trying to index at 0 will cause a type error, so there must be nothing in the db thus call the API for data
            print("check if api call ending early:",db_results)
            return True
        
        #db_time = datetime.strptime(db_results, "%Y-%m-%d %H:%M:%S").__add__(timedelta(hours=1))  # hardcoding adding 1 hr as we are in gmt+1 timezone
        current_time = time.time()  # datetime.strptime(get_datetime(), "%Y-%m-%d %H:%M:%S")

        return db_results + self.api_call_freq < current_time
    


if __name__ == "__main__":
    #this should be testing for how often the API should be called
    #if the current time > (database records timestamp + database_handl.api_call_freq) 
    print(f"[{get_datetime()}]connecting to database")
    conn = setup_conn("weather_api_logs.db")
    if conn == None:
        print("cannot connect to the database")
        exit(-1)


    database_handl = database_handler(conn)
    database_handl.set_up_database()

    lat = 26.2056
    long = 28.0337

    i=0
    database_handl.api_call_freq = 5
    while True:
        print("")
        time.sleep(3)
        should_api_call:bool = database_handl.check_if_api_call(lat, long)
        print("should_api_call: ", should_api_call)
        if should_api_call:

            results = database_handl.run_sql_command(f"SELECT last_time_updated FROM weather_api_logs WHERE latitude={lat} and longitude={long};")

            if results == []:  # if a entry for the pk already exists then update, not insert
                print("INSERTING data", time.time())
                database_handl.run_sql_command(f"INSERT INTO weather_api_logs({', '.join(TABLE_COLUMNS)}) VALUES ({lat}, {long}, {time.time()}, 'one must imagin data here');")
            else:
                print("UPDATING timestamp and data", time.time())
                database_handl.run_sql_command(f"UPDATE weather_api_logs SET last_time_updated = {time.time()} ,raw_api_data='UPDATED THE DATA HERE'")

            #api_results = call_api(lat,long)  # just imagine the API is called and the data is added
            print("UPDATING timestamp and data", time.time())
            database_handl.run_sql_command(f"UPDATE weather_api_logs SET last_time_updated = {time.time()} ,raw_api_data='UPDATED THE DATA HERE {i}'")


        print("all data from db:")
        print(database_handl.run_sql_command(f"SELECT * FROM weather_api_logs;"))
        i+=1