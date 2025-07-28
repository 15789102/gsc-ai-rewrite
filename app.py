import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openai import OpenAI


def classify_keyword_importance(row, impression_threshold):
                    if row["Click_Share"] >= 0.2:
                        return "Primary"
                    elif row["Click_Share"] < 0.2 and row["Impressions"] >= 30 and row["Position"] <= 20:
                        return "Secondary"
                    elif row["Impressions"] >= impression_threshold and row["Position"] > 30:
                        return "Ghost"
                    else:
                        return "Ignore"

def classify_action(row, avg_ctr, impression_threshold):
    imp, ctr, pos = row['Impressions'], row['CTR'], row['Position']
    if imp > impression_threshold and ctr > avg_ctr and 1 <= pos <= 5:
        return 'no_change_needed_high_performer'
    elif imp > impression_threshold and ctr < avg_ctr and 6 <= pos <= 10:
        return 'strengthen_title_meta_internal_linking'
    elif imp > impression_threshold and ctr < avg_ctr and 11 <= pos <= 20:
        return 'semantic_review_and_refinement'
    elif imp > impression_threshold and ctr > avg_ctr and 6 <= pos <= 10:
        return 'deepen_faq_expand_subkeywords'
    elif imp > impression_threshold and ctr < avg_ctr and 1 <= pos <= 5:
        return 'revise_title_meta_for_clicks'
    else:
        return 'no_action'


def generate_title_meta(prompt):
    # 呼叫 OpenAI API 回傳結果
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert SEO copywriter."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content



def create_prompt_page_level(page, tone_instruction):
    primary_keywords = [
        kw for kw, imp in zip(page["Keywords"], page["Keyword_Importance"])
        if imp == "Primary"
    ]
    secondary_keywords = [
        kw for kw, imp in zip(page["Keywords"], page["Keyword_Importance"])
        if imp == "Secondary"
    ]

    primary_text = "\n".join(f"- {kw}" for kw in primary_keywords) if primary_keywords else "None"
    secondary_text = "\n".join(f"- {kw}" for kw in secondary_keywords) if secondary_keywords else "None"

    prompt = f"""
        You are a professional SEO copywriter.

        Your task:
        Generate an optimized SEO Title (max 60 characters) and Meta Description (max 160 characters) for the following webpage.

        Page URL: {page['Page']}

        Current Title:
        "{page['Current_Title']}"

        Current Meta Description:
        "{page['Current_Meta']}"

        Here are the keywords and their importance:

        Primary Keywords:
        {primary_text}

        Secondary Keywords:
        {secondary_text}

        Guidelines:
        - Primary keywords must appear in the Title and Meta Description.
        - Secondary keywords should be included if they fit naturally, but are not mandatory.
        - The Title should be attractive and encourage clicks.
        - The Meta Description should be compelling and clearly explain the page’s purpose.
        - Keep the writing clear, natural, and reader-friendly.
        - Do not exceed character limits.
        - Writing Tone: {tone_instruction}

        Please return your response in this format:

        Title: ...
        Meta Description: ...
        """
    return prompt

def extract_title_meta(text):
    title, meta = "", ""
    for line in text.split("\n"):
        if line.lower().startswith("title:"):
            title = line.split(":",1)[1].strip()
        elif line.lower().startswith("meta description:"):
            meta = line.split(":",1)[1].strip()
    return title, meta

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

####==========================================================


with st.sidebar:
    st.image("gsc-img.png", width=360)  # 可調整 width
    st.markdown("🔐 **OpenAI Key Setting**")
    openai_api_key = st.text_input("Paste your OpenAI API key", type="password", key="openai_key_input")
    if openai_api_key:
        st.session_state["OPENAI_API_KEY"] = openai_api_key

# 在程式主區域建立 client
if "OPENAI_API_KEY" in st.session_state:
    client = OpenAI(api_key=st.session_state["OPENAI_API_KEY"])
else:
    st.error("🔐 Please Paste OpenAI API Key")

#client = OpenAI(api_key="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")  # 請替換成你的 key

with st.sidebar.expander("📘 Instroduction", expanded=False):
    st.markdown("""
        ### 📘 Features of This Tool:
        1. Upload a CSV file containing pages and keywords
        2. Set CTR and Impression thresholds
        3. Automatically generate SEO title and meta description suggestions using AI
        4. Download the results for website optimization and updates

        ### 🧩 Column Descriptions:
        - `Current_Title`: Original page title
        - `Current_Meta`: Original page meta description
        - `Suggested_Title`: AI-generated new title
        - `Suggested_Meta`: AI-generated new meta description

        ### 📌 Important Notes:
        - Please do not upload more than 100 rows of data
        - Make sure to input your OpenAI API key to generate suggestions
    """)

    st.markdown("---")
    st.markdown("© by **Ben Chen**, 2025")

with st.sidebar.expander("📘 Project Background: Why This Tool?"):
    st.markdown("""
    This tool is designed to help marketers and content creators **quickly identify pages and keywords worth optimizing from GSC data**, and automatically generate improved SEO titles and meta descriptions.

    #### 🔧 Optimization Logic Overview:

    1. **Data Filtering**  
       Set thresholds for Impressions and CTR to find pages that deserve attention.

    2. **Smart Action Classification**  
       Based on Impressions, CTR, and Position, each row is categorized for different optimization actions (e.g., update meta title, add internal links, expand content).

    3. **AI-Powered Suggestions**  
       Generates new SEO titles and descriptions using OpenAI's API and your selected tone of voice.

    4. **One-Click Export**  
       Download the final suggestions as a CSV — ready to update on your site.
    """)

    st.markdown("---")
    st.markdown("© by **Ben Chen**, 2025")

# 預設頁面設定
st.set_page_config(page_title="SEO Meta Rewrite Tool", layout="wide")
st.title("Google Search Console AI Rewrite Assistant")
st.text("© by **Ben Chen**, 2025")

# Step 1: 上傳檔案
#st.header("Step 1:Upload Your File（CSV）")

with st.expander("📄 View the file format & Download the Sample File"):
    st.markdown("""
    Please make sure the file format you upload contains the following fields：
    - `Page`
    - `Query`
    - `Clicks`
    - `Impressions`
    - `CTR`
    - `Position`
    
    Example：
    ```
    Page,Query,Clicks,Impressions,CTR,Position
    https://drive.google.com/file/d/1h-1gdm0ubTHkBK7VekFso1_PZo0u7NV_/view?usp=sharing
    ```
    """)

with st.expander("⚙️ Basic Settings - Parameters Setting"):
    st.markdown("The parameters will be used for keyword classification")
    impression_threshold = st.number_input(
        "🔍 Impressions Threshold", min_value=0, value=100, step=10
    )
    ctr_threshold = st.slider(
        "🔍CTR (%) Threshold", min_value=0.0, max_value=100.0, value=1.0, step=0.1
    )
    tone_options = {
    "Professional & Focused": "Use a professional and informative tone. Be concise, accurate, and emphasize value.",
    "Friendly & Trustworthy": "Use a warm and approachable tone. Write like you’re helping a friend make a good decision.",
    "Inspiring & Motivational": "Use a bold and inspiring tone. Spark curiosity and confidence in the reader.",
    "Conversationa": "Use a natural, casual tone like a real human talking. Make it relatable and easy to read.",
    "Persuasive & Energetic": "Use a persuasive and energetic tone. Create urgency and excitement to encourage clicks."
}
    tone_choice = st.selectbox("✍️ AI Tone of Voice", list(tone_options.keys()))
    tone_instruction = tone_options[tone_choice]
    st.markdown(f"""
    - Current Setting： Focus on `Impressions >= {impression_threshold}` and `CTR >= {ctr_threshold:.1f}%` Keywords。
    """)

# 開始上傳流程
uploaded_file = st.file_uploader("📤 Please upload a CSV file containing keyword data", type=["csv"])

if uploaded_file is not None:
    # Check if OpenAI key is provided
    if not st.session_state.get("OPENAI_API_KEY"):
        st.error("❌ Please enter your OpenAI API key in the sidebar before uploading a file.")
        st.stop()  # Prevent further execution
    try:
        df = pd.read_csv(uploaded_file)

        required_columns = ['Page', 'Query', 'Clicks', 'Impressions', 'CTR', 'Position']
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            st.error(f"❌ Required fields are missing：{', '.join(missing_cols)}")
        else:
            # 數值清洗
            df['Impressions'] = df['Impressions'].astype(str).str.replace(',', '', regex=False)
            df['Impressions'] = pd.to_numeric(df['Impressions'], errors='coerce')

            df['CTR'] = df['CTR'].astype(str).str.replace('%', '', regex=False)
            df['CTR'] = pd.to_numeric(df['CTR'], errors='coerce') / 100

            for col in ['Clicks', 'Position']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            if df[['Clicks', 'Impressions', 'CTR', 'Position']].isnull().values.any():
                st.warning("⚠️ Some values failed to convert, please check the data")

            st.success("✅ The file was uploaded successfully, the fields and format are correct")
            st.dataframe(df.head())

            # Step 2: 關鍵字分類與 Action Code 分析
            if st.button("Step 2 - Perform keyword pre-processing analysis"):
                df["Total_Clicks_Page"] = df.groupby("Page")["Clicks"].transform("sum")
                df["Click_Share"] = df["Clicks"] / df["Total_Clicks_Page"]
                df["Keyword_Importance"] = df.apply(lambda row: classify_keyword_importance(row, impression_threshold),axis=1)
                df_focus = df[df["Keyword_Importance"].isin(["Primary", "Secondary"])].copy()
                avg_ctr = df_focus["CTR"].mean()

                df_focus["Action_Code"] = df_focus.apply(lambda row: classify_action(row, avg_ctr, impression_threshold), axis=1)
                st.session_state["df_focus"] = df_focus  # ➜ 儲存 df_focus
                st.success("🎯 Complete. The following are recommended optimization keywords.")
                st.dataframe(df_focus)

        #Step3------
        if st.button("Step 3 - Get Current Title & Meta"):
            if "df_focus" not in st.session_state:
                st.warning("Please perform Step 2 analysis before you can capture。")
            else:
                df_focus = st.session_state["df_focus"]
                unique_urls = df_focus["Page"].unique()
                total = len(unique_urls)

                st.info(f"🔎{total} pages will be fetched, please wait...")
                progress_bar = st.progress(0, text="正在擷取中...")

                # 擷取 Title & Meta
                title_meta_dict = {}
                for idx, url in enumerate(unique_urls):
                    title, meta = fetch_title_and_meta(url)
                    title_meta_dict[url] = {
                        "Current_Title": title,
                        "Current_Meta": meta
                    }
                    progress = int((idx + 1) / total * 100)
                    progress_bar.progress(progress, text=f"Capturing... ({idx + 1}/{total})")

                progress_bar.empty()

                # 合併結果
                df_title_meta = pd.DataFrame.from_dict(title_meta_dict, orient="index").reset_index()
                df_title_meta.rename(columns={"index": "Page"}, inplace=True)
                df_focus = df_focus.merge(df_title_meta, on="Page", how="left")

                # 建立 URL_ID 與排序
                df_focus["URL_ID"] = pd.factorize(df_focus["Page"])[0] + 1
                df_focus.sort_values(by="URL_ID", inplace=True)
                st.session_state["df_focus"] = df_focus

                # 篩選可優化關鍵字
                df_focus_action = df_focus[df_focus["Action_Code"] != "no_action"]
                grouped = df_focus_action.groupby("URL_ID")

                # 建立 summary 資料
                pages_data = []
                for url_id, group in grouped:
                    group_sorted = group.sort_values("Click_Share", ascending=False).head(10)
                    keywords = group_sorted["Query"].tolist()
                    keyword_importance = group_sorted["Keyword_Importance"].tolist()
                    current_title = group_sorted.iloc[0]["Current_Title"]
                    current_meta = group_sorted.iloc[0]["Current_Meta"]
                    url = group_sorted.iloc[0]["Page"]

                    pages_data.append({
                        "URL_ID": url_id,
                        "Page": url,
                        "Keywords": keywords,
                        "Keyword_Importance": keyword_importance,
                        "Current_Title": current_title,
                        "Current_Meta": current_meta
                    })

                df_pages_summary = pd.DataFrame(pages_data)
                st.success("✅ All pages successfully retrieved Title & Meta！")
                st.session_state["df_pages_summary"] = df_pages_summary
                df_pages_summary = st.session_state["df_pages_summary"]
                st.dataframe(df_pages_summary.head())

        #Step4------
        if st.button("Step 4 - Automatically generate suggestions Title & Meta"):
            if "df_pages_summary" not in st.session_state:
                st.warning("⚠️ Please execute Step 3 to capture the content first")
            else:
                df_pages_summary = st.session_state["df_pages_summary"]
                pages_data = df_pages_summary.to_dict(orient="records")

                generated_results = []
                with st.spinner("New Title & Meta is being generated, please wait..."):
                    for page in pages_data:
                        try:
                            prompt = create_prompt_page_level(page, tone_instruction)
                            result = generate_title_meta(prompt)
                            title, meta = extract_title_meta(result)
                        except Exception as e:
                            title, meta = "❌ An error occurred", str(e)

                        page["Suggested_Title"] = title
                        page["Suggested_Meta"] = meta
                        generated_results.append(page)

                # 轉回 DataFrame
                df_final = pd.DataFrame(generated_results)

                # 保留欄位順序
                df_final = df_final[[
                    "URL_ID",
                    "Page",
                    "Current_Title",
                    "Current_Meta",
                    "Suggested_Title",
                    "Suggested_Meta",
                    "Keywords",
                    "Keyword_Importance"
                ]]

                # 顯示結果與儲存
                st.success("✅ All suggestions were successfully output!")
                st.dataframe(df_final)
                st.session_state["df_final"] = df_final
                csv = df_final.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Download the result (CSV)",
                    data=csv,
                    file_name="seo_suggestions.csv",
                    mime='text/csv'
        )




    except Exception as e:
        st.error(f"❌ An error occurred while reading the archive:{e}")
else:
    st.info("Please upload a correctly formatted CSV keyword file")

