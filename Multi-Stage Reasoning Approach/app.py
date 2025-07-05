from flask import Flask, request, jsonify, render_template
from Event_Relation_Extractor import EventRelationExtractor
from Semantic_Subgraph_Filter import iterative_filtering
from Infer_Causal_Structure import InferenceModule
from Generation import LLMResponseGenerator

app = Flask(__name__)

# 初始化模块
extractor = EventRelationExtractor()
inference_module = InferenceModule()
generator = LLMResponseGenerator()

# 初始化上下文
context = ""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    global context
    user_query = request.json.get("query")

    if user_query is None:
        return jsonify({"error": "Missing 'query' field."}), 400

    if user_query.lower() == "退出":
        context = ""
        return jsonify({"response": "对话已结束。"})

    # === 首轮：context 为空，走全流程 ===
    if context.strip() == "":
        try:
            # 事件抽取
            _, events, relations = extractor.extract(user_query)

            # 子图检索
            filtered_subgraphs = iterative_filtering(events, top_k=5)

            # 因果结构分析
            results = inference_module.analyze_subgraphs([sg['text_id'] for sg in filtered_subgraphs])

            # 拼接所有结果为 prompt 中的 subgraph_info
            subgraph_info_list = []
            for result in results:
                causal_str = ", ".join(f"{c['type']}: {c['nodes']}" for c in result['causal_structures'])
                info = f"""文本编号：{result['text_id']}
                        节点：{result['nodes']}
                        三元组：{result['triples']}
                        因果结构：{causal_str}"""
                subgraph_info_list.append(info)

            subgraph_info = "\n\n".join(subgraph_info_list)

            # 首轮调用 LLM，带入子图信息
            response = generator.generate_response(user_query, subgraph_info=subgraph_info, context="")

        except Exception as e:
            return jsonify({"response": f"[错误] 后端处理失败：{str(e)}"})

    # === 后续轮次：只传上下文，不做子图推理 ===
    else:
        response = generator.generate_response(user_query, context=context)

    # 更新上下文
    context += f"用户问题：{user_query}\nAI回答：{response}\n"

    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
