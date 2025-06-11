import streamlit as st
import openai
import os
import time
import pandas as pd
import re
from datetime import datetime

from problems import problems
from game_logic import deduct_score, ask_gpt
from sheets import save_individual_score, save_final_score

# GPT API 키 설정
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 세션 상태 초기화
if "problem_idx" not in st.session_state:
    st.session_state.problem_idx = 0
    st.session_state.score = 100
    st.session_state.total_score = 0
    st.session_state.history = []
    st.session_state.ended = False
    st.session_state.result_log = []
    st.session_state.hint_shown = False

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
    save_final_score(name, st.session_state.total_score)

    st.stop()

# 사용자 질문 입력
question = st.text_input(f"문제 {st.session_state.problem_idx+1}/9 - 난이도: {difficulty}\n질문을 입력하세요:")

# 건너뛰기 버튼
if st.button("⏭️ 건너뛰기"):
    st.session_state.result_log.append({
        "이름": name,
        "문제 번호": st.session_state.problem_idx + 1,
        "난이도": difficulty,
        "정답": answer,
        "점수": 0
    })
    st.session_state.problem_idx += 1
    st.session_state.score = 100
    st.session_state.history.clear()
    st.session_state.hint_shown = False
    st.rerun()

# 질문 처리
if st.button("질문 보내기") and question:
    with st.spinner("GPT가 생각 중..."):
        penalty = deduct_score(question, answer)
        st.session_state.score = max(0, st.session_state.score - penalty)
        reply = ask_gpt(question, answer, difficulty)
        time.sleep(0.5)

    st.session_state.history.append((question, reply))
    st.write("**GPT:**", reply)

    # 정답 포함 여부 확인 (단어 단위)
    if re.search(rf"\\b{re.escape(answer.lower())}\\b", question.lower()):
        st.success("정답입니다! 🎉 다음 문제로 이동합니다.")

        # 점수 기록
        save_individual_score(name, st.session_state.problem_idx + 1, difficulty, answer, st.session_state.score, st.session_state.total_score + st.session_state.score)

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
        st.session_state.hint_shown = False
        st.rerun()

# 힌트 제공 조건: 5번 질문 이상 시 초성 힌트
if len(st.session_state.history) >= 5 and not st.session_state.hint_shown:
    chosung = ''.join([c[0] for c in answer if '가' <= c <= '힣'])
    st.info(f"💡 초성 힌트: {' '.join(chosung)}")
    st.session_state.hint_shown = True

# 이전 질문 출력
if st.session_state.history:
    st.subheader("💬 이전 질문들")
    for q, r in st.session_state.history[::-1]:
        st.markdown(f"**Q:** {q}")
        st.markdown(f"**A:** {r}")
        st.markdown("---")