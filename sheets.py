import gspread
import pandas as pd
import json
from datetime import datetime
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

# 🔐 구글 워크시트 연결
def _get_worksheet():
    credentials = json.loads(st.secrets["GOOGLE_SHEET_CREDENTIALS"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["GOOGLE_SHEET_KEY"])
    return sheet.sheet1  # "Leaderboard" 시트

# ✅ 문제 맞출 때마다 누적 점수 갱신 (1줄만 유지)
def save_individual_score(name, problem_num, difficulty, answer, score, total_score):
    worksheet = _get_worksheet()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    name = name.strip()  # 공백 제거

    existing = pd.DataFrame(worksheet.get_all_records())

    if "이름" in existing.columns and name in existing["이름"].values:
        idx = existing[existing["이름"] == name].index[0]
        existing.at[idx, "총점"] = total_score
        existing.at[idx, "날짜"] = now
    else:
        new_row = pd.DataFrame([{
            "이름": name,
            "총점": total_score,
            "날짜": now
        }])
        existing = pd.concat([existing, new_row], ignore_index=True)

    set_with_dataframe(worksheet, existing)

# # ✅ 최종 점수 저장은 동일하게 유지 (중복 저장될 순 있음)
# def save_final_score(name, total_score):
#     worksheet = _get_worksheet()
#     row = pd.DataFrame([{
#         "이름": name.strip(),
#         "총점": total_score,
#         "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     }])
#     existing = pd.DataFrame(worksheet.get_all_records())
#     updated = pd.concat([existing, row], ignore_index=True)
#     set_with_dataframe(worksheet, updated)

# ✅ 리더보드 조회
def get_leaderboard():
    worksheet = _get_worksheet()
    df = pd.DataFrame(worksheet.get_all_records())
    if "이름" in df.columns and "총점" in df.columns:
        leaderboard = df.groupby("이름")["총점"].max().reset_index().sort_values(by="총점", ascending=False)
        return leaderboard
    return pd.DataFrame(columns=["이름", "총점"])
