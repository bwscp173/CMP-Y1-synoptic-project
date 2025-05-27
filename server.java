import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;
import java.time.LocalTime;


// i dont think i can set up a static IP on uni wifi so for the project we will have to type in some numbers for the client

public class server{
    public static String get_time(){
        // gets time but neatly '16:06:03' instead of '16:06:03.916445900'
        return LocalTime.now().toString().substring(0, 8);
    }

    public static void main(String args[]) throws IOException{
        int portNumber = 4545;
        
        try{
            System.out.println("started server socket");
            ServerSocket server_Socket = new ServerSocket(portNumber);
            System.out.println("opened server socket on port "+portNumber);
            System.out.println("waiting on client connection");
            Socket clientSocket = server_Socket.accept();
            DataInputStream from_client = new DataInputStream(clientSocket.getInputStream());
            DataOutputStream to_client = new DataOutputStream(clientSocket.getOutputStream());

            System.out.println("client has connected: " + clientSocket.toString());
            System.out.println("client message is: " + from_client.readUTF());
            System.out.println("sending confirmation of message.");
        
            to_client.writeUTF("we have your message!" + get_time());

            System.out.println("closing down server");
            server_Socket.close();
            from_client.close();
            to_client.close();
            System.out.println("ending server and connections");
        }
        catch(IOException e){
            System.out.println("failed to accept connection, maybe the port is already in use");
        }
    }
}