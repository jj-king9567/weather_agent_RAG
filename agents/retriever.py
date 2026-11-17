import chromadb
from sentence_transformers import CrossEncoder


class RetrieverAgent:
    def __init__(self):
        self.name = "资料员"
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection("jjk_knowledge")

        self.reranker = CrossEncoder(r'D:\Weather_Agent\models\models\BAAI--bge-reranker-base\snapshots\master')

    def search_db(self, query):
        print(f"[{self.name}] 正在翻阅本地知识库，查找：{query}")

        results = self.collection.query(query_texts=[query], n_results=3)
        docs = results.get('documents', [[]])[0]
                                        #放多个问题
        if not docs:
            return "知识库没有相关记录（数据库可能是空的）"

        baseline = docs[0]
        pairs = [[query, doc] for doc in docs]

        # 修正 3：这里用 self.reranker
        scores = self.reranker.predict(pairs)
        scores = [float(score) for score in scores]

        # 修正 4：zip 里面一定要用 docs，不能用 pairs！
        score_pairs = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)

        best_doc = score_pairs[0][1]
        best_score = score_pairs[0][0]

        if best_score >= 0.1:
            return best_doc
        else:
            print(f" Rerank最高分仅 {best_score:.4f}，回退到粗排结果")
            return baseline