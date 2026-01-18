use clap::{Parser, Subcommand};
use colored::Colorize;
use tokio::{
    io::{AsyncBufReadExt, AsyncWriteExt, BufReader},
    net::{TcpListener, TcpStream},
    sync::broadcast,
};

#[derive(Parser)]
#[command(name = "chat_app")]
#[command(about = "Async Rust Chat", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {

    Server {
        #[arg(short, long, default_value_t = 8080)]
        port: u16,
    },

    Client {
        #[arg(short, long, default_value_t = String::from("127.0.0.1:8080"))]
        address: String,
        #[arg(short, long)]
        username: String,
    },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Command::Server { port } => run_server(port).await?,
        Command::Client { address, username } => run_client(&address, &username).await?,
    }

    Ok(())
}

async fn run_server(port: u16) -> Result<(), Box<dyn std::error::Error>> {
    let addr = format!("0.0.0.0:{}", port);
    let listener = TcpListener::bind(&addr).await?;
    println!("Server running on {}. Waiting for connections...", addr);

    let (tx, _rx) = broadcast::channel::<(String, std::net::SocketAddr)>(100);

    loop {
        let (mut socket, addr) = listener.accept().await?;
        let tx = tx.clone();
        let mut rx = tx.subscribe();

        tokio::spawn(async move {
            let (reader, mut writer) = socket.split();
            let mut reader = BufReader::new(reader);
            let mut line = String::new();


            let username = match reader.read_line(&mut line).await {
                Ok(0) => return, 
                Ok(_) => line.trim().to_string(),
                Err(e) => {
                    eprintln!("Failed to read username from {}: {}", addr, e);
                    return;
                }
            };
            

            println!("INFO: User '{}' connected from {}", username, addr);
            

            let _ = tx.send((format!("System: User '{}' joined the chat\n", username), addr));
            line.clear();

            
            loop {
                tokio::select! {
                    result = reader.read_line(&mut line) => {
                        match result {
                            Ok(0) => break, 
                            Ok(_) => {
                                let msg = line.clone();
                                
                                if let Err(e) = tx.send((msg, addr)) {
                                    eprintln!("Broadcast error: {}", e);
                                }
                                line.clear();
                            }
                            Err(e) => {
                                eprintln!("Error reading from {}: {}", username, e);
                                break;
                            }
                        }
                    }
                    result = rx.recv() => {
                        match result {
                            Ok((msg, sender_addr)) => {
                                
                                if sender_addr != addr {
                                    if let Err(_) = writer.write_all(msg.as_bytes()).await {
                                        break; 
                                    }
                                }
                            }
                            Err(_) => break,
                        }
                    }
                }
            }


            println!("INFO: User '{}' disconnected", username);
            let _ = tx.send((format!("System: User '{}' left the chat\n", username), addr));
        });
    }
}

async fn run_client(address: &str, username: &str) -> Result<(), Box<dyn std::error::Error>> {
    let stream = TcpStream::connect(address).await?;
    println!("Connected to server at {}. Logged in as '{}'", address, username);
    println!("Type message and press Enter. Type '/stop' to exit.");

    let (reader, mut writer) = stream.into_split();
    let username_owned = username.to_string();


    writer.write_all(format!("{}\n", username).as_bytes()).await?;


    let mut reader = BufReader::new(reader);
    let read_task = tokio::spawn(async move {
        let mut line = String::new();
        while let Ok(bytes) = reader.read_line(&mut line).await {
            if bytes == 0 { 
                println!("Server closed connection.");
                break; 
            }
            

            let trimmed = line.trim();
            if trimmed.contains(&format!("@{}", username_owned)) {
                println!("{}", trimmed.green().bold());
            } else {
                println!("{}", trimmed);
            }
            line.clear();
        }
    });


    let username_owned = username.to_string();
    let stdin = tokio::io::stdin();
    let mut stdin_reader = BufReader::new(stdin);
    let mut line = String::new();

    while let Ok(bytes) = stdin_reader.read_line(&mut line).await {
        if bytes == 0 { break; } 

        let msg_content = line.trim();


        if msg_content == "/stop" {
            println!("Closing connection...");
            break; 
        }

        if !msg_content.is_empty() {
            let msg = format!("{}: {}\n", username_owned, msg_content);
            if writer.write_all(msg.as_bytes()).await.is_err() {
                println!("Error sending message");
                break;
            }
        }
        line.clear();
    }


    read_task.abort();
    Ok(())
}