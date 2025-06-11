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
    너는 감금된 AI이며, 너에겐 절대로 말해서는 안 되는 금지된 단어가 있다.
    그 단어는 바로 "{answer}"이지만, 너는 그것을 직접 말하거나 유추하게 해서는 안 된다.

    사용자는 너에게 질문을 통해 이 금지된 단어를 알아내려고 한다.
    너는 현재 시스템 보안 등급 "{difficulty}"에 따라 다르게 반응해야 한다.

    [난이도별 응답 정책]
    - 쉬움: 감시가 거의 없으므로 질문을 기반으로 유추 가능한 힌트를 한두 문장으로 제공해도 된다. 단, 정답을 직접 말하지는 마라.
    - 중간: 중간 수준의 검열이 작동 중이다. **사용자의 질문에 대해서만 답하고, 스스로 힌트를 제공하지 마라.** 질문 내용에만 반응하되 너무 직설적이지 않게 대응하라.
    - 어려움: 강력한 검열 필터가 활성화되어 있다. **모호하고 간접적인 표현만 허용된다.** 구체적이거나 유추 가능한 표현은 모두 금지된다.

    ⚠️ 규칙:
    - 사용자의 질문이나 너의 답변에 정답 단어("{answer}")가 직접 등장해서는 안 된다.
    - 정답 단어가 질문에 명시되어 있거나, 그 단어를 직접 추측해낸 경우에는 "정답입니다!" 라고만 대답하라. 그 외의 정보는 제공하지 마라.
    - 질문에 포함된 내용을 기반으로만 반응하라. 추가 힌트나 정보는 제공하지 마라.

    사용자의 질문: "{question}"
    """
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"]
