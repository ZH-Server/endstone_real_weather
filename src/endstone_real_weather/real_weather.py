from endstone.command import Command, CommandSender
from endstone.plugin import Plugin

import requests, json, os

class RealWeather(Plugin):
    api_version = "0.5"

    def __init__(self):
        super().__init__()
        self.url: str = 'http://t.weather.sojson.com/api/weather/city/'

    def on_enable(self) -> None:
        self.save_default_config()
        self.load_config()

        if not os.path.exists("plugins/real_weather/city.json"):
            self.logger.error("Missing dependent file! Go to https://github.com/ZH-Server/endstone_real_weather read README.md at first!")

        self.server.scheduler.run_task(self, self.update_weather, delay=0, period = self.update_period * 72000)

    commands = {
        "rw": {
            "description": "Real weather command",
            "usages": ["/rw (sync|info)<action: RWAction> [city: str]"],
            "permissions": ["rw.command.rw"],
        },
    }

    permissions = {
        "rw.command.rw": {
            "desciption": "Allow users to use the /rw command",
            "default": "op",
        },
    }

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if command.name == "rw":
            
            if str(args[0]) == "sync":
                if len(args[1]) > 0:
                    if not self.sync_weather(args[1]) != "ERROR":
                        sender.send_message(f"{args[1]}'s weather: {self.sync_weather(args[1])}")
                        self.server.dispatch_command(self.server.command_sender, f"weather {self.sync_weather(args[1])}")
                        sender.send_message(f"Has synchronized {args[1]} weather")
            
            if str(args[0]) == "info":
                if len(args[1]) > 0:
                    if self.sync_weather(str(args[1])) != "ERROR":
                        sender.send_message(f"{args[1]}'s weather: {self.sync_weather(args[1])}")
        return True

    def sync_weather(self, city:str) -> str:
        f = open("plugins/real_weather/city.json", 'rb')
        city_list = json.load(f)
        city = city_list.get(city)

        if city != None:
            response = requests.get(self.url + city)

            d = response.json()
            weather=str(d['data']['forecast'][0]['type'])

            if(d['status'] == 200):
                if weather in ["小雨", "大雨", "中雨", "雪", "大雪", "小雪", "中雪"]:
                    return "rain"
                if weather in ["暴雨", "大暴雨", "中暴雨", "台风", "暴雪", "大暴雪", "中暴雪", "冰雹"]:
                    return "thunder"
                else:
                    return "clear"
        else:
            return "ERROR"

    def update_weather(self):
        self.server.dispatch_command(self.server.command_sender, f"weather {self.sync_weather(self.city)} {self.update_period}")

    def load_config(self) -> None:
        self.city = self.config["city"]
        self.update_period = self.config["update_period"]
