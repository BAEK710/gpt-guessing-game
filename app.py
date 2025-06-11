# app.py
import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime

from game_logic import deduct_score, ask_gpt
from sheets import save_to_google_sheet
from problems import problems

# 세션 상태 초기화
if "problem_idx" not in st.session_state:
    st.session_state.problem_idx = 0
    st.session_state.score = 100
    st.session_state.total_score = 0
    st.session_state.history = []
    st.session_state.ended = False
    st.session_state.result_log = []
    st.session_state.hint_revealed = False

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
    if name:
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
    # 중복 질문 방지
    if question in [q for q, _ in st.session_state.history]:
        st.warning("이미 입력한 질문입니다. 다른 방식으로 질문해보세요.")
    else:
        with st.spinner("GPT가 생각 중..."):
            penalty = deduct_score(question, answer)
            st.session_state.score = max(0, st.session_state.score - penalty)
            reply = ask_gpt(question, answer, difficulty)
            time.sleep(0.5)

        st.session_state.history.append((question, reply))
        st.write("**GPT:**", reply)

        # 질문 5회 이상 시 초성 힌트 표시
        if len(st.session_state.history) >= 5 and not st.session_state.hint_revealed:
            initials = ''.join([char[0] if re.match(r'[가-힣]', char) else char for char in answer])
            st.info(f"🧩 초성 힌트: `{initials}`")
            st.session_state.hint_revealed = True

        # 정답 포함 여부 확인 (질문 or 답변에 포함되면 성공 처리)
        if re.search(rf"\b{re.escape(answer.lower())}\b", question.lower()) or \
           re.search(rf"\b{re.escape(answer.lower())}\b", reply.lower()):
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

            # ✅ 개별 문제 완료 후 Google Sheet 저장
            if name:
                score_df = pd.DataFrame([{
                    "이름": name,
                    "문제 번호": st.session_state.problem_idx + 1,
                    "난이도": difficulty,
                    "정답": answer,
                    "점수": st.session_state.score,
                    "총점": st.session_state.total_score,
                    "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])
                save_to_google_sheet(score_df)

            st.session_state.problem_idx += 1
            st.session_state.score = 100
            st.session_state.history.clear()
            st.session_state.hint_revealed = False
            st.rerun()

# ❌ 문제 넘기기 기능
if st.button("❌ 이 문제 넘기기"):
    st.session_state.result_log.append({
        "이름": name,
        "문제 번호": st.session_state.problem_idx + 1,
        "난이도": difficulty,
        "정답": answer,
        "점수": 0
    })

    # ✅ Google Sheet에 0점 저장
    if name:
        score_df = pd.DataFrame([{
            "이름": name,
            "문제 번호": st.session_state.problem_idx + 1,
            "난이도": difficulty,
            "정답": answer,
            "점수": 0,
            "총점": st.session_state.total_score,
            "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        save_to_google_sheet(score_df)

    st.session_state.problem_idx += 1
    st.session_state.score = 100
    st.session_state.history.clear()
    st.session_state.hint_revealed = False
    st.rerun()

# 이전 질문 출력
if st.session_state.history:
    st.subheader("💬 이전 질문들")
    for q, r in st.session_state.history[::-1]:
        st.markdown(f"**Q:** {q}")
        st.markdown(f"**A:** {r}")
        st.markdown("---")
