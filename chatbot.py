from google import genai
import sys
client = genai.Client(api_key='AIzaSyC2z6JrSJiz2CfbACivW4l8b07wm_Ou3ZY')
 
#how to setup a chatbot
chat = client.chats.create(model="gemini-2.5-flash")
 
#Loop till user enters "quit"    
while True:
    query = input("User (Enter 'quit' to End the chat session): ")
    if query.upper() == "QUIT":
        chathistory = input("Do you want to print CHAT History? ")
        chathistory = chathistory.upper()
        if (chathistory == "Y" or chathistory == "YES"):
            print("Bye.")
            print("MESSAGE HISTORY")
            for message in chat.get_history():
                print(f'role - {message.role}',end=": ")
                print(message.parts[0].text)
        print("Bye.")
        sys.exit(0)
    #print("USER: ", query)
    response = chat.send_message(query)
    print("MODEL: ", response.text)