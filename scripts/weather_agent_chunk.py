import chromadb

# 1. 模拟一篇真实世界的长篇大论（大概 400 字）
long_text = """
南宁是一座充满活力的绿城，气候温和。今天的南宁天气晴朗，温度在25度左右，非常舒适，非常适合穿短袖出门散步或者去南湖公园游玩。到了明天，南宁预计会有雷阵雨，温度会下降到20度，建议大家出门带上雨伞，并增加一件薄外套。除了南宁，北京今天的天气比较恶劣，有严重的沙尘暴，PM10爆表，温度15度，绝对不建议出门或者开窗通风。而上海今天有中雨，温度20度，出行请带好雨伞，注意安全。如果你想在周末去广州，广州今天有大暴雨，温度28度，湿度极高，体感非常闷热，不太适合户外活动。最后提一句，成都今天多云转晴，温度22度，非常舒服，是个适合吃火锅的好日子。
"""


# 2. 写一个原生的切分函数（带重叠区 overlap，防止一句话被从中间切断）
def split_text(text, chunk_size, overlap):
    chunks = []     #长度    切片                   减法
    start = 0
    while start < len(text):
        # 截取从 start 到 start + chunk_size 的文本
        chunk = text[start: start + chunk_size]
               #切字片[0:80]
        chunks.append(chunk)
              #装进chunk列表里
        #  ，形成重叠  80-10 =70 从70开头，就是为了联系上下文，避免ai无法理解
        start += chunk_size - overlap
    return chunks


# 3. 连接 ChromaDB（注意：我们新建一个集合专门用来测试切分，不影响之前的）
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="chunk_test_collection")

# 4. 核心对比实验：分别用不同大小切分入库
chunk_sizes = [30, 80, 150]  # 测试：极小、中等、较大
overlap = 10  # 重叠 10 个字

for size in chunk_sizes:
    print(f"\n正在测试 Chunk Size: {size} ...")
    try:
        client.delete_collection(name=f"test_size_{size}")
        #  delete 是删除意思
    except:
        pass

    # 建个专属的小库
    temp_collection = client.create_collection(name=f"test_size_{size}")

    # 切分文本
    chunks = split_text(long_text, chunk_size=size, overlap=overlap)

    # 存入库
    ids = [f"chunk_{size}_{i}" for i in range(len(chunks))]
    temp_collection.add(documents=chunks, ids=ids)
                    #   文档内容
    print(f"--- 共切成了 {len(chunks)} 块 ---")

    # 5. 评测环节：问一个刁钻问题！
    query = "南宁明天要带伞吗？"
    results = temp_collection.query(query_texts=[query], n_results=2)

    print(f"提问: {query}")
    print(f"召回的第一名内容: 【{results['documents'][0][0]}】")

    if "带伞" in results['documents'][0][0] or "雨" in results['documents'][0][0]:
        print(" 召回成功！找对段落了。")
    else:
        print(" 召回失败！切得太碎，语义丢失了。")