import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 預設頁面設定
st.set_page_config(page_title="SEO Meta Rewrite Tool", layout="wide")
st.title("🔍 Google Search Console AI Rewrite Assistant")

# Step 1: 上傳檔案
st.header("Step 1: 上傳關鍵字資料（CSV）")

with st.expander("📄 點我查看檔案格式範例"):
    st.markdown("""
    請確保你上傳的檔案格式包含以下欄位：
    - `Page`
    - `Query`
    - `Clicks`
    - `Impressions`
    - `CTR`
    - `Position`
    
    範例：
    ```
    Page,Query,Clicks,Impressions,CTR,Position
    https://your-site.com/page-1,keyword A,10,300,0.9%,9.5
    ```
    """)

# 抓取 Title 與 Meta 的方法（加入 headers 增加成功率）
def fetch_title_and_meta(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else ""

        meta_tag = soup.find("meta", attrs={"name": "description"})
        meta = meta_tag["content"].strip() if meta_tag and "content" in meta_tag.attrs else ""

        return title, meta

    except Exception as e:
        return "", ""


# 開始上傳流程
uploaded_file = st.file_uploader("📤 請上傳包含關鍵字資料的 CSV 檔案", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        required_columns = ['Page', 'Query', 'Clicks', 'Impressions', 'CTR', 'Position']
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            st.error(f"❌ 缺少必要欄位：{', '.join(missing_cols)}")
        else:
            # 數值清洗
            df['Impressions'] = df['Impressions'].astype(str).str.replace(',', '', regex=False)
            df['Impressions'] = pd.to_numeric(df['Impressions'], errors='coerce')

            df['CTR'] = df['CTR'].astype(str).str.replace('%', '', regex=False)
            df['CTR'] = pd.to_numeric(df['CTR'], errors='coerce') / 100

            for col in ['Clicks', 'Position']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            if df[['Clicks', 'Impressions', 'CTR', 'Position']].isnull().values.any():
                st.warning("⚠️ 有些數值轉換失敗，請檢查資料")

            st.success("✅ 檔案上傳成功，欄位與格式皆正確")
            st.dataframe(df.head())

            # Step 2: 關鍵字分類與 Action Code 分析
            if st.button("Step 2 - 進行關鍵字前處理分析"):
                df["Total_Clicks_Page"] = df.groupby("Page")["Clicks"].transform("sum")
                df["Click_Share"] = df["Clicks"] / df["Total_Clicks_Page"]

                def classify_keyword_importance(row):
                    if row["Click_Share"] >= 0.2:
                        return "Primary"
                    elif row["Click_Share"] < 0.2 and row["Impressions"] >= 30 and row["Position"] <= 20:
                        return "Secondary"
                    elif row["Impressions"] >= 30 and row["Position"] > 30:
                        return "Ghost"
                    else:
                        return "Ignore"

                df["Keyword_Importance"] = df.apply(classify_keyword_importance, axis=1)
                df_focus = df[df["Keyword_Importance"].isin(["Primary", "Secondary"])].copy()

                avg_ctr = df_focus["CTR"].mean()

                def classify_action(row, avg_ctr):
                    imp, ctr, pos = row['Impressions'], row['CTR'], row['Position']
                    if imp > 30 and ctr > avg_ctr and 1 <= pos <= 5:
                        return 'no_change_needed_high_performer'
                    elif imp > 30 and ctr < avg_ctr and 6 <= pos <= 10:
                        return 'strengthen_title_meta_internal_linking'
                    elif imp > 30 and ctr < avg_ctr and 11 <= pos <= 20:
                        return 'semantic_review_and_refinement'
                    elif imp > 30 and ctr > avg_ctr and 6 <= pos <= 10:
                        return 'deepen_faq_expand_subkeywords'
                    elif imp > 30 and ctr < avg_ctr and 1 <= pos <= 5:
                        return 'revise_title_meta_for_clicks'
                    else:
                        return 'no_action'

                df_focus["Action_Code"] = df_focus.apply(lambda row: classify_action(row, avg_ctr), axis=1)
                st.session_state["df_focus"] = df_focus  # ➜ 儲存 df_focus
                st.success("🎯 分析完成，以下為推薦優化關鍵字")
                st.dataframe(df_focus)

            if st.button("Step 3 - 取得 Title & Meta"):
                    if "df_focus" not in st.session_state:
                        st.warning("請先執行 Step 2 分析，才能進行擷取。")
                    else:
                        df_focus = st.session_state["df_focus"]
                        unique_urls = df_focus["Page"].unique()
                        total = len(unique_urls)

                        st.info(f"🔎 即將擷取 {total} 個頁面，請稍候...")
                        progress_bar = st.progress(0, text="正在擷取中...")

                        title_meta_dict = {}
                        for idx, url in enumerate(unique_urls):
                            title, meta = fetch_title_and_meta(url)
                            title_meta_dict[url] = {
                                "Current_Title": title,
                                "Current_Meta": meta
                            }

                            # 更新進度條
                            progress = int((idx + 1) / total * 100)
                            progress_bar.progress(progress, text=f"擷取中... ({idx + 1}/{total})")

                        progress_bar.empty()  # 移除進度條

                        df_title_meta = pd.DataFrame.from_dict(title_meta_dict, orient="index").reset_index()
                        df_title_meta.rename(columns={"index": "Page"}, inplace=True)

                        df_focus = df_focus.merge(df_title_meta, on="Page", how="left")

                        # 更新 session_state 以便後續使用
                        st.session_state["df_focus"] = df_focus

                        st.success("✅ 成功擷取所有頁面 Title & Meta！")
                        st.dataframe(df_focus.head())

    except Exception as e:
        st.error(f"❌ 讀取檔案時發生錯誤：{e}")
else:
    st.info("請上傳正確格式的 CSV 關鍵字檔案")