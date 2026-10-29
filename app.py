from __future__ import annotations

import io
import os

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import filter_transactions, grouped_fraud, high_value_fraud, kpis
from src.ai_assistant import answer_question, test_gemini_connection
from src.config import gemini_api_key, gemini_model
from src.data_loader import DATA_FILE, load_transactions
from src.report_generator import build_report

st.set_page_config(page_title="FinSight | Fraud Intelligence", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{color-scheme:dark;--bg:#08111F;--surface:#111D2E;--surface2:#162438;--text:#F1F5F9;--secondary:#CBD5E1;--muted:#94A3B8;--border:#334155;--accent:#38BDF8;--fraud:#F87171;--success:#34D399}
html,body,[data-testid="stAppViewContainer"],.stApp{background-color:var(--bg)!important;color:var(--text)!important;font-family:'DM Sans',system-ui,sans-serif}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 15% 0%,#13243a 0,transparent 36%),var(--bg)!important}
header[data-testid="stHeader"]{background:rgba(8,17,31,.96)!important;border-bottom:1px solid rgba(51,65,85,.55);color:var(--text)!important}
header[data-testid="stHeader"] button,[data-testid="stToolbar"]{color:var(--text)!important}
[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{background:var(--surface)!important;padding-top:1.1rem}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] span,[data-testid="stSidebar"] small{color:var(--text)!important}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:var(--muted)!important}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:9px;padding:.2rem .45rem;transition:background-color .15s ease}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#1B2B40!important}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#153149!important;outline:1px solid #24506B}
[data-testid="stSidebar"] [role="radio"]{accent-color:var(--accent)}
.block-container{padding-top:1.6rem;max-width:1500px;color:var(--text)}
h1,h2,h3,h4,h5,h6{font-family:Manrope,'DM Sans',system-ui,sans-serif;color:var(--text)!important;letter-spacing:-.025em}
p,li,label,small,span{color:var(--secondary)}
[data-testid="stMetric"]{background:linear-gradient(150deg,#14243A,#101B2B)!important;padding:18px 20px;border:1px solid var(--border)!important;border-radius:14px}
[data-testid="stMetricLabel"],[data-testid="stMetricLabel"] *{color:var(--secondary)!important}
[data-testid="stMetricValue"],[data-testid="stMetricValue"] *{font-family:Manrope,sans-serif;color:var(--text)!important}
.hero{padding:24px 28px;background:linear-gradient(110deg,#12243A,#10212E);border:1px solid #294158;border-radius:18px;margin-bottom:20px}
.hero small,.hero .muted{color:var(--muted)!important}.hero h1{margin:4px 0 5px;font-size:clamp(1.65rem,3vw,2.25rem);line-height:1.2;color:var(--text)!important}
input,textarea,[data-baseweb="input"] input,[data-baseweb="textarea"] textarea{background:#0B1727!important;color:var(--text)!important;-webkit-text-fill-color:var(--text)!important;caret-color:var(--accent)!important;border-color:var(--border)!important}
input::placeholder,textarea::placeholder,[data-baseweb="input"] input::placeholder,[data-baseweb="textarea"] textarea::placeholder{color:#A9B8CA!important;-webkit-text-fill-color:#A9B8CA!important;opacity:1!important}
input:focus,textarea:focus,[data-baseweb="input"]:focus-within,[data-baseweb="textarea"]:focus-within{outline:none!important;border-color:var(--accent)!important;box-shadow:0 0 0 2px rgba(56,189,248,.25)!important}
[data-testid="stChatInput"]{background:#0B1727!important;border:1px solid #475569!important;border-radius:14px!important;box-shadow:0 8px 26px rgba(0,0,0,.18)!important;transition:border-color .15s,box-shadow .15s}
[data-testid="stChatInput"]:focus-within{border-color:var(--accent)!important;box-shadow:0 0 0 3px rgba(56,189,248,.22)!important}
[data-testid="stChatInput"] textarea{background:transparent!important;color:var(--text)!important;-webkit-text-fill-color:var(--text)!important;caret-color:#7DD3FC!important;font-size:16px!important;line-height:1.5!important;padding:14px 16px!important;min-height:54px!important}
[data-testid="stChatInput"] textarea::placeholder{color:#A9B8CA!important;-webkit-text-fill-color:#A9B8CA!important;opacity:1!important}
[data-testid="stChatInput"] button{background:#153149!important;color:#F1F5F9!important;border:1px solid #3C6C8D!important;border-radius:10px!important;min-width:42px!important;min-height:40px!important}
[data-testid="stChatInput"] button svg{fill:#F1F5F9!important;color:#F1F5F9!important}
[data-testid="stChatInput"] button:disabled{background:#172335!important;color:#718096!important;border-color:#334155!important;opacity:.75}
[data-testid="stSelectbox"] [data-baseweb="select"]>div,[data-testid="stMultiSelect"] [data-baseweb="select"]>div{background:#0B1727!important;border-color:var(--border)!important;color:var(--text)!important}
[data-testid="stSelectbox"] [data-baseweb="select"] span,[data-testid="stMultiSelect"] [data-baseweb="select"] span{color:var(--text)!important}
[data-testid="stMultiSelect"] [data-baseweb="tag"]{background:#16415B!important;border:1px solid #32708F!important;border-radius:7px!important}
[data-testid="stMultiSelect"] [data-baseweb="tag"] *,[data-testid="stMultiSelect"] [data-baseweb="tag"] svg{color:#F1F5F9!important;fill:#F1F5F9!important}
[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"]{background:#111D2E!important;color:var(--text)!important;border:1px solid var(--border)!important}
[role="option"],[data-baseweb="menu"] li{background:#111D2E!important;color:var(--text)!important}
[role="option"]:hover,[role="option"][aria-selected="true"],[data-baseweb="menu"] li:hover{background:#1D344B!important;color:#fff!important}
[data-testid="stDateInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{background:#0B1727!important;color:var(--text)!important;-webkit-text-fill-color:var(--text)!important}
[data-testid="stSlider"] [role="slider"]{background:var(--accent)!important;border-color:#E0F2FE!important}
[data-testid="stSlider"] [data-testid="stTickBar"]{background:var(--border)!important}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button{background:#153149!important;color:#F1F5F9!important;border:1px solid #3C6C8D!important;border-radius:9px!important;font-weight:600!important;transition:background .15s,border-color .15s}
[data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover{background:#1A4562!important;border-color:var(--accent)!important;color:#fff!important}
[data-testid="stButton"] button:focus-visible,[data-testid="stDownloadButton"] button:focus-visible{outline:3px solid rgba(56,189,248,.65)!important;outline-offset:2px!important}
[data-testid="stButton"] button:disabled,[data-testid="stDownloadButton"] button:disabled{background:#182436!important;color:#8795A8!important;border-color:#334155!important;opacity:.75}
[data-testid="stCheckbox"] label,[data-testid="stRadio"] label{color:var(--text)!important}
[data-testid="stAlert"]{border:1px solid var(--border)!important;border-radius:12px!important}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid var(--border)!important;border-radius:12px!important;overflow:hidden}
[data-testid="stJson"]{background:#0B1727!important;border:1px solid var(--border)!important;border-radius:10px!important;color:var(--text)!important}
[data-testid="stCodeBlock"]{background:#0B1727!important;border:1px solid var(--border)!important;border-radius:10px!important}
[data-testid="stExpander"]{background:#101B2B!important;border:1px solid var(--border)!important;border-radius:11px!important}
.stMarkdown a{color:#7DD3FC!important;text-decoration-color:#38BDF8}
hr{border-color:var(--border)!important}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner="Loading and validating transaction data…")
def get_data():
    return load_transactions(DATA_FILE)

try:
    df, metadata = get_data()
except Exception as exc:
    st.error(f"Could not load the transaction dataset: {exc}")
    st.stop()

st.sidebar.markdown("## ◈ FinSight")
st.sidebar.caption("FINANCIAL FRAUD INTELLIGENCE")
page = st.sidebar.radio("Navigation", ["Executive Overview", "Fraud Explorer", "Risk Intelligence", "AI Fraud Assistant", "AI Reports", "About the Project"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.markdown("### Analysis filters")
subset = df
if "Transaction_Date" in df and df["Transaction_Date"].notna().any():
    low, high = df["Transaction_Date"].min().date(), df["Transaction_Date"].max().date()
    picked = st.sidebar.date_input("Transaction date", (low, high), min_value=low, max_value=high)
    if isinstance(picked, tuple) and len(picked) == 2:
        subset = filter_transactions(subset, {"date_range": picked})
sidebar_filters = {}
for col in ("City", "Payment_Method", "Merchant_Category"):
    if col in df:
        options = sorted(df[col].dropna().astype(str).unique().tolist())
        val = st.sidebar.multiselect(col.replace("_", " "), options)
        if val:
            sidebar_filters[col] = val
if sidebar_filters:
    subset = filter_transactions(subset, sidebar_filters)
st.sidebar.divider()
st.sidebar.caption("Source: financial_fraud_dataset_10000.csv · Fraud status reflects supplied labels.")

def header(kicker: str, title: str, subtitle: str):
    st.markdown(f'<div class="hero"><small>{kicker}</small><h1>{title}</h1><span class="muted">{subtitle}</span></div>', unsafe_allow_html=True)

def chart(fig, height=360):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"family":"DM Sans","color":"#c4d0df"}, margin={"l":15,"r":15,"t":55,"b":15}, height=height, legend_title_text="")
    fig.update_xaxes(gridcolor="#203044", zerolinecolor="#203044")
    fig.update_yaxes(gridcolor="#203044", zerolinecolor="#203044")
    st.plotly_chart(fig, width="stretch")


def answer_model_hint() -> str:
    return f"{gemini_model()} ·"


def render_result_table(records: list[dict], height: int = 300) -> None:
    frame = pd.DataFrame(records)
    if frame.empty:
        st.info("No matching records in the current filters.")
        return
    labels = {
        "Payment_Method": "Payment method", "Merchant_Category": "Merchant category", "City": "City",
        "fraud_count": "Fraud-labelled transactions", "fraud_amount": "Labelled amount (INR)",
        "Transaction_ID": "Transaction ID", "Amount": "Transaction amount (INR)",
        "Risk_Score": "Risk score", "threshold": "Amount threshold (INR)",
        "count": "Fraud-labelled transactions", "fraud_pct": "Fraud-labelled rate (%)",
        "avg_risk": "Average risk score", "transactions": "Transactions",
    }
    renamed = frame.rename(columns=labels)
    column_config = {}
    for source, label in labels.items():
        if source in frame.columns and ("amount" in source.casefold() or source == "threshold"):
            column_config[label] = st.column_config.NumberColumn(label, format="₹ %.2f")
        elif source in frame.columns and source in ("fraud_count", "count", "transactions"):
            column_config[label] = st.column_config.NumberColumn(label, format="%d")
        elif source in frame.columns and source in ("Risk_Score", "avg_risk"):
            column_config[label] = st.column_config.NumberColumn(label, format="%.2f")
        elif source in frame.columns and source == "fraud_pct":
            column_config[label] = st.column_config.NumberColumn(label, format="%.2f%%")
    st.dataframe(renamed, width="stretch", hide_index=True, height=height, column_config=column_config)


def render_ai_results(answer: dict) -> None:
    if not answer.get("supported"):
        st.info(answer.get("explanation", answer.get("message", "This question is not supported.")))
        return
    st.markdown("**Deterministic answer · calculated with Pandas**")
    st.caption("These figures come from the dataset and current sidebar filters. Display formatting does not change the underlying values.")
    results = answer.get("results", {})
    if answer.get("operation") == "amount threshold":
        threshold, count = answer.get("threshold"), answer.get("count", 0)
        col1, col2 = st.columns(2)
        col1.metric("Amount threshold", f"₹{threshold:,.2f}" if threshold is not None else "Unavailable")
        col2.metric("Fraud-labelled transactions", f"{count:,}")
        render_result_table(results)
    elif isinstance(results, dict) and "kpis" in results:
        kpis = results["kpis"]
        cols = st.columns(4)
        cols[0].metric("Transactions", f"{kpis.get('transactions', 0):,}")
        cols[1].metric("Fraud-labelled", f"{kpis.get('fraud_count', 0):,}")
        cols[2].metric("Fraud-labelled rate", f"{kpis.get('fraud_pct', 0):.2f}%")
        cols[3].metric("Labelled amount", f"₹{kpis.get('fraud_labelled_amount', 0):,.2f}")
        for key, label in (("Payment_Method", "Payment method"), ("Merchant_Category", "Merchant category"), ("City", "City")):
            if results.get(key):
                st.markdown(f"**{label} breakdown**")
                render_result_table(results[key], height=230)
    elif isinstance(results, list):
        render_result_table(results)
    else:
        st.info("The calculation returned no tabular results.")
    with st.expander("Technical details (raw calculation output)"):
        st.json(results)
    st.markdown("**Gemini-generated interpretation**")
    st.write(answer.get("explanation", "No explanation was generated."))

if page == "Executive Overview":
    header("FRAUD MONITORING  /  EXECUTIVE VIEW", "Financial intelligence, at a glance", "Explore the supplied 2025 transaction records and their fraud labels.")
    m = kpis(subset)
    cols = st.columns(5)
    labels = [("Transactions", f"{m['transactions']:,}"),("Fraud-labelled", f"{m['fraud_count']:,}"),("Fraud-labelled rate", f"{m['fraud_pct']:.2f}%"),("Labelled transaction amount", f"₹{m['fraud_labelled_amount']:,.0f}"),("Average risk score", f"{m['avg_risk']:.1f}" if m['avg_risk'] is not None else "N/A")]
    for c,(label,value) in zip(cols,labels): c.metric(label,value)
    st.caption("The amount KPI is the sum of Amount for rows labelled Fraud; it is not confirmed financial loss. Risk score is the dataset field, not a model trained by this application.")
    left,right=st.columns(2)
    with left:
        st.subheader("Fraud labels over time")
        if "Transaction_Date" in subset:
            trend=subset.assign(Month=subset.Transaction_Date.dt.to_period("M").astype(str)).groupby(["Month","Fraud_Status"],dropna=False).size().reset_index(name="Transactions")
            chart(px.line(trend,x="Month",y="Transactions",color="Fraud_Status",markers=True,color_discrete_map={"Fraud":"#f2b66d","Legitimate":"#52d6d0"}))
        else: st.info("No usable date column is available.")
    with right:
        st.subheader("Fraud-labelled vs legitimate")
        chart(px.pie(subset,names="Fraud_Status",hole=.68,color="Fraud_Status",color_discrete_map={"Fraud":"#f2b66d","Legitimate":"#52d6d0"}))
    left,right=st.columns(2)
    for col,container,title in (("Payment_Method",left,"Fraud counts by payment method"),("Merchant_Category",right,"Fraud counts by merchant category")):
        with container:
            st.subheader(title)
            g=grouped_fraud(subset,col)
            if len(g): chart(px.bar(g.sort_values("fraud_count"),x="fraud_count",y=col,orientation="h",color_discrete_sequence=["#52d6d0"],labels={"fraud_count":"Fraud-labelled transactions",col:col.replace("_"," ")}))
            else: st.info(f"{col} is unavailable.")
    left,right=st.columns(2)
    with left:
        st.subheader("Fraud-label distribution by city")
        g=grouped_fraud(subset,"City")
        if len(g): chart(px.bar(g.head(10),x="City",y="fraud_count",color="fraud_count",color_continuous_scale=["#19414b","#52d6d0"],labels={"fraud_count":"Fraud-labelled transactions"}))
        else: st.info("City data is unavailable.")
    with right:
        st.subheader("Risk score distribution")
        if "Risk_Score" in subset: chart(px.histogram(subset,x="Risk_Score",color="Fraud_Status",nbins=24,barmode="overlay",opacity=.78,color_discrete_map={"Fraud":"#f2b66d","Legitimate":"#52d6d0"}))
        else: st.info("Risk_Score is not available.")

elif page == "Fraud Explorer":
    header("INVESTIGATION WORKSPACE", "Fraud explorer", "Combine filters, inspect records, and export the currently matching transactions.")
    filters={}
    for col in ("City","Payment_Method","Merchant_Category","Fraud_Status"):
        if col in subset:
            opts=sorted(subset[col].dropna().astype(str).unique().tolist())
            filters[col]=st.multiselect(col.replace("_"," "),opts,key=f"explore_{col}") if col!="Fraud_Status" else st.selectbox("Fraud status",["All"]+opts)
    filters={k:v for k,v in filters.items() if v and v!="All"}
    filters["search"]=st.text_input("Search transaction ID",placeholder="e.g. TXN100123")
    for col,key in (("Amount","amount_range"),("Risk_Score","risk_range")):
        if col in subset:
            numeric=pd.to_numeric(subset[col],errors="coerce").dropna()
            if not numeric.empty:
                lo,hi=float(numeric.min()),float(numeric.max())
                filters[key]=(lo,hi) if lo == hi else st.slider(col.replace("_"," "),lo,hi,(lo,hi))
    result=filter_transactions(subset,filters)
    st.caption(f"{len(result):,} matching records · Fraud labels are source data, not a new investigation flag.")
    display=[c for c in ["Transaction_ID","Transaction_Date","Amount","Fraud_Status","Risk_Score","Payment_Method","Merchant_Category","City","Transaction_Type","Device_Type","Bank_Name"] if c in result]
    st.dataframe(result[display],width="stretch",hide_index=True,height=420)
    if not result.empty and "Transaction_ID" in result:
        selected=st.selectbox("Transaction detail",result["Transaction_ID"].astype(str).tolist())
        with st.expander("Selected transaction"):
            st.json(result[result.Transaction_ID.astype(str)==selected].iloc[0].drop(labels=["_is_fraud"],errors="ignore").to_dict())
    st.download_button("Download filtered CSV",result.drop(columns=["_is_fraud"],errors="ignore").to_csv(index=False).encode("utf-8-sig"),"filtered_transactions.csv","text/csv",disabled=result.empty)

elif page == "Risk Intelligence":
    header("RISK INTELLIGENCE", "Patterns for analyst review", "Descriptive summaries identify where further validation may be useful; they do not show causation.")
    a,b=st.columns(2)
    for container,col,title in ((a,"Payment_Method","Fraud count and labelled amount by payment method"),(b,"Merchant_Category","Fraud count by merchant category")):
        with container:
            st.subheader(title); g=grouped_fraud(subset,col)
            if len(g): chart(px.bar(g,x=col,y="fraud_count",hover_data={"fraud_amount":":,.2f"},color="fraud_count",color_continuous_scale=["#1b4850","#52d6d0"]))
            else: st.info("No supported data for this breakdown.")
    a,b=st.columns(2)
    with a:
        st.subheader("City distribution")
        g=grouped_fraud(subset,"City")
        if len(g): chart(px.bar(g.head(10),x="City",y="fraud_count",color_discrete_sequence=["#f2b66d"]))
    with b:
        st.subheader("Risk-score comparison")
        if "Risk_Score" in subset: chart(px.box(subset,x="Fraud_Status",y="Risk_Score",color="Fraud_Status",color_discrete_map={"Fraud":"#f2b66d","Legitimate":"#52d6d0"}))
    threshold=st.number_input("High-value threshold",min_value=0.0,value=10000.0,step=1000.0)
    high=high_value_fraud(subset,threshold)
    st.metric(f"Fraud-labelled transactions above ₹{threshold:,.0f}",f"{len(high):,}")
    st.dataframe(high.drop(columns=["_is_fraud"],errors="ignore"),width="stretch",hide_index=True)
    if "Payment_Method" in subset:
        st.subheader("Payment-method summary")
        st.dataframe(grouped_fraud(subset,"Payment_Method"),width="stretch",hide_index=True)
    st.info("Counts are descriptive and depend on the dataset labels. Group counts do not adjust for transaction volume; observed association does not establish cause. No predictive model is implemented here.")

elif page == "AI Fraud Assistant":
    header("GROUNDED DATA ASSISTANT", "Ask the dataset", "Pandas calculates the answer first; Gemini explains only the compact results.")
    st.warning("AI explanations require verification and are not a substitute for professional fraud investigation.")
    api_key = gemini_api_key()
    connection = st.session_state.get("gemini_connection", {})
    if not api_key:
        st.error("Gemini API key missing · add GEMINI_API_KEY to the ignored local .env file.")
    elif connection.get("status") == "verified":
        st.success(connection.get("message", "Gemini connection verified."))
    elif connection.get("status"):
        status_labels = {
            "authentication_failed": "Gemini authentication failed",
            "unsupported_model": "Gemini model unavailable",
            "quota_exceeded": "Gemini quota exceeded",
            "temporarily_unavailable": "Gemini temporarily unavailable",
            "invalid_response": "Gemini returned an invalid response",
        }
        label = status_labels.get(connection.get("status"), "Gemini connection failed")
        st.error(f"{label} · {connection.get('message', 'Check the Gemini configuration.')}")
    else:
        st.info(f"Gemini configured · {answer_model_hint()} connection not verified yet.")
    if st.button("Test Gemini Connection", type="secondary", key="test_gemini_connection"):
        with st.spinner("Checking Gemini with a minimal test prompt…"):
            connection = test_gemini_connection()
        st.session_state["gemini_connection"] = connection
        if connection["status"] == "verified":
            st.success(connection["message"])
        elif connection["status"] == "missing_key":
            st.error(connection["message"])
        else:
            status_labels = {
                "authentication_failed": "Gemini authentication failed",
                "unsupported_model": "Gemini model unavailable",
                "quota_exceeded": "Gemini quota exceeded",
                "temporarily_unavailable": "Gemini temporarily unavailable",
                "invalid_response": "Gemini returned an invalid response",
            }
            label = status_labels.get(connection.get("status"), "Gemini connection failed")
            st.error(f"{label} · {connection['message']}")
    st.caption("The current sidebar date, city, payment-method, and merchant-category filters are applied to calculations here and on AI Reports. Only calculated aggregates and your question are sent to Gemini; transaction rows are not.")
    history = st.session_state.setdefault("assistant_history", [])
    for item in history:
        with st.chat_message(item["role"]):
            if item["role"] == "user":
                st.markdown(item["content"])
            elif item.get("answer"):
                render_ai_results(item["answer"])
    q = st.chat_input("Ask about fraud counts, labelled amounts, cities, or high-value records…")
    if q:
        followup_starts = ("what about", "how about", "and for", "same for", "compare that", "tell me more")
        previous = next((item["content"] for item in reversed(history) if item["role"] == "user"), "")
        calculation_question = f"{previous} {q}" if previous and len(q) < 80 and q.casefold().startswith(followup_starts) else q
        with st.spinner("Calculating and preparing an explanation…"):
            answer = answer_question(calculation_question, subset)
        if answer.get("supported"):
            st.chat_message("user").markdown(q)
            with st.chat_message("assistant"):
                render_ai_results(answer)
            history.extend([{"role": "user", "content": q}, {"role": "assistant", "answer": answer}])
        else:
            st.chat_message("user").markdown(q)
            with st.chat_message("assistant"):
                render_ai_results(answer)
            history.extend([{"role": "user", "content": q}, {"role": "assistant", "answer": answer}])
    with st.expander("Example questions"):
        st.markdown("- Which payment methods have the highest fraud counts?\n- Which merchant categories have the largest labelled amounts?\n- Show the five cities with the highest fraud counts.\n- How many fraud-labelled transactions are above 10,000?\n- Summarize the important findings.")

elif page == "AI Reports":
    header("ANALYST BRIEFING", "AI-generated fraud report", "A concise report with deterministic figures and clearly qualified interpretation.")
    st.caption("Gemini is optional. Without a key, the report remains available with calculated facts and a configuration note.")
    if st.button("Generate AI Report",type="primary"):
        st.session_state["fraud_report"] = build_report(subset,metadata)
    if st.session_state.get("fraud_report"):
        st.markdown(st.session_state["fraud_report"])
        st.download_button("Download Markdown report",st.session_state["fraud_report"],"financial_fraud_report.md","text/markdown")
    else: st.info("Generate a report to view the current filtered analysis.")

else:
    header("PROJECT NOTES", "About this analysis", "Dataset provenance, analytical definitions, and implementation boundaries.")
    st.markdown(f"""
### Supplied data
The source file contains **{metadata['source_rows']:,} rows** and **{len(df.columns)-1} source columns**. Exact repeated records ({metadata['exact_duplicates_removed']:,}) are omitted once in calculations and explorer views. The original CSV remains unchanged. Missing values are retained and ignored only where a calculation requires the absent field.

### Metric definitions
- **Fraud-labelled** means `Fraud_Status` equals `Fraud` (case-insensitive).
- **Fraud-labelled amount** is the sum of `Amount` for those labelled records. It is not confirmed loss.
- **Average risk score** uses the source `Risk_Score` field; this app does not create a score.
- Group counts are raw descriptive counts and do not account for each group's transaction volume.

### Architecture and limitations
Streamlit renders the interface; Pandas performs deterministic filters and aggregations; Plotly renders charts. A controlled intent router selects supported calculations. The official Google Gen AI SDK (`google-genai`) receives only calculated aggregate results and the question, never the transaction CSV. Unsupported questions receive a limitation message. AI output is interpretation and must be checked. No predictive model, causation analysis, or confirmed-loss measure is implemented.

### Original project assets
The existing SQL analysis, Power BI dashboard (`dashboard.pbix`), screenshots, and source dataset remain part of this project.
""")
