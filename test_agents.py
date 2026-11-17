from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.retriever import RetrieverAgent
from agents.reflector import ReflectorAgent

planner = PlannerAgent()
executor = ExecutorAgent()
retriever = RetrieverAgent()
reflector = ReflectorAgent()

def chat_with_agent(user_input):
    print(f"\n================ 用户：{user_input} ================")

    # 1. 规划
    task_ticket = planner.analyze(user_input)
    action = task_ticket["action"]

    result = ""

    # 2. 串联调用
    if action == "execute_weather":
        city = task_ticket["target"]
        result = executor.run_weather_api(city)  # 走真 API
    elif action == "retrieve_knowledge":
        query = task_ticket["query_text"]
        result = retriever.search_db(query)  # 走真 RAG
    else:
        result = "抱歉，我不知道你在说什么。"

    # 3. 反思
    is_ok = reflector.check(result)

    if is_ok:
        print(f"\n👉 最终返回给用户的答案：\n{result}")


# 测试用例 1：查真实天气（走外网）
chat_with_agent("南宁今天天气怎么样？")

# 测试用例 2：查本地知识（走 RAG）
chat_with_agent("jjk帅吗？")