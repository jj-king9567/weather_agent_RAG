import chromadb

from sentence_transformers import CrossEncoder
import os
os.environ["HF_ENDPOINT"] ="https://hf-mirror.com"
# 1. 连接你的本地向量库
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("jjk_knowledge")

reranker = CrossEncoder(r'D:\Weather_Agent\models\models\BAAI--bge-reranker-base\snapshots\master')

# 3. 把你刚刚用的 10 道地狱级测试题复制过来！
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
count_rerank = 0

print(f"开始 RAG + Rerank 终极测试(2.0)，共 {len(test_cases)} 道题...\n")

for i, case in enumerate(test_cases):
    query = case["question"]
    expeced = case["expeced_keyword"]

    # 第一步：粗排
    results = collection.query(query_texts=[query], n_results=3)
    retrieved_docs = results['documents'][0]

    if not retrieved_docs:
        continue
    baseline = retrieved_docs[0]
    # pairs 配对  这个是推导式，将问题把这篇每项拿出来绑成一对
    pairs = [[query, doc] for doc in retrieved_docs]
    scores = reranker.predict(pairs)
    # predict 预测  给相似的打分

    # 第三步：根据分数重新排序（降序）  #这个zip，会把括号里面（列表）数据一一对应绑起来    lambda 匿名函数     取第0个元素
    doc_score_pairs = sorted(zip(scores, retrieved_docs), key=lambda x: x[0], reverse=True)
                    #sorted 排序函数 把乱序的数据按你要求排好            key 排序的依据  这个x是每一对绑好的数据       从大到小
    best_doc = doc_score_pairs[0][1]
    best_score = doc_score_pairs[0][0]
    score=0.1
    if expeced in best_doc :
        count_rerank += 1
        if best_score > score:
            print(f" 第{i + 1}题命中 (得分:{best_score:.2f}): {query} ,得：{best_doc}")
        else:
            print(f"第{i + 1}题命中,得：{baseline}")
    else:
        print(f" 第{i + 1}题未命中 (得分:{best_score:.2f}): {query}")
        print(f"   期待找到: {expeced}")
        print(f"   实际重排Top-1: {best_doc}\n")

hit_rate_rerank = (count_rerank / len(test_cases)) * 100
print(f"\n==================================")
print(f" 优化后成绩单 (RAG + Rerank)")
print(f"当前 Top-1 召回率: {hit_rate_rerank}%")
print(f"==================================")