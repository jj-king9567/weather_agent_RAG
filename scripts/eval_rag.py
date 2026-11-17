import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("jjk_knowledge")

test_cases = [
    {"question":"南宁明天要带伞吗","expeced_keyword":"有雨"},
    {"question":"今天的北京可以开窗通风吗","expeced_keyword":"有沙尘暴"},
    {"question":"今天有雨的城市是那个","expeced_keyword":"上海"},
    {"question":"jjk计划表给人的感觉怎么样","expeced_keyword":"硬核"},
    {"question":"jjk每天学习多久","expeced_keyword":"4-5小时"},
    {"question":"我想去能穿短袖的城市","expeced_keyword":"南宁"},
    {"question":"京津冀现在有什么气象灾害","expeced_keyword":"沙尘暴"},
    {"question":"比彭于晏颜值还高的是谁","expeced_keyword":"man"},
    {"question":"那个城市需要穿厚外套","expeced_keyword":"西藏"},
    {"question":"我想去广西首都,天气如何","expeced_keyword":"25度"},
]

correct_count = 0
top_k=1
print(f"开始rag调试（1.1）共{len(test_cases)}道题，top-{top_k} 召回：\n")
for index, case in enumerate(test_cases):
    question = case["question"]     #将列表字典抽出来
    expected = case["expeced_keyword"]
    results = collection.query(
        query_texts=[question],
        n_results=top_k
    )
    retrieved_docs = results["documents"][0]
    retrieved_text = "".join(retrieved_docs)   #以为这个还是个列表， join直接把它变成字符串
    is_hit = expected in retrieved_text       #in 这个只能对字符串用
    if is_hit:
        correct_count += 1
        print(f"第{index+1}题命中，问题：{question}")
    else:
        print(f" 第{index+1}题未命中。问：{question}")
        print(f"   期待找到：{expected}")
        print(f"   实际找到：{retrieved_docs}")

# 4. 计算分数   这个是答对的题    总题目（4）
hit_rate = (correct_count / len(test_cases)) * 100
print("\n" + "="*30)
print(f" 摸底成绩单 (Baseline)")
print(f"当前 Top-{top_k} 召回率：{hit_rate:.1f}%")  # .1f  就是保留一位小数
print("="*30)