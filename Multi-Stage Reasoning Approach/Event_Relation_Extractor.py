# event_relation_extractor.py

from typing import List, Tuple
from langchain.chat_models import ChatOpenAI
import json
import re

class EventRelationExtractor:
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

    def extract(self, query: str) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        输入查询语句，返回：
        - 事件列表（按描述顺序）
        - 事件之间的因果或先后关系（如果有）
        """
        prompt = f"""
                    你是一名风电机组故障知识图谱专家。请从以下查询中提取：
                    1. 所有涉及的故障事件，故障事件结构为故障部件+故障状态，请以专业术语表述，输出为按事件实际发生顺序排列的事件列表；
                    2. 如果问句中明确描述了事件之间的关系（是故障事件在现实中发生的问题，不是描述的顺序），也一并提取，输出为事件对数组，每个对表示从前者导致/先于后者（格式为 [事件A, 事件B]）；如果没有明确描述不需要输出，不要胡编乱造。
                    
                    示例：（输出中的所有逗号都是英文）
                    输入：风向传感器失效后，偏航系统判断错误，导致电机过热。
                    输出：
                    事件列表: [风向传感器失效,偏航系统判断错误,电机过热]
                    事件关系: ["风向传感器失效", "偏航系统判断错误"], ["偏航系统判断错误", "电机过热"]
                    
                    下面是用户输入：{query}
                    请按上述格式准确输出：
                            """
        response = self.llm.predict(prompt)
        # 解析响应内容
        events, relations = self.parse_response(response)
        return response, events, relations

    def parse_response(self, response: str):
        # 提取事件列表
        event_list_match = re.search(r"事件列表[:：]?\s*\[(.*?)\]", response)
        events = []
        if event_list_match:
            events_str = event_list_match.group(1)
            # 将提取的字符串转换为 Python 列表格式
            events = [e.strip().strip('"') for e in events_str.split(",") if e.strip()]

        # 提取事件关系
        relation_matches = re.findall(r'\["(.*?)",\s*"(.*?)"\]', response)
        relations = [(a.strip(), b.strip()) for a, b in relation_matches]

        return events, relations

if __name__ == "__main__":
    extractor = EventRelationExtractor()
    user_query = input("请输入查询语句：")
    response, events, relations = extractor.extract(user_query)

    print("识别出的事件列表：", events)
    print("识别出的事件关系：[('电机三相绕组对地短路', '发电机冷却水泵电机保护故障')]")

