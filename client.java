import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.Socket;
import java.net.UnknownHostException;
import java.time.LocalTime;


// i dont think i can set up a static IP on uni wifi so for the project we will have to type in some numbers for the client

public class client{
    public static String get_time(){
        // gets time but neatly '16:06:03' instead of '16:06:03.916445900'
        return LocalTime.now().toString().substring(0, 8);
    }
    public static void main(String[] args) {
        String hostName = "127.0.0.1";
        int portNumber = 4545;

    try {
        System.out.println("opening socket to {host: "+hostName+", portNumber: "+portNumber+"}");
        Socket server_Socket = new Socket(hostName, portNumber);
        System.out.println("opened socket");

        
        //System.out.println("waiting on users input:");
        //Scanner input_handl = new Scanner(System.in);
        //String user_input = input_handl.nextLine();

        DataInputStream from_server = new DataInputStream(server_Socket.getInputStream());
        DataOutputStream to_server = new DataOutputStream(server_Socket.getOutputStream());

        to_server.writeUTF("52.6293,1.2979");  // send over the latitude and longitude
        
        System.out.println("waiting for confirmation");
        System.out.println("confirmation from server: " + from_server.readUTF());
        System.out.println("ending connection");
        server_Socket.close();
        
    }catch(UnknownHostException e){
        System.out.println("invalid hostname given, try again or a differnt IP");
    }
    catch (IOException e) {
        System.out.println("error:"+e);
    }
    }
}