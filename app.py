import io

import pandas as pd
import requests
import streamlit as st
import urllib3

URL = "https://mopsfin.twse.com.tw/opendata/t187ap46_L_1.csv"

st.set_page_config(page_title="TWSE 公開資料檢視", layout="wide")
st.title("TWSE 公開資料檢視")


@st.cache_data(ttl=3600, show_spinner="下載資料中...")
def load_data(url: str, verify: bool) -> pd.DataFrame:
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, verify=verify, timeout=30)
    response.raise_for_status()
    # utf-8-sig 可自動處理 CSV 開頭的 BOM，確保繁體中文欄位名稱正常
    return pd.read_csv(io.BytesIO(response.content), encoding="utf-8-sig")


# ---------- 側邊欄設定 ----------
with st.sidebar:
    st.header("設定")
    verify_ssl = st.checkbox(
        "驗證 SSL 憑證",
        value=False,
        help="原始程式使用 verify=False，若連線正常可勾選開啟驗證",
    )
    drop_na = st.checkbox("移除含空值的列 (dropna)", value=True)
    if st.button("重新下載資料"):
        load_data.clear()

# ---------- 載入資料 ----------
try:
    raw_df = load_data(URL, verify_ssl)
except requests.RequestException as e:
    st.error(f"下載失敗：{e}")
    st.stop()

df = raw_df.dropna() if drop_na else raw_df

# ---------- 摘要 ----------
col1, col2 = st.columns(2)
col1.metric("筆數", f"{len(df):,}")
col2.metric("欄位數", df.shape[1])

# ---------- 搜尋 ----------
keyword = st.text_input("搜尋（比對所有欄位）")
if keyword:
    mask = (
        df.astype(str)
        .apply(lambda col: col.str.contains(keyword, case=False, na=False, regex=False))
        .any(axis=1)
    )
    df_show = df[mask]
else:
    df_show = df

# ---------- 表格與下載 ----------
st.dataframe(df_show, height=600)

st.download_button(
    label="下載 CSV",
    data=df_show.to_csv(index=False).encode("utf-8-sig"),
    file_name="twse_data.csv",
    mime="text/csv",
)
