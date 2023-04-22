import os
import socket
import ssl
import time
import openai
import re
openai.api_key = "" #Insert your secret key between quotes
server = "irc.oftc.net"
port = 6697 # 6667 for non SSL
channel = '#/s/'
botnick = "Pepa"
allow_names = ["pepa", "pepe", "Pepe", "пепа", "пепе", "Пепе", "Пепа", "пипа", "Пипа", "Pepa"] #How can I contact the bot?
password = ""
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((server, port))
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
irc_ssl = context.wrap_socket(irc, server_hostname=server)
irc_ssl.send(("USER " + botnick + " " + botnick + " " + botnick + " :I am a bot!\r\n").encode())
irc_ssl.send(("NICK " + botnick + "\r\n").encode())
irc_ssl.send(("JOIN " + channel + "\r\n").encode())
prompt_base = "Roleplay as a IRC bot. Answer short as possible. Talk like a virgin in 4chan forum. Swear a lot. In russian language. Do not repeat the text if you are asked to."
conversation_history = [] #don't touch

while True:
    data = irc_ssl.recv(4096).decode('utf-8')
    print(data)  # print all data received from server to console
    if data.find("PING") != -1:
        irc_ssl.send(("PONG " + data.split()[1] + "\r\n").encode())
    elif data.find("422") != -1 or data.find("376") != -1:  # if no MOTD or end of MOTD
        irc_ssl.send(("JOIN " + channel + "\r\n").encode())
    elif data.find("PRIVMSG") != -1:
        match = re.search(r'^:(.*)!(.*)@(.*) PRIVMSG (.*) :(.*)', data)
        if match:
            user = match.group(1)
            message = match.group(5)
            if any(message.startswith(name + "") for name in allow_names):
            #if message.startswith(botnick + ""):
                #question = message.split(botnick + "")[1]
                trigger_name = next(name for name in allow_names if message.startswith(name))
                question = message.split(trigger_name + "")[1]
                conversation_history.append({"user": user, "message": question})
                while len(conversation_history) > 8:
                    conversation_history.pop(0)
                context = "".join([f"{item['user']}: {item['message']}\n" for item in conversation_history])
                prompt = f"{context}GPT-3:"

                try:
                    response = openai.Completion.create(
                        engine="text-davinci-003",  # text-curie-001 is 10x cheaper and dumber
                        #prompt=prompt,
                        prompt = f"{context}\n{prompt_base} {question}\nGPT-3:",
                        max_tokens=2048,  # may have to lower if you use curie
                        n=1,
                        stop=None,
                        temperature=0.4,  # higher = more random
                    )
                    print(response)
                    if response.choices and response.choices[0].text.strip():
                        text = response.choices[0].text.strip()
                        conversation_history.append({"user": "GPT-3", "message": text})
                        lines = (line.strip() for line in text.split("\n") if line.strip())
                        for i, line in enumerate(lines):
                            if i >= 15:
                                irc_ssl.send(f"PRIVMSG {channel} :Бля, слишком много строк.\r\n".encode())
                                break
                            prefix = " " if i == 0 else ""
                            max_chars_per_line = 256 
                            for i in range(0, len(line), max_chars_per_line):
                                chunk = line[i:i+max_chars_per_line]
                                irc_ssl.send(f"PRIVMSG {channel} :{chunk}\r\n".encode())
                except Exception as e:
                    print("Error:", str(e))
                    irc_ssl.send(f"PRIVMSG {channel} :Ошибка при обработке запроса, идите нахуй.\r\n".encode())
    time.sleep(1)
