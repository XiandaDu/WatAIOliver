import csv
import io
import os
import shutil
from datetime import datetime
from transformers import AutoTokenizer, AutoModel
import torch
import chromadb
from chroma_utils import *
from evaluate_api import *
from fastapi import Depends, FastAPI, Request, UploadFile, File, Form, Query, HTTPException, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, StreamingResponse
from starlette.templating import Jinja2Templates

from models import User, Course, Log
from database import engine, get_db
from util.r import ok
# 导入 Base 和 engine
from models import Base
from database import engine

# 从您的 app.py 中重用的函数
def build_conversation_history(conversation, max_tokens=1024):
    conversation_history = ""
    total_tokens = 0
    for turn in reversed(conversation):
        user_turn = f"User: {turn['question']}\n"
        assistant_turn = f"Assistant: {turn.get('answer', '')}\n"
        turn_text = user_turn + assistant_turn
        turn_tokens = len(turn_text.split())  # 简单的词数统计，您可以根据需要调整
        if total_tokens + turn_tokens <= max_tokens:
            conversation_history = turn_text + conversation_history
            total_tokens += turn_tokens
        else:
            break
    return conversation_history

def load_background_information():
    background_file_path = '/Users/eric/Desktop/Automatic_Tutoring/lions and tigers.txt'  # 根据需要调整路径
    try:
        with open(background_file_path, 'r', encoding='utf-8') as f:
            background_info = f.read()
    except Exception as e:
        background_info = "No background information available."
        print(f"Error loading background information: {e}")
    return background_info

def main():
    # 初始化对话历史
    conversation = []
    # 加载背景信息
    background_info = load_background_information()

    print("You are now chatting with Oliver. Type 'exit' to quit.\n")

    while True:
        # 获取用户输入
        question = input("You: ")
        if question.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break

        # 将当前问题添加到对话
        conversation.append({'question': question})

        # 限制对话历史的长度
        MAX_CONVERSATION_LENGTH = 10
        if len(conversation) > MAX_CONVERSATION_LENGTH:
            conversation = conversation[-MAX_CONVERSATION_LENGTH:]

        # 构建对话历史
        conversation_history = build_conversation_history(conversation[:-1])

        # 构建最终提示
        final_prompt = (
            f"Here is some possibly relevant background information:\n"
            f"{background_info}\n\n"
            f"{conversation_history}"
            f"User: {question}\n"
            f"Assistant:"
        )

        # 调用语言模型生成回答
        answer = text_text_eval(document_text="", prompt_text=final_prompt,
                                model="nemo", max_length=1024)

        # 更新最后一轮对话的回答
        conversation[-1]['answer'] = answer

        # 打印 Oliver 的回答
        print(f"Oliver: {answer}\n")

        # 可选：将交互记录到数据库（如果需要）
        # with SessionLocal() as db:
        #     entity = Log()
        #     entity.create_time = datetime.now()
        #     entity.user_id = 1  # 使用默认用户 ID 或根据需要调整
        #     entity.background = background_info
        #     entity.query = question
        #     entity.answer = answer
        #     entity.llm = answer
        #     db.add(entity)
        #     db.commit()

if __name__ == "__main__":
    main()
