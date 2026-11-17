import chromadb
import requests
import sqlite3
from flask import Flask, render_template, request, jsonify  #flask 是制作网站应用  render_template 是渲染html页面
                      #json 是json -->字典                                            #把文件填上数据发给浏览器
import time           #request 是接收用户的请求   jsonify 就是把python字典转化成JSON格式（普通话）
import os             #os 操作系统   读取系统环境变量
from dotenv import load_dotenv   #dotenv 将 .env 文件内容注入系统‘环境变量’
from sentence_transformers import CrossEncoder
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.retriever import RetrieverAgent
from agents.reflector import ReflectorAgent

planner = PlannerAgent()
executor = ExecutorAgent()
retriever = RetrieverAgent()
reflector = ReflectorAgent()

reranker = CrossEncoder(r'./models/models/BAAI--bge-reranker-base/snapshots/master')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("jjk_knowledge")
app = Flask(__name__)   #如果他运行就变成main（主角） ，如果是别的文件就是他自己的名字
#flask在这 相当于一个中介，接收到用户请求，跑到后端拿数据，在传递
#__name__是内置变量  ，在这里翻译就是当前文件的身份是谁
conn = sqlite3.connect('weather.db')
curr = conn.cursor()
                #create table  创建一个表   if not exists 就是没有这个文件就创造
curr.execute('''CREATE TABLE IF NOT EXISTS weather (
id INTEGER PRIMARY KEY AUTOINCREMENT,
city TEXT NOT NULL,
result TEXT NOT NULL,
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
#integer 就是要求他是整数   priomary key  身份标识  autoincrement  自动递增（1-2-3）
#最后一行的 ：  timestamp (数据类型） 时间类型  剩下的别管了
conn.commit()
conn.close()
load_dotenv()    #将 .env文件 里键值对注释到环境变量来  嗯/ 能放蛮多东西的 数据库密钥，地址，redis密码
gaode_key =os.getenv("API_KEY")    ##去操作系统里寻找‘API_KEY'标签  如果没有：None

#为什么：：
# 为什么用缓存：高德天气接口有调用频率限制（免费额度更紧），而且每次请求都要联网、耗时。
# 如果 10 分钟内重复查同一个城市，每次都打 API 既慢又浪费配额。
# 用一个全局字典把“最近查过的结果”存下来，下次直接返回，省掉这次网络请求。
rag_client = chromadb.PersistentClient(path="./chroma_db")
rag_collection = rag_client.get_or_create_collection(name="jjk_knowledge")
# 缓存结构：weather_cache = { 城市名: {"ts": 存入的时间戳, "data": 结果字典} }
#没错他就是一个空字典（本身就是内存缓存）
weather_cache = {}
CACHE_TTL = 600   # 缓存有效期 600 秒 = 10 分钟（天气数据在 10 分钟内变化很小）

def get_weather(city):
    """查询天气，返回【字典】，方便前端 JSON 解析。
    返回字段：
    - success:      bool，是否成功
    - city:         str，城市名
    - weather:      str，天气（晴/多云/雨…，失败时为空字符串）
    - temperature:  str，温度
    - humidity:     str，湿度
    - db_result:    str，格式化好的文本，用于写历史记录表
    - message:      str，提示信息（成功为 'ok'，失败为具体原因）
    - from_cache:   bool，是否来自缓存（True 时只给前端展示，不写入历史记录）
    """
    city = (city or '').strip()

    # 命中条件：缓存里存在，且“现在 - 存入时间”还没超过 600 秒（没过期）
    cached = weather_cache.get(city)
    if cached and (time.time() - cached['ts']) < CACHE_TTL:
        #time.time 就是当前的时间戳（就是1970年1.1到现在的秒数）
        return {**cached['data'], 'from_cache': True}
        #这两个**是 字典分解拆开 键和值    这里就是我（自己）告诉前端是从缓存里拿的（看前端就懂了）
    url = "https://restapi.amap.com/v3/weather/weatherInfo"  #restapi 是高德后端（数据）的专线
                            #v3 是第3版接口（目前最高）     这个是information 实况信息
    params = {"city": city, "key": gaode_key}
    try:
        response = requests.get(url, params=params, timeout=5)   #这个timeout 是等待最多5秒，等完直接停
        if response.status_code == 200:
            data = response.json()    #将取到的数据 转化成python字典
            if data.get('status') == '1' and data.get('lives'):
                life = data['lives'][0]         #这段里很多变量都与高德设计有关（65-69）
                weather = life.get('weather', '')    #这个‘’，是如果没有数据返回空号
                temperature = life.get('temperature', '')
                humidity = life.get('humidity', '')
                # db_result：给历史记录表存库用的文本，保留原有展示格式
                db_result = f"城市:{life['city']},天气：{weather},温度:{temperature},湿度:{humidity}%"
                result = {
                    'success': True,
                    'city': life.get('city', city),
                    'weather': weather,
                    'temperature': temperature,
                    'humidity': humidity,
                    'db_result': db_result,
                    'message': 'ok',
                    'from_cache': False,
                }
            else:
                result = {
                    'success': False,
                    'city': city,
                    'weather': '', 'temperature': '', 'humidity': '',
                    'db_result': '',
                    'message': f"高德返回错误：{data.get('info', '未知错误')}",
                    'from_cache': False,
                }
        else:
            result = {
                'success': False,
                'city': city,
                'weather': '', 'temperature': '', 'humidity': '',
                'db_result': '',
                'message': '网络请求失败，jjk站台无法收到信号，讲述完毕！',
                'from_cache': False,
            }
    except Exception as e:
        result = {
            'success': False,
            'city': city,
            'weather': '', 'temperature': '', 'humidity': '',
            'db_result': '',
            'message': f'网络连接出现异常。原因可能是:{e}',
            'from_cache': False,
        }
    # 失败通常是暂时的（网络抖动、被限流），如果把失败也缓存 600 秒，
    # 这 10 分钟内用户每次都会拿到同一个“失败”，无法自动恢复，体验很差。 --dsh
    if result['success']:
        weather_cache[city] = {'ts': time.time(), 'data': result}
    return result
#前后端职责分离
#不写 methods 默认是 GET
@app.route('/')
def index():
    # 【修改】首页只负责渲染页面，不再处理表单 POST。      POST是传递数据的一种方式
    # 天气查询改由前端 JS 用 fetch 异步调用 /api/weather/<city>，页面不用刷新。
    return render_template('index.html')

@app.route('/api/weather/<city>')
def api_weather(city):
    """【新增】给前端 fetch 调用的 GET 接口，返回 JSON。
    例如浏览器访问 /api/weather/崇左，会返回类似：
    {"success": true, "city": "崇左", "weather": "晴", "temperature": "26", ...}
    人话：给前端看的"""
    data = get_weather(city)
    # 【修改】只有“真正联网查询成功”才写历史记录；缓存命中的结果只给前端展示，不重复入库。
    # 写库失败不影响接口返回，只打印日志，避免前端拿不到天气数据。
    if data['success'] and not data.get('from_cache'):
        try:
            with sqlite3.connect('weather.db') as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO weather (city, result) VALUES (?, ?)",
                            (data['city'], data['db_result']))
                conn.commit()
        except Exception as e:
            print("数据写入失败：", e)
    return jsonify(data)

@app.route('/history')
def history():
    search_city = request.args.get('city')
    # 【修改】变量名统一用 start_date / end_date，与表单字段名、模板变量保持一致
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    with sqlite3.connect('weather.db') as conn:
        curr = conn.cursor()
        sql = "SELECT created_at ,city,result FROM weather WHERE 1=1"
        params = []
        if search_city:
            sql += " AND city LIKE ?"
            params.append(f"%{search_city}%")
        if start_date:
            sql += " AND created_at >= ?"
            # 【修改】日期后补一个空格再拼时间，得到 "2026-11-03 00:00:00" 这种正确格式
            params.append(start_date + " 00:00:00")
        if end_date:
            # 【修改】AND 前补一个空格，避免拼成 "... ?AND created_at" 的语法错误
            sql += " AND created_at <= ?"
            params.append(end_date + " 23:59:59")
        sql += " ORDER BY id DESC"
        curr.execute(sql, tuple(params))
        rows = curr.fetchall()
        return render_template('history.html', records=rows,
                               current_city=search_city,
                               start_date=start_date, end_date=end_date)

# 为什么这里又有methods ,
    #因为它要提交数据到服务器
@app.route('/api/ask', methods=['POST'])
def ask_agent():
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({"success": False, "answer": "问题不能为空！不然浪费jjk的脑力"})

    try:
        task_ticket = planner.analyze(question)
        action = task_ticket["action"]

        result = ""
        if action == "execute_weather":
            city = task_ticket.get("target", "北京")  # 默认北京
            result = executor.run_weather_api(city)
        elif action == "retrieve_knowledge":
            query = task_ticket["query_text"]
            result = retriever.search_db(query)
        else:
            result = "抱歉，我还没写这个功能。"

        is_ok = reflector.check(result)

        if is_ok:
            return jsonify({"success": True, "answer": result})
        else:
            return jsonify({"success": False, "answer": "jjk反思了一下，觉得这个答案不靠谱，不给了。"})

    except Exception as e:
        print("Agent 脑子出错了:", e)
        return jsonify({"success": False, "answer": "服务器开小差了，请稍后再试。"})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

#笔记有误可说明更改，不代表官方知识       ----jjk
