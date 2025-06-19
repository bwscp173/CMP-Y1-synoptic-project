import sqlite3
from datetime import datetime
from datetime import timedelta
import time

TABLE_COLUMNS = ["latitude","longitude","last_time_updated","raw_api_data"]
EXPECTED_COLUMNS = ['avg_temp', 'daily_avg_visibility', 'day', 'weather_desc', 'precipitation_sum']

def setup_conn(fileName:set = "weather_api_logs.db") -> sqlite3.Connection | None:
    try:
        #setting check_same_thread=False, as when this is imported it counts as a differnt thread
        conn = sqlite3.Connection(fileName, check_same_thread=False)
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
    def __init__(self, conn:sqlite3.Connection, days_to_store:int = 7):
        self.conn = conn
        self.database_cursor = self.conn.cursor()
        self.api_call_freq = 60 * 10  # stores seconds. currently 10min
        self.days_to_store = days_to_store + 1 # the +1 to account for the current day so it gets the next 7 days not 6. 
        self.cursor = conn.cursor()

    def first_time_install(self):
        self.set_up_database()
        self.remove_current_triggers()
        self.create_update_trigger()

    def remove_current_triggers(self):
        """as sqlite3 does not allow 'CREATE OR REPLACE TRIGGER'
        we must delete and create the TRIGGER each time its run to ensure
        the TRIGGER function is upto date"""
        self.database_cursor.execute("DROP TRIGGER IF EXISTS auto_update_time;")
        self.conn.commit()

    def set_up_database(self) -> None:
        """creates the table"""

        # it will be labed clearly as well so like:
        # day_0_avg_temp
        # day_1_avg_temp
        # day_2_avg_temp
        all_days_columns = []
        for i in range(self.days_to_store):
            for j in range(len(EXPECTED_COLUMNS)):
                column_with_day = f"day_{i}_{EXPECTED_COLUMNS[j]}"
                all_days_columns.append(column_with_day)

        table_columns_checks = f"""
    latitude REAL NOT NULL CHECK(90 > latitude > -90),
    longitude REAL NOT NULL CHECK(180 > latitude > -180),
    last_time_updated FLOAT NOT NULL,
    {','.join(all_days_columns)},
    PRIMARY KEY (latitude, longitude)"""
        print(all_days_columns)

        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS weather_api_logs({table_columns_checks});")
        self.conn.commit()
        print("created the db's table")
    
    def create_update_trigger(self):
        """when ever a UPDATE statement happens on the db, the 
        'last_time_updated' gets updated to the current time"""
        self.database_cursor.execute(f"""CREATE TRIGGER auto_update_time BEFORE UPDATE
    on weather_api_logs
    FOR EACH ROW
    BEGIN
        UPDATE weather_api_logs
        set last_time_updated=unixepoch()
        WHERE OLD.latitude = latitude AND longitude = OLD.longitude;
    END;""")
        #unixepoch() returns the unix timestamp
        self.conn.commit()

    def create_insert_trigger(self):
        """a simple trigger function to set the 'last_time_updated' to a unix timestamp"""
        #         self.database_cursor.execute("""CREATE TRIGGER insert_with_time BEFORE INSERT
        # ON weather_api_logs
        # BEING
        #     INSERT INTO weather_api_logs()

        # """)
        pass

    def run_sql_command(self, query: str, params=""):
        """runs *any* SQL command given onto the db only checks
        if there is a connection to the db. has better error handling then a regular
        execute command
        
        returns -1 if error
        returns None if nothing to return
        returns List if item(s) are found"""
        if self.conn is not None:
            try:
                if params:
                    self.database_cursor.execute(query,params)
                else:
                    self.database_cursor.execute(query)
            except sqlite3.OperationalError as e:
                print(f"[run_sql_command][error]with sql command '{query}'")
                print(e)
                return -1
            except sqlite3.ProgrammingError as e:
                print(f"[run_sql_command][error]with sql command '{query}',{params}")
                print(e)
                return -1

            self.conn.commit()

            if query.lstrip()[:6].upper() != "SELECT":
                # if query is not a select statement, then there is no need to fetch all
                return None
            
            try:
                return self.database_cursor.fetchall()
            except Exception as e:
                print(f"[run_sql_command][error] {e}")
                # no results to fetch from that command
                return None

    def check_if_api_call(self, latitude: float|str, longitude: float|str):
        """checks the database for the 'last_time_updated' with latitude, longitude
        and returns True/False if enough time has passed
        use '.api_call_freq = ??' to change how often the api should then be requested
        to update the data"""
        self.database_cursor.execute(f"SELECT last_time_updated FROM weather_api_logs WHERE latitude={latitude} and longitude={longitude};")
        db_results = self.database_cursor.fetchone()

        try:
            db_results = float(db_results[0])  # indexing here as fetchone() returns a list
        except TypeError: # if the db is empty then trying to index at 0 will cause a type error, so there must be nothing in the db thus call the API for data
            print("[check_if_api_call]returning early db is empty for that pk")
            return True
        
        #db_time = datetime.strptime(db_results, "%Y-%m-%d %H:%M:%S").__add__(timedelta(hours=1))  # hardcoding adding 1 hr as we are in gmt+1 timezone
        current_time = time.time()  # datetime.strptime(get_datetime(), "%Y-%m-%d %H:%M:%S")
        #print("diff in time:",current_time - db_results)

        return db_results + self.api_call_freq < current_time
    
    def save_data(self,api_data:list[dict],latitude:float,longitude:float):
        """
        
        returns -1 when latitude or longitude are not floats"""
        print("one must imagin saving the api_data")
        if type(latitude) != float or type(longitude) != float:
            return -1
        should_api_call:bool = self.check_if_api_call(latitude, longitude)
        print("should_api_call: ", should_api_call)
        if True:  # should_api_call:

            results = self.run_sql_command(f"SELECT last_time_updated FROM weather_api_logs WHERE latitude={latitude} and longitude={longitude};")

            if results == -1:
                print("GIANT ERROR OMG RESULTS IS -1")
                return -1

            all_days_columns = []
            all_days_values = []

            for i in range(self.days_to_store):
                for j in range(len(EXPECTED_COLUMNS)):
                    column_with_day = f"day_{i}_{EXPECTED_COLUMNS[j]}"
                    all_days_columns.append(column_with_day)
                    if EXPECTED_COLUMNS[j] in ["weather_desc","day"]:
                        day_value =  f"'{str(api_data[i][EXPECTED_COLUMNS[j]])}'"
                    else:
                        day_value = str(api_data[i][EXPECTED_COLUMNS[j]])
                    all_days_values.append(day_value)
            
            #print("all day columns:",all_days_columns)

            if results == []:  # if a entry for the pk already exists then update, not insert
                print(f"[{get_datetime()}]INSERTING data at unix time:", time.time())
                self.run_sql_command(f"INSERT INTO weather_api_logs(latitude, longitude,last_time_updated ,{', '.join(all_days_columns)}) VALUES ({latitude}, {longitude}, {time.time()}, {','.join(all_days_values)});")
            else:

                update_both_column_value = ""
                for i in range(len(all_days_columns)):
                    update_both_column_value += f"{all_days_columns[i]} = {all_days_values[i]},"

                update_both_column_value = update_both_column_value[:-1]  # [:-1] to remove the , at the end

                print(f"[{get_datetime()}]UPDATING data at unix time:", time.time())
                self.run_sql_command(f"UPDATE weather_api_logs SET {update_both_column_value} WHERE latitude={latitude} AND longitude={longitude};")
            #print(self.run_sql_command(f"SELECT latitude, longitude, last_time_updated FROM weather_api_logs;"))

