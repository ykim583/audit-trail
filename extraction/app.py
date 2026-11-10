import streamlit as st
 
from excel_importer import FK_ENGAGEMENT_ID, load_workbook
 
st.set_page_config(page_title="Audit Trail", layout="wide")
 
 
@st.cache_data
def get_data():
    return load_workbook()
 
 
data = get_data()
eng, pbc, cf = data["Engagements"], data["PBC_Requests"], data["Confirmations"]
 
st.title("Audit Trail — 감사 자료 현황")
 
# ---- Sidebar: filter by engagement (FK)
labels = {"ALL": "전체"} | dict(zip(eng[FK_ENGAGEMENT_ID], eng[FK_ENGAGEMENT_ID] + " · " + eng["client_name"]))
selected = st.sidebar.selectbox("감사 건", list(labels), format_func=labels.get)
 
if selected != "ALL":
    eng = eng[eng[FK_ENGAGEMENT_ID] == selected]
    pbc = pbc[pbc[FK_ENGAGEMENT_ID] == selected]
    cf = cf[cf[FK_ENGAGEMENT_ID] == selected]
 
# ---- Summary numbers
c1, c2, c3, c4 = st.columns(4)
c1.metric("PBC 요청", len(pbc))
c2.metric("PBC 미수령", int((pbc["status"] == "REQUESTED").sum()))
c3.metric("조회서", len(cf))
c4.metric("조회서 미회수", int(cf["status"].isin(["DRAFT", "SENT"]).sum()))
 
# ---- Tables
tab_pbc, tab_cf, tab_eng = st.tabs(["PBC 요청", "조회서", "감사 건"])
with tab_pbc:
    st.dataframe(pbc, hide_index=True)
with tab_cf:
    st.dataframe(cf, hide_index=True)
with tab_eng:
    st.dataframe(eng, hide_index=True)