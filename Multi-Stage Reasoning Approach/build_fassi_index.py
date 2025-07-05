import numpy as np
import pickle
import faiss
from neo4j import GraphDatabase

# === 参数配置 ===
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "123123"  # ← 请替换
VECTOR_DIM = 384  # 视你的模型而定

# === 初始化Neo4j连接 ===
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# === 向量解析函数 ===
def string_to_vector(vec_str):
    if not vec_str or ";" not in vec_str:
        return None
    try:
        return np.array([float(v) for v in vec_str.split(";")], dtype="float32")
    except:
        return None

# === 加载Neo4j中所有带向量的节点 ===
def load_node_vectors(tx):
    query = "MATCH (n) WHERE exists(n.向量) RETURN n.name as name, n.向量 as vector"
    results = tx.run(query)
    names, vectors = [], []
    for record in results:
        vec = string_to_vector(record["vector"])
        if vec is not None and vec.shape[0] == VECTOR_DIM:
            names.append(record["name"])
            vectors.append(vec)
    return names, np.vstack(vectors)

# === 构建并保存向量库 ===
def build_and_save_vector_store():
    with driver.session() as session:
        print("📥 正在从 Neo4j 加载节点向量...")
        names, vectors = session.read_transaction(load_node_vectors)
        print(f"✅ 加载完成，共 {len(names)} 个节点")

    print("📦 正在构建 FAISS 向量库...")
    index = faiss.IndexFlatL2(VECTOR_DIM)
    index.add(vectors)

    print("💾 正在保存向量库和索引...")
    np.save("node_vectors.npy", vectors)
    with open("node_names.pkl", "wb") as f:
        pickle.dump(names, f)
    faiss.write_index(index, "faiss.index")
    print("✅ 所有文件已保存：node_vectors.npy, node_names.pkl, faiss.index")

# === 运行入口 ===
if __name__ == "__main__":
    build_and_save_vector_store()
