import streamlit as st
import openai
import os
import time
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# GPT API 키 설정
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 구글 시트 저장 함수 정의
def save_to_google_sheet(df):
    credentials = json.loads(st.secrets["GOOGLE_SHEET_CREDENTIALS"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(st.secrets["GOOGLE_SHEET_KEY"])
    worksheet = sheet.sheet1  # 첫 번째 시트 사용

    existing = pd.DataFrame(worksheet.get_all_records())
    updated = pd.concat([existing, df], ignore_index=True)
    set_with_dataframe(worksheet, updated)

# 문제 리스트 설정 (난이도별 3문제씩)
problems = [
    {"word": "인공지능", "difficulty": "쉬움"},
    {"word": "컴퓨터", "difficulty": "쉬움"},
    {"word": "고양이", "difficulty": "쉬움"},
    {"word": "세금", "difficulty": "중간"},
    {"word": "의사소통", "difficulty": "중간"},
    {"word": "우정", "difficulty": "중간"},
    {"word": "정의", "difficulty": "어려움"},
    {"word": "탈진", "difficulty": "어려움"},
    {"word": "교제", "difficulty": "어려움"}
]

# 세션 상태 초기화
if "problem_idx" not in st.session_state:
    st.session_state.problem_idx = 0
    st.session_state.score = 100
    st.session_state.total_score = 0
    st.session_state.history = []
    st.session_state.ended = False
    st.session_state.result_log = []

# 점수 차감 함수 (GPT를 활용하여 관련성 판단 - 세분화)
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
        return 3  # fallback in case of unexpected response

# GPT 호출 함수
def ask_gpt(question, answer, difficulty):
    prompt = f"""
    너는 단어 추리 게임의 마스터야. 숨겨진 단어는 "{answer}"이야.
    사용자가 "{question}"이라고 물었을 때 난이도 "{difficulty}" 기준으로 힌트를 줘.
    - 난이도 '쉬움'이면 최대한 구체적인 힌트를 줘.
    - 난이도 '중간'이면 중간 수준의 힌트를 줘.
    - 난이도 '어려움'이면 모호하게 대답해.
    또한 사용자의 질문에 정답 단어가 포함되어 있다면 바로 정답 처리하고 종료 메시지를 출력해.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"]

# 제목
st.title("🔍 GPT 단어 추리 게임")

# 이름 입력
name = st.text_input("당신의 이름을 입력하세요:")

# 현재 문제 불러오기
if st.session_state.problem_idx < len(problems):
    current = problems[st.session_state.problem_idx]
    answer = current["word"]
    difficulty = current["difficulty"]
else:
    st.session_state.ended = True

# 게임 종료 처리
if st.session_state.ended:
    st.success("🎉 모든 문제를 완료했습니다!")
    st.markdown(f"### 🔚 최종 점수: {st.session_state.total_score}점")
    result_df = pd.DataFrame(st.session_state.result_log)
    st.download_button("📥 전체 결과 CSV 다운로드", result_df.to_csv(index=False), file_name="final_results.csv")

    # ✅ 구글 시트에 저장
    score_df = pd.DataFrame([{
        "이름": name,
        "총점": st.session_state.total_score,
        "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    save_to_google_sheet(score_df)

    st.stop()

# 사용자 질문 입력
question = st.text_input(f"문제 {st.session_state.problem_idx+1}/9 - 난이도: {difficulty}\n질문을 입력하세요:")

if st.button("질문 보내기") and question:
    with st.spinner("GPT가 생각 중..."):
        penalty = deduct_score(question, answer)
        st.session_state.score -= penalty
        reply = ask_gpt(question, answer, difficulty)
        time.sleep(0.5)

    st.session_state.history.append((question, reply))
    st.write("**GPT:**", reply)

    if answer.lower() in question.lower():
        st.success("정답입니다! 🎉 다음 문제로 이동합니다.")

        # 점수 기록
        st.session_state.result_log.append({
            "이름": name,
            "문제 번호": st.session_state.problem_idx + 1,
            "난이도": difficulty,
            "정답": answer,
            "점수": st.session_state.score
        })

        st.session_state.total_score += st.session_state.score
        st.session_state.problem_idx += 1
        st.session_state.score = 100
        st.session_state.history.clear()
        st.rerun()

# 이전 질문 출력
if st.session_state.history:
    st.subheader("💬 이전 질문들")
    for q, r in st.session_state.history[::-1]:
        st.markdown(f"**Q:** {q}")
        st.markdown(f"**A:** {r}")
        st.markdown("---")
