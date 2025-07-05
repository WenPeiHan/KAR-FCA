from Event_Relation_Extractor import EventRelationExtractor
from Semantic_Subgraph_Filter import iterative_filtering
from Infer_Causal_Structure import InferenceModule
from Generation import LLMResponseGenerator

if __name__ == "__main__":
    # 初始化事件提取器
    extractor = EventRelationExtractor()

    # 初始化推理模块
    inference_module = InferenceModule()

    # 初始化生成模块
    generator = LLMResponseGenerator()

    # 初始化上下文
    context = ""

    # 用户输入首次查询语句
    user_query = input("请输入查询语句：")

    # 提取事件列表和事件关系
    response, events, relations = extractor.extract(user_query)

    print("\n原始响应：\n", response)
    print("识别出的事件：", events)
    print("识别出的事件关系：", relations)

    # 调用子图检索
    filtered_subgraphs = iterative_filtering(events, top_k=5)

    print("\n检索到的子图：")
    for subgraph in filtered_subgraphs:
        print(f"文本编号：{subgraph['text_id']}")
        print(f"节点：{subgraph['nodes']}")
        print(f"三元组：{subgraph['triples']}")
        print("-" * 50)

    # 分析子图的因果结构
    print("\n分析子图的因果结构：")
    results = inference_module.analyze_subgraphs([subgraph['text_id'] for subgraph in filtered_subgraphs])
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

        # 生成响应
        subgraph_info = f"""
        文本编号：{result['text_id']}
        节点：{result['nodes']}
        三元组：{result['triples']}
        因果结构：{causal_structures_str}
        """
        response = generator.generate_response(user_query, subgraph_info, context)
        print("语言模型生成的响应：")
        print(response)
        print("-" * 50)

        # 更新上下文
        context += f"用户问题：{user_query}\nAI回答：{response}\n"

    # 多轮问答
    while True:
        user_query = input("请输入新的问题（输入'退出'结束对话）：")
        if user_query.lower() == "退出":
            break

        # 生成响应
        response = generator.generate_response(user_query, context=context)
        print("语言模型生成的响应：")
        print(response)
        print("-" * 50)

        # 更新上下文
        context += f"用户问题：{user_query}\nAI回答：{response}\n"