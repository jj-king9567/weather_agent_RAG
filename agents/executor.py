import os
import requests
from dotenv import load_dotenv
load_dotenv()
gade_key = os.getenv("API_KEY")

class ExecutorAgent:
    def __init__(self):
        self.name = "执行者"
    def run_weather_api(self, city):
        print(f"[{self.name}] 正在通过外部网络调用高德 API，查询城市：{city}")
        url = "https://restapi.amap.com/v3/weather/weatherInfo"
        params = {"city": city, "key": gade_key}

        try:
            response = requests.get(url=url, params=params,timeout=5)
            data = response.json()
            if data.get("status")=='1' and data.get('lives'):
                life = data['lives'][0]
                return f"{life['city']}今天天气：{life['weather']},温度：{life['temperature']},湿度：{life['humidity']}%。"
            else :
                return "高德地图返回失败，查询不到这个城市的天气。"
        except Exception as e:
            return f"网络异常:{e}"
