import chromadb

print("正在初始化本地向量数据库...")
#client 意思是客户  persistent(持久化）+Client(客户端）
client = chromadb.PersistentClient(path="./chroma_db")
                            #path 路径   ./ 当前文件夹
#意思就是 有chormadb这个库，创建 一个持久化客户端（将数据保存在硬盘上），存到这个文件夹
                                 #集合 也可理解 分类文件夹（可以创建多了collection）
collection = client.get_or_create_collection(name="jjk_knowledge")
                   #获取 或者 建立   集合        标识
#get_or_create 这是采用 幂等性 设计  避免第二场启动代码时报错（因为如果你只写create，第二次它会发现已经有重复的了）
# 3. 准备你的知识文档（这里我们先用几条天气相关的假数据测试）
documents = [
    "南宁今天天气晴朗，温度25度，非常适合出门散步。",
    "南宁明天预计有雨，温度20度，建议带伞出门。",
    "南宁是广西首府，是一座绿色的一线城市",
    "北京今天有沙尘暴，温度15度，建议留在室内关好门窗。",
    "预计明天北京天气灾害得到缓解",
    "上海今天有中雨，温度20度，出门记得带伞。",
    "上海有迪士尼，人流极多，今天门票以销售完",
    "jjk的大山档计划非常硬核，每天要学4-5小时。",
    "jjk是世界最帅的man",
    "西藏今天降雪，温度-1度，出门记得穿厚外套"
]    #序号  0 1 2 3

# 给每个文档一个唯一的编号
ids = [f"id{i}" for i in range(len(documents))]  #这里序号是 0 1 2

print("正在把文档存入知识库...")
# 4. 把文档存入数据库（Chroma 会自动把每一句话转成机器认识的“数字向量”）
collection.add(
    documents=documents,
    ids=ids
)    # 红的 documents ids 就是数据库参数
#如果 documents与ids 是独立的阶段， 所以你删除列表的东西不行，因为内容已经存入数据库了
#所以你只能用get连接   输 ： collcetion.delete(ids=["id*"])
print("✅ 文档入库成功！\n")

# ==========================================
# 下面开始模拟用户的提问
# ==========================================

# 假设用户输入了一个问题，注意：问题里没有“北京”两个字，只有“沙尘”
query_text = "今天哪里不适合出门？"
print(f"🙋‍♂️ 模拟用户提问：{query_text}")

# 5. 去数据库里找最相似的 2 条内容（这就是 RAG 的“检索 Retrieval”）
results = collection.query(
    query_texts=[query_text],
    n_results=2
)   # query（检索）  query_texts（可支持多问题）所以它要的是列表（这也是为什么 text明明是字符串要加中括号）
#n_(number的缩写） 限制数量  看到这个就是整数限制值

print("\n🔍 AI 从知识库里找出的相关内容：")
#                           这个是字典  大列表     小列表
for i, doc in enumerate(results['documents'][0]):
    print(f"  {i+1}. {doc}")  #这里并没有忽略 下标0 的数据
                             #因为 i 是默认0开始排，但是我最后 i+1 并没有动数据而是改序号而已
    #results 里面包含：{dacuments:[[全部回答]]
  #基本就是括号包括号了  distances:[[向量]]
                    #metadatas:[[元数据]]
                    #ids：[[ids(序号）]]}