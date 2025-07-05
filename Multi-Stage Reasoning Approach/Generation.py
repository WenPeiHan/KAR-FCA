from langchain.chat_models import ChatOpenAI


class LLMResponseGenerator:
    def __init__(self, llm=None):
        if llm is None:
            self.llm = ChatOpenAI(
                temperature=0,
                model_name="Moonshot-v1-8k",
                openai_api_key="",
                openai_api_base="https://api.moonshot.cn/v1"
            )
        else:
            self.llm = llm

    def generate_response(self, query: str, subgraph_info: str = "", context: str = "") -> str:
        """
        输入：
        - 查询问句
        - 推理模块的输出内容（包括节点、三元组和因果结构，仅首次回答时使用）
        - 上下文信息（用于多轮问答）

        输出：
        - 语言模型生成的响应
        """
        if context:
            # 后续追问的提示词
            prompt = f"""
            你是一位专业的风电机组故障分析专家。你的任务是根据以下信息，回答用户输入的问题。
            用户提出了以下问题：
            {query}

            之前的对话内容如下：
            {context}
            """
        else:
            # 首次回答的提示词
            prompt = f"""
            你是一位专业的风电机组故障分析专家。你的任务是根据以下信息，回答用户输入的问题。
            用户提出了以下问题：
            {query}

            根据知识图谱检索到的相关子图信息如下：
            {subgraph_info}

            其中：
            - 文本编号：历史相似事件编号。
            - 节点：子图中包含的所有故障子事件。
            - 三元组：子事件及其关系。
            - 因果结构：识别出的因果结构类型及其涉及的事件节点。

            因果结构类型说明：
            - 并发独立根因：存在多个原因，每个根因可独立导致后果。
            - 并发协同根因：存在多个原因，多因协同才能引发后果。
            - 分层链式因果：存在多个原因链式传播。
            - 并发症状：一个事件导致多个现象。
            - 链式现象：多个现象之间的链式反应。

            回答中需要明确标记以下内容：
            - [可能的故障传播路径--来源于KG]：
                输出子图中所有节点和三元组，将三元组以事件链的形式呈现，不要做多余的分析
            - [因果结构分析]：
                输入中的因果结构对应内容，不做多于分析
            - [基于KG的故障分析]：
                基于你具备的风电机组故障领域专业知识和知识图谱检索到的相关子图信息生成的回答，不要过度发散和凭空想象
            """

        # 调用语言模型生成响应
        response = self.llm.predict(prompt)
        return response