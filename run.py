import os
import time
import subprocess
import webbrowser
from threading import Thread
#from app.web import main as web
from core.cpe import cpe
from db import init_db

if __name__ == "__main__":
    print(
        r"""
     ______   __  __     ______     ______     ______     ______      ______     ______     ______     __   __    
    /\__  _\ /\ \_\ \   /\  == \   /\  ___\   /\  __ \   /\__  _\    /\  ___\   /\  ___\   /\  __ \   /\ "-.\ \   
    \/_/\ \/ \ \  __ \  \ \  __<   \ \  __\   \ \  __ \  \/_/\ \/    \ \___  \  \ \ \____  \ \  __ \  \ \ \-.  \  
       \ \_\  \ \_\ \_\  \ \_\ \_\  \ \_____\  \ \_\ \_\    \ \_\     \/\_____\  \ \_____\  \ \_\ \_\  \ \_\\"\_\ 
        \/_/   \/_/\/_/   \/_/ /_/   \/_____/   \/_/\/_/     \/_/      \/_____/   \/_____/   \/_/\/_/   \/_/ \/_/ 
                                                                                                          
        v.0.0 by s0hee & rac00n                                                                                             
        """
    )

    print("🚀 Starting Threat Scanner...")
    time.sleep(1)
    print("🔎 Loading vulnerability database...")
    init_db.init_cpe_table()
    cpe.get_cpe()

    # print("🌐 Initializin web server...")
    # web_thread = Thread(target=web)
    # web_thread.daemon = True
    # web_thread.start()
    #
    # time.sleep(2)
    # webbrowser.open("http://127.0.0.1:5000")
    #
    # print("✅ Threat Scanner is ready!")
    #
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("\n👋 Have a nice day! bye...")


# todo: remove the process percentage, use nvd lib, add loading icon in the web interface, result in table, do not hitting the llm unless user click detail