if __name__ == "__main__":
    #this should be testing for how often the API should be called
    #if the current time > (database records timestamp + database_handl.api_call_freq)
    #to check if its working just see if there are both INSERT and UPDATE statements being used
    print(f"[{get_datetime()}]connecting to database")
    conn = setup_conn("weather_api_logs.db")
    if conn == None:
        print("cannot connect to the database")
        exit(-1)


    database_handl = database_handler(conn)
    database_handl.first_time_install()
    #database_handl.set_up_database()

    lat = 26.2056
    long = 28.0337

    i=0
    database_handl.api_call_freq = 5  # 5 seconds
    while True:
        print("")
        time.sleep(1.1)
        should_api_call:bool = database_handl.check_if_api_call(lat, long)
        print("should_api_call: ", should_api_call)
        if should_api_call:

            results = database_handl.run_sql_command(f"SELECT last_time_updated FROM weather_api_logs WHERE latitude={lat} and longitude={long};")

            if results == []:  # if a entry for the pk already exists then update, not insert
                print("INSERTING data", time.time())
                database_handl.run_sql_command(f"INSERT INTO weather_api_logs({', '.join(TABLE_COLUMNS)}) VALUES ({lat}, {long}, {time.time()}, 'one must imagin data here');")
            else:
                print("UPDATING timestamp and data", time.time())
                database_handl.run_sql_command(f"UPDATE weather_api_logs SET raw_api_data='UPDATED THE DATA HERE {i}' WHERE latitude={lat} AND longitude={long};")

            #api_results = call_api(lat,long)  # just imagine the API is called and the data is added
            #print("UPDATING timestamp and data", time.time())
            #database_handl.run_sql_command(f"UPDATE weather_api_logs SET last_time_updated = {time.time()} ,raw_api_data='UPDATED THE DATA HERE {i}'")


        print("all data from db:")
        print(database_handl.run_sql_command(f"SELECT * FROM weather_api_logs;"))
        i+=1