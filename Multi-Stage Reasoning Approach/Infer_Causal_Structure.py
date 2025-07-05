from py2neo import Graph

class InferenceModule:
    def __init__(self, graph_uri="bolt://localhost:7687", auth=("neo4j", "123123")):
        self.graph = Graph(graph_uri, auth=auth)

    def get_subgraph_by_text_id(self, text_id):
        """
        根据文本编号从 Neo4j 中检索对应的子图
        """
        query = f"""
        MATCH (n)-[r]->(m)
        WHERE n.`文本编号` = $text_id OR m.`文本编号` = $text_id
        RETURN n.name AS head, type(r) AS relation, m.name AS tail, n.`文本编号` AS text_id, labels(n) AS labels
        """
        results = self.graph.run(query, text_id=text_id).data()
        subgraph = {
            "text_id": text_id,
            "nodes": set(),
            "triples": [],
            "labels": {}
        }
        for record in results:
            subgraph["nodes"].add(record["head"])
            subgraph["nodes"].add(record["tail"])
            subgraph["triples"].append({
                "head": record["head"],
                "relation": record["relation"],
                "tail": record["tail"]
            })
            subgraph["labels"][record["head"]] = record["labels"]
            subgraph["labels"][record["tail"]] = record["labels"]
        subgraph["nodes"] = list(subgraph["nodes"])
        return subgraph

    def infer_causal_structure(self, subgraph):
        """
        根据子图的节点标签和三元组判断因果结构
        """
        causal_structures = []

        # 提取节点标签
        node_labels = subgraph["labels"]
        fault_causes = [node for node, labels in node_labels.items() if "故障原因" in labels]
        common_causes = [node for node, labels in node_labels.items() if "共同原因" in labels]
        fault_phenomena = [node for node, labels in node_labels.items() if "故障现象" in labels]

        # 并发独立根因
        if len(fault_causes) > 1 and all(node_labels[fault_cause] == ["故障原因"] for fault_cause in fault_causes):
            causal_structures.append({
                "type": "并发独立根因",
                "nodes": " or ".join(fault_causes)
            })

        # 并发协同根因
        if len(common_causes) > 1:
            causal_structures.append({
                "type": "并发协同根因",
                "nodes": " and ".join(common_causes)
            })

        # 分层链式因果
        cause_relations = set()
        for triple in subgraph["triples"]:
            if (triple["head"] in fault_causes or triple["head"] in common_causes) and \
               (triple["tail"] in fault_causes or triple["tail"] in common_causes):
                cause_relations.add((triple["head"], triple["tail"]))
        if cause_relations:
            causal_structures.append({
                "type": "分层链式因果",
                "nodes": " → ".join([head for head, tail in cause_relations])
            })

        # 链式现象
        phenomenon_relations = set()
        for triple in subgraph["triples"]:
            if triple["head"] in fault_phenomena and triple["tail"] in fault_phenomena:
                phenomenon_relations.add((triple["head"], triple["tail"]))
        if phenomenon_relations:
            causal_structures.append({
                "type": "链式现象",
                "nodes": " → ".join([head for head, tail in phenomenon_relations])
            })

        # 并发症状
        if len(fault_phenomena) > 1 and not phenomenon_relations:
            causal_structures.append({
                "type": "并发症状",
                "nodes": " and ".join(fault_phenomena)
            })

        return causal_structures

    def analyze_subgraphs(self, text_ids):
        """
        根据文本编号列表分析多个子图的因果结构
        """
        results = []
        for text_id in text_ids:
            subgraph = self.get_subgraph_by_text_id(text_id)
            causal_structures = self.infer_causal_structure(subgraph)
            results.append({
                "text_id": subgraph["text_id"],
                "nodes": subgraph["nodes"],
                "triples": subgraph["triples"],
                "causal_structures": causal_structures
            })
        return results

# 示例调用
if __name__ == "__main__":
    # 示例文本编号列表
    text_ids = ["356"]

    # 初始化推理模块
    inference_module = InferenceModule()

    # 分析子图
    results = inference_module.analyze_subgraphs(text_ids)

    # 输出结果
    for result in results:
        print(f"文本编号：{result['text_id']}")
        print(f"节点：{result['nodes']}")
        print(f"三元组：{result['triples']}")

        # 将因果结构的每个字典转换为字符串形式
        causal_structures_str = ", ".join(
            f"{structure['type']}: {structure['nodes']}" for structure in result['causal_structures']
        )
        print(f"因果结构：{causal_structures_str}")
        print("-" * 50)