# game_logic.py
import openai
import streamlit as st

openai.api_key = st.secrets["OPENAI_API_KEY"]

def deduct_score(question, answer):
    relevance_prompt = f"""
    사용자의 질문: "{question}"
    정답 단어: "{answer}"

    위 질문이 정답 단어를 추리하는 데 얼마나 관련성이 있는지 5단계로 평가해줘:
    - 매우 높음: -1점
    - 높음: -2점
    - 보통: -3점
    - 낮음: -4점
    - 매우 낮음 또는 무관함: -5점

    숫자만 답해줘. 예: 1, 2, 3, 4, 5 중 하나
    """
    relevance_response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": relevance_prompt}],
        temperature=0
    )
    score_str = relevance_response["choices"][0]["message"]["content"].strip()
    try:
        return int(score_str)
    except:
        return 3  # fallback

def ask_gpt(question, answer, difficulty):
    prompt = f"""
    너는 단어 추리 게임의 마스터야. 숨겨진 단어는 "{answer}"이야.
    사용자가 "{question}"이라고 물었을 때 난이도 "{difficulty}" 기준으로 힌트를 줘.

    - 쉬움: 약간 유추 가능한 힌트를 한두 문장으로 제공 (정답 직접 노출은 절대 금지)
    - 중간: 추상적이거나 비유적인 설명으로 유도 (직접적으로 연상되면 안 됨)
    - 어려움: 최대한 모호하고 보수적으로 대답해. 구체적인 설명은 피해

    ⚠️ 중요: 정답 단어를 질문에 포함했거나 GPT 응답에 정답 단어가 직접적으로 나타나면 안 된다. 절대 노출하지 마라.
    단어를 맞췄다면 "정답입니다!"라는 메시지를 제공하고 종료하되, 정답 단어는 직접 출력하지 마.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"]