import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

//description will get the latitude and longitude from the client, maybe the city name.
//and this server will fetch the data from API's like "https://wttr.in/norwich" and give only the needed
//information to the client

//so a client server interaction will look something like:
//client: my location is 59.123,22.423
//server: *TODO check a database for the most recent API calls*
//        *if the last API call was made 15> then make another API call to fetch a weeks worth of data and saves it to a database*
//        here is the most recent 7 day forcast
//client and server: ends connection.
//client: *saves the data from the server, and will display that data when its impossible to connect to the server*

//the minimal communication between the client/server is a priority

// i dont think i can set up a static IP on uni wifi so for the project we will have to type in some numbers for the client

// storing this so it will match the APIs reponse so i can reference this objs struct to get the api data i want.
// why cant requests be easy like they are in python
class apiStruct {
    public double latitude;
    public double longitude;
    public double generationtime_ms;
    public int utc_offset_seconds;
    public String timezone;
    public String timezone_abbreviation;
    public double elevation;
    public DailyUnits daily_units;
    public Daily daily;

    public static class DailyUnits {
        public String time;
        public String temperature_2m_max;
        public String temperature_2m_min;
        public String precipitation_sum;
        public String weathercode;
    }

    public static class Daily {
        public List<String> time;
        public List<Double> temperature_2m_max;
        public List<Double> temperature_2m_min;
        public List<Double> precipitation_sum;
        public List<Integer> weathercode;
    }
}


class ThreadedClientConnection extends Thread {
    Socket clientSocket;

    public ThreadedClientConnection(Socket clientSocket) {
        this.clientSocket = clientSocket;
    }

    public static String get_time() {
        // gets time but neatly '16:06:03' instead of '16:06:03.916445900'
        return LocalTime.now().toString().substring(0, 8);
    }

    public static void get_important_information_from_api(HttpResponse<String> api_Response) {
        // example response:
        // {"latitude":52.62,"longitude":1.2999997,"generationtime_ms":0.095367431640625,"utc_offset_seconds":3600,"timezone":"Europe/London","timezone_abbreviation":"GMT+1","elevation":22.0,"daily_units":{"time":"iso8601","temperature_2m_max":"°C","temperature_2m_min":"°C","precipitation_sum":"mm","weathercode":"wmo
        // code"},"daily":{"time":["2025-05-27","2025-05-28","2025-05-29","2025-05-30","2025-05-31","2025-06-01","2025-06-02","2025-06-03"],"temperature_2m_max":[16.5,19.0,21.6,22.0,22.4,18.8,15.7,19.2],"temperature_2m_min":[12.8,12.2,12.5,13.7,14.6,12.7,10.6,9.3],"precipitation_sum":[6.20,8.30,2.00,0.00,0.00,0.00,0.90,0.00],"weathercode":[80,95,61,3,3,3,3,45]}}
        System.out.println("in the funct");
        //apiStruct response = new ObjectMapper().readValue(api_Response.toString(), apiStruct.class);
        System.out.println("wow very cool mark");
        //System.out.println(response.latitude);
        System.out.println(api_Response.headers().allValues("date"));
        System.out.println(api_Response.body());
    }

    public static HttpResponse<String> make_weather_api_call(double latitude, double longitude) {
        int days_to_look_ahead = 7;

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        LocalDate today = LocalDate.now();
        LocalDate futureDate = today.plusDays(days_to_look_ahead);

        String current_date = today.format(formatter);
        String end_date = futureDate.format(formatter);

        System.out.println(latitude + " | " + longitude + " | " + current_date + " | " + end_date);
        // i know this line is very long but it only needs to be done once
        String url = "https://api.open-meteo.com/v1/forecast?latitude=" + latitude + "&longitude=" + longitude
                + "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&timezone=auto&start_date="
                + current_date + "&end_date=" + end_date;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .GET()
                .build();

        HttpResponse<String> response = null;
        try {
            response = HttpClient.newHttpClient().send(request, BodyHandlers.ofString());
        } catch (IOException | InterruptedException e) {
            System.out.println(e);
            e.printStackTrace();
        }
        return response;

    }

    // no args can be parsed into this function
    @Override
    public void run() {
        // try {
        System.out.println("{Thread: " + Thread.currentThread().threadId() + "} is running");
        DataInputStream from_client = null;
        DataOutputStream to_client = null;
        try {
            from_client = new DataInputStream(clientSocket.getInputStream());
            to_client = new DataOutputStream(clientSocket.getOutputStream());
        } catch (IOException ex) {
        }

        System.out.println("client has connected: " + clientSocket.toString());
        String raw_client_info = null;
        try {
            raw_client_info = from_client.readUTF();
        } catch (IOException ex) {
        }

        String[] location = new String[1]; // saving resources by only allowing 2 inputs
        location = raw_client_info.split(",");
        double latitude = Double.parseDouble(location[0]);
        double longitude = Double.parseDouble(location[1]);
        System.out.println("latitude: " + latitude);
        System.out.println("longitude: " + longitude);

        HttpResponse<String> api_response = ThreadedClientConnection.make_weather_api_call(latitude, longitude);
        ThreadedClientConnection.get_important_information_from_api(api_response);

        System.out.println("client message is: " + raw_client_info);
        System.out.println("sending confirmation of message.");

        try {
            to_client.writeUTF("we have your message!" + get_time());
        } catch (IOException ex) {
        }

        System.out.println("closing down clients connection");
        try {
            from_client.close();
            to_client.close();
        } catch (IOException ex) {
        }
        System.out.println("{Thread: " + Thread.currentThread().threadId() + "} is now free");
        // }
        // catch (Exception e) {
        // System.out.println("Exception is caught from a Thread");
        // System.out.println(e);
        // }
    }
}

public class server {
    public static String get_time() {
        // gets time but neatly '16:06:03' instead of '16:06:03.916445900'
        return LocalTime.now().toString().substring(0, 8);
    }

    public static void main(String args[]) throws IOException {
        int portNumber = 4545;
        System.out.println("started server socket");
        try (ServerSocket server_Socket = new ServerSocket(portNumber)) {
            System.out.println("opened server socket on port " + portNumber);
            boolean accept_new_clients = true;
            while (accept_new_clients) {
                System.out.println("waiting on client connection");
                Socket clientSocket = server_Socket.accept();
                System.out.println("accepted client connection");
                System.out.println("");
                ThreadedClientConnection object = new ThreadedClientConnection(clientSocket);
                object.start();
                accept_new_clients = false;
            }
        }
    }
}