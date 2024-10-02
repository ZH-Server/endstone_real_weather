from endstone._internal.endstone_python import Command, CommandSender
from endstone.plugin import Plugin
import requests, json, os

class RealWeather(Plugin):
    api_version = "0.5"

    def __init__(self):
        super().__init__()
        self.update_period:float = 0
        self.city:str = ""
        
        self.url:str = 'http://t.weather.sojson.com/api/weather/city/'
        self.update_time:int = int(self.update_period*72000)

    def on_enable(self) -> None:
        self.save_default_config()
        self.load_config()
        
        if not os.path.exists("plugins/real_weather/city.json"): # Get city.json from repo
            city_json=requests.get("https://raw.githubusercontent.com/https://github.com/ZH-Server/endstone_real_weather/main/assets/city.json")
            if city_json.status_code == 200:
                with open("plugins/real_weather/city.json", "wb") as file:
                    file.write(city_json.content)
                self.logger.info("Dependent file is ready!")
            else:
                self.logger.error("Missing dependent file! Go to https://github.com/ZH-Server/endstone_real_weather/ read README.md first!")
                #self.plugin_loader.disable_plugin()
        
        self.server.scheduler.run_task(self, self.update_weather, delay=0, period = self.update_time)

    commands = {
        "realweather": {
            "description": "Real weather command",
            "usages": ["/realweather (sync)<action: RWAction> [city: str]"],
            "permissions": ["real_weather.command.realweather"],
        },
    }

    permissions = {
        "real_weather.command.realweather": {
            "desciption": "Allow users to use the /realweather command",
            "default": "op",
        },
    }

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if command.name == "realweather":
            if str(args[0]) == "sync":
                if len(str(args[1])) >= 0:
                    self.server.dispatch_command(self.server.command_sender, f"weather {self.sync_weather(str(args[1]))}")
                    sender.send_message(f"Has synchronized {args[1]} weather")
                else:
                    self.server.dispatch_command(self.server.command_sender, f"weather {self.sync_weather(str(self.city))}")
                    sender.send_message("Has used default config to sync weather")

    def sync_weather(self, city:str) -> str:
        f = open("plugins/real_weather/city.json", 'rb')
        cities = json.load(f)
        city = cities.get(city)
        
        if city != None:
            response = requests.get(self.url + city)

            d = response.json()
            weather=str(d['data']['forecast'][0]['type'])

            if(d['status'] == 200):
                self.logger.info(f"天气：{weather}")
                if weather in ["小雨", "大雨", "中雨", "雪", "大雪", "小雪", "中雪"]:
                    return "rain"
                if weather in ["暴雨", "大暴雨", "中暴雨", "台风", "暴雪", "大暴雪", "中暴雪", "冰雹"]:
                    return "thunder"
                else:
                    return "clear"
            else:
                self.logger.error("Network error!")
                return "ERROR"
        else:
            self.logger.error("Wrong city!")
            return "ERROR"
    
    def change_weather(self, weather:str, time: int) -> None:
        if weather != "ERROR":
            self.server.dispatch_command(self.server.command_sender, "gamerule doWeatherCycle false")
            self.server.dispatch_command(self.server.command_sender, f"weather {weather} {time}")
        else:
            self.server.dispatch_command(self.server.command_sender, "gamerule doWeatherCycle true")
            self.logger.error("Wrong weather")
    
    def update_weather(self) -> None:
        self.change_weather(self.sync_weather(str(self.city)), self.update_time)
    
    def load_config(self) -> None:
        self.city=self.config["city"]
        self.update_period=self.config["update_period"]