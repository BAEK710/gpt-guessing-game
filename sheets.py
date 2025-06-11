# sheets.py
import gspread
import pandas as pd
import json
from datetime import datetime
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st


def _get_worksheet():
    credentials = json.loads(st.secrets["GOOGLE_SHEET_CREDENTIALS"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["GOOGLE_SHEET_KEY"])
    return sheet.sheet1


def save_individual_score(name, problem_num, difficulty, answer, score, total_score):
    worksheet = _get_worksheet()
    row = pd.DataFrame([{
        "이름": name,
        "문제 번호": problem_num,
        "난이도": difficulty,
        "정답": answer,
        "점수": score,
        "총점": total_score,
        "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    existing = pd.DataFrame(worksheet.get_all_records())
    updated = pd.concat([existing, row], ignore_index=True)
    set_with_dataframe(worksheet, updated)


def save_final_score(name, total_score):
    worksheet = _get_worksheet()
    row = pd.DataFrame([{
        "이름": name,
        "총점": total_score,
        "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    existing = pd.DataFrame(worksheet.get_all_records())
    updated = pd.concat([existing, row], ignore_index=True)
    set_with_dataframe(worksheet, updated)