class PlannerAgent:
    def __init__(self):
        self.name = "外设大脑"

    def analyze(self, user_query):
        print(f"[{self.name}] 收到问题：{user_query}，正在思考...")
                               #先默认给个unkown（随便都得）
        task_sachma ={"action":"unkown",
                      "target":"",
                      "query_text":user_query}
                                    #这个是变量（value）值可以不用加“”
        if "天气" in user_query:
            task_sachma["action"] = "execute_weather"

            # 升级版：写一个简单的地名提取器（虽然还是很土，但比写死强多了）
            # 只要句子里有这几个城市，就把它切出来
            known_cities = ["南宁", "北京", "郑州", "上海", "广州", "成都", "西藏", "崇左"]
            found_city = "北京"  # 默认兜底

            for city in known_cities:
                if city in user_query:
                    found_city = city
                    break

            task_sachma["target"] = found_city
        elif "帅" in user_query or "计划" in user_query:
            task_sachma["action"] = "retrieve_knowledge"

        print(f"[{self.name}] 任务拆解完毕，生成标准工单：{task_sachma}")
        return task_sachma
