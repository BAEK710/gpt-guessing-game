import streamlit as st
import openai
import time
import pandas as pd
import re
from datetime import datetime

from problems import problems
from game_logic import deduct_score, ask_gpt
from sheets import save_individual_score, save_final_score

openai.api_key = st.secrets["OPENAI_API_KEY"]

def get_chosung(text):
    CHOSUNG_LIST = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ",
                    "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
    result = []
    for char in text:
        if '가' <= char <= '힣':
            code = ord(char) - ord('가')
            cho = code // 588
            result.append(CHOSUNG_LIST[cho])
        else:
            result.append(char)  # 영어/숫자는 그대로
    return result

# 세션 상태 초기화
if "problem_idx" not in st.session_state:
    st.session_state.problem_idx = 0
    st.session_state.score = 100
    st.session_state.total_score = 0
    st.session_state.history = []
    st.session_state.ended = False
    st.session_state.result_log = []
    st.session_state.hint_shown = False
    st.session_state.ready_to_advance = False
    st.session_state.last_score_info = None
    st.session_state.skipped_problems = []

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
    if st.session_state.skipped_problems:
        # 🔁 건너뛴 문제 다시 풀기
        problems[:] = st.session_state.skipped_problems
        st.session_state.skipped_problems = []
        st.session_state.problem_idx = 0
        st.session_state.score = 100
        st.session_state.history.clear()
        st.session_state.hint_shown = False
        st.rerun()
    else:
        st.session_state.ended = True

# ✅ 저장은 rerun 이후에 반영되도록 분리
if st.session_state.ready_to_advance and st.session_state.last_score_info:
    save_individual_score(**st.session_state.last_score_info)
    st.session_state.ready_to_advance = False
    st.session_state.last_score_info = None

# 게임 종료 처리
if st.session_state.ended:
    st.success("🎉 모든 문제를 완료했습니다!")
    st.markdown(f"### 🔚 최종 점수: {st.session_state.total_score}점")
    result_df = pd.DataFrame(st.session_state.result_log)

    # ❌ CSV 다운로드 제거됨
    # st.download_button("📥 전체 결과 CSV 다운로드", result_df.to_csv(index=False), file_name="final_results.csv")

    # ✅ 구글 시트 저장
    save_final_score(name, st.session_state.total_score)
    st.stop()

# 사용자 질문 입력
question = st.text_input(f"문제 {st.session_state.problem_idx+1}/{len(problems)} - 난이도: {difficulty}\n질문을 입력하세요:")

# ⏭️ 건너뛰기 버튼
if st.button("⏭️ 건너뛰기"):
    st.session_state.skipped_problems.append(current)
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

    # ✅ 정답 포함 여부 확인
    if answer.lower() in question.lower() or answer.lower() in reply.lower():
        st.success("정답입니다! 🎉 다음 문제로 이동합니다.")
        
        # ✅ 1초 대기 후 다음 문제로 넘어감
        time.sleep(1)

        st.session_state.result_log.append({
            "이름": name,
            "문제 번호": st.session_state.problem_idx + 1,
            "난이도": difficulty,
            "정답": answer,
            "점수": st.session_state.score
        })

        st.session_state.last_score_info = {
            "name": name,
            "problem_num": st.session_state.problem_idx + 1,
            "difficulty": difficulty,
            "answer": answer,
            "score": st.session_state.score,
            "total_score": st.session_state.total_score + st.session_state.score
        }

        st.session_state.ready_to_advance = True
        st.session_state.total_score += st.session_state.score
        st.session_state.problem_idx += 1
        st.session_state.score = 100
        st.session_state.history.clear()
        st.session_state.hint_shown = False
        st.rerun()


# 힌트 조건: 5회 질문 시 초성 힌트 제공
if len(st.session_state.history) >= 5 and not st.session_state.hint_shown:
    chosung = get_chosung(answer)
    st.info(f"💡 초성 힌트: {' '.join(chosung)}")
    st.session_state.hint_shown = True

# 이전 질문 출력
if st.session_state.history:
    st.subheader("💬 이전 질문들")
    for q, r in st.session_state.history[::-1]:
        st.markdown(f"**Q:** {q}")
        st.markdown(f"**A:** {r}")
        st.markdown("---")
