from py2neo import Graph
import numpy as np
from sentence_transformers import SentenceTransformer

# 加载编码模型
# model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
#model = SentenceTransformer(r"E:\code\paraphrase-multilingual-MiniLM-L12-v2")
model_path = "E:\code\paraphrase-multilingual-MiniLM-L12-v2"  # 替换为你的本地模型路径
model = SentenceTransformer(model_path)

# 查询接口函数：基于关键字模糊匹配 -> 匹配相似节点
def retrieve_subgraph_by_keyword(event_list, top_k=5):
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "123123"))  # 修改密码

    matched_nodes = set()
    for event in event_list:
        query = """
        MATCH (n)
        WHERE n.name =~ $pattern
        RETURN n.name AS node_name
        LIMIT $top_k
        """
        results = graph.run(query, pattern=f".*{event}.*", top_k=top_k).data()
        for record in results:
            matched_nodes.add(record["node_name"])

    return list(matched_nodes)


# 查询接口函数：基于嵌入向量相似度匹配 -> 匹配相似节点
def retrieve_subgraph_by_embedding(event_list, top_k=5):
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "123123"))  # 修改密码

    # 获取所有节点名称
    query = """
    MATCH (n)
    RETURN n.name AS node_name
    """
    results = graph.run(query).data()
    all_nodes = [record["node_name"] for record in results]

    # 编码所有节点名称
    node_embeddings = model.encode(all_nodes)

    # 编码事件列表
    event_embeddings = model.encode(event_list)

    # 计算相似度
    similarities = np.dot(node_embeddings, event_embeddings.T) / (
            np.linalg.norm(node_embeddings, axis=1)[:, np.newaxis] * np.linalg.norm(event_embeddings, axis=1)
    )

    # 获取每个事件的 top_k 相似节点
    top_indices = np.argsort(-similarities, axis=0)[:top_k, :].T
    matched_nodes = set()
    for indices in top_indices:
        for idx in indices:
            matched_nodes.add(all_nodes[idx])

    return list(matched_nodes)


# 查询相似节点所在的子图
def get_subgraphs_by_text_id(node_name_list, graph):
    # 查询所有相关节点及其文本编号
    query = """
    MATCH (n)
    WHERE n.name IN $node_names
    WITH n.`文本编号` AS text_id, collect(n) AS nodes
    RETURN text_id, nodes
    ORDER BY text_id
    """
    results = graph.run(query, node_names=node_name_list).data()

    # 合并相同文本编号的子图
    subgraphs = {}
    for record in results:
        text_id = record["text_id"]
        nodes = record["nodes"]
        if text_id not in subgraphs:
            subgraphs[text_id] = {"nodes": set(), "triples": []}
        for node in nodes:
            subgraphs[text_id]["nodes"].add(node["name"])

        # 查询这些节点的所有关系
        for node in nodes:
            query_triples = """
            MATCH (n)-[r]->(m)
            WHERE n.name = $node_name OR m.name = $node_name
            RETURN n.name AS head, type(r) AS relation, m.name AS tail
            """
            triples = graph.run(query_triples, node_name=node["name"]).data()
            for triple in triples:
                subgraphs[text_id]["triples"].append(triple)

    # 将子图转换为列表形式输出
    subgraph_list = []
    for text_id, subgraph in subgraphs.items():
        subgraph_list.append({
            "text_id": text_id,  # 这里 text_id 是字符串类型
            "nodes": list(subgraph["nodes"]),
            "triples": subgraph["triples"]
        })

    return subgraph_list


# 迭代式筛选
def iterative_filtering(event_list, top_k=5):
    # 初始化 Neo4j 连接
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "123123"))  # 修改密码

    # 初步筛选：基于关键字模糊匹配
    keyword_matched_nodes = retrieve_subgraph_by_keyword(event_list, top_k=top_k)
    # 初步筛选：基于嵌入向量相似度匹配
    embedding_matched_nodes = retrieve_subgraph_by_embedding(event_list, top_k=top_k)

    # 合并两种方法的结果，去重
    matched_nodes = list(set(keyword_matched_nodes + embedding_matched_nodes))

    # 获取初步筛选出的子图
    candidate_subgraphs = get_subgraphs_by_text_id(matched_nodes, graph)

    print(f"初始候选池：{len(candidate_subgraphs)} 个子图")
    for subgraph in candidate_subgraphs:
        print(f"文本编号：{subgraph['text_id']}")
        print(f"节点：{subgraph['nodes']}")
        print(f"三元组：{subgraph['triples']}")
        print("-" * 50)

    # 进一步筛选：基于关键字和向量相似度匹配
    for i, event in enumerate(event_list, start=1):
        print(f"第 {i} 轮筛选，当前事件：{event}")

        # 用于存储通过筛选的子图
        filtered_subgraphs = []

        # 遍历当前候选池中的每个子图
        for subgraph in candidate_subgraphs:
            # 获取子图中所有节点的名称
            node_names = subgraph["nodes"]

            # 先执行关键字模糊匹配
            keyword_matched = any(event in node_name for node_name in node_names)
            if keyword_matched:
                filtered_subgraphs.append(subgraph)
                continue

            # 如果关键字匹配失败，再执行向量相似度匹配
            node_embeddings = model.encode(node_names)
            event_embedding = model.encode([event])[0]
            similarities = np.dot(node_embeddings, event_embedding) / (
                    np.linalg.norm(node_embeddings, axis=1) * np.linalg.norm(event_embedding)
            )
            if np.any(similarities > 0.8):  # 阈值可以根据需要调整
                filtered_subgraphs.append(subgraph)

        # 更新候选池
        candidate_subgraphs = filtered_subgraphs

        # 打印当前轮次筛选后的子图
        print(f"第 {i} 轮筛选后，剩余子图数量：{len(candidate_subgraphs)}")
        for subgraph in candidate_subgraphs:
            print(f"文本编号：{subgraph['text_id']}")
            print(f"节点：{subgraph['nodes']}")
            print(f"三元组：{subgraph['triples']}")
            print("-" * 50)

    # 获取最终筛选出的子图对应的完整节点集合
    final_subgraphs = []
    for subgraph in candidate_subgraphs:
        text_id = subgraph["text_id"]
        query = """
        MATCH (n)
        WHERE n.`文本编号` = $text_id
        RETURN n.name AS node_name
        """
        results = graph.run(query, text_id=text_id).data()
        all_nodes = [record["node_name"] for record in results]

        query_triples = """
        MATCH (n)-[r]->(m)
        WHERE n.`文本编号` = $text_id OR m.`文本编号` = $text_id
        RETURN n.name AS head, type(r) AS relation, m.name AS tail
        """
        triples = graph.run(query_triples, text_id=text_id).data()

        final_subgraphs.append({
            "text_id": text_id,
            "nodes": all_nodes,
            "triples": triples
        })

    return final_subgraphs


# 示例调用
if __name__ == "__main__":
    query_events = ["冷却水泵电机保护故障", "电机三相绕组对地短路", "电机转动卡"]
    filtered_subgraphs = iterative_filtering(query_events, top_k=5)

    print(f"最终筛选出的子图数量：{len(filtered_subgraphs)}")
    for subgraph in filtered_subgraphs:
        print(f"文本编号：{subgraph['text_id']}")
        print(f"节点：{subgraph['nodes']}")
        print(f"三元组：{subgraph['triples']}")
        print("-" * 50)