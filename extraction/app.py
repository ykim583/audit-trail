from pathlib import Path

import pandas as pd
import streamlit as st

from extraction.define import ADMIN_DIR, FK_ENGAGEMENT_ID, OrderStatus, WORKBOOK_PATH
from excel_importer import load_workbook, status_update

# ---- HTML page configuration
st.set_page_config(page_title="Audit Trail", layout="wide")

st.title("Excel Data Uploader")

# Create the file uploader widget
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        ADMIN_DIR.mkdir(parents=True, exist_ok=True)
        upload_path = ADMIN_DIR / Path(uploaded_file.name).name

        if upload_path.exists():
            st.error(f"File already exists and was not overwritten: {upload_path.name}")
        else:
            upload_path.write_bytes(uploaded_file.getvalue())
            st.success(f"File saved to {upload_path}")
            st.write(f"**Rows:** {df.shape[0]} | **Columns:** {df.shape[1]}")
            st.dataframe(df)
    except (OSError, ValueError, ImportError) as error:
        st.error(f"Could not read or save the uploaded Excel file: {error}")
 
# ---- Front End: Streamlit UI 
st.title("Audit Trail — 감사 자료 현황")

# ---- Load the workbook data
@st.cache_data
def get_data(workbook_path: str):
    return load_workbook(Path(workbook_path))

# ---- Front End: Streamlit UI for Workbook Selection
workbook_files = sorted(
    (
        path
        for path in ADMIN_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".xlsx", ".xls"}
    ),
    key=lambda path: path.name.lower(),
)
if not workbook_files:
    st.error(f"No Excel workbooks found in {ADMIN_DIR}")
    st.stop()

default_workbook = next(
    (index for index, path in enumerate(workbook_files) if path == WORKBOOK_PATH),
    0,
)
selected_workbook = st.sidebar.selectbox(
    "Excel 파일",
    workbook_files,
    index=default_workbook,
    format_func=lambda path: path.name,
)

data = get_data(str(selected_workbook))
eng, pbc, cf = data["Engagements"], data["PBC_Requests"], data["Confirmations"]
 
# ---- Front End: Sidebar UI for Engagement Selection
labels = {"ALL": "전체"} | dict(zip(eng[FK_ENGAGEMENT_ID], eng[FK_ENGAGEMENT_ID] + " · " + eng["client_name"]))
selected = st.sidebar.selectbox("감사 건", list(labels), format_func=labels.get)
 
if selected != "ALL":
    eng = eng[eng[FK_ENGAGEMENT_ID] == selected]
    pbc = pbc[pbc[FK_ENGAGEMENT_ID] == selected]
    cf = cf[cf[FK_ENGAGEMENT_ID] == selected]

# ---- Front End: Sidebar UI for Status Filter
status_names = list(
    dict.fromkeys(
        [
            *(status.name for status in OrderStatus),
            *pbc["status"].dropna().astype(str).unique(),
            *cf["status"].dropna().astype(str).unique(),
        ]
    )
)
status_labels = {"ALL": "전체"} | {
    name: status_update(OrderStatus[name]) if name in OrderStatus.__members__ else name
    for name in status_names
}
selected_status = st.sidebar.selectbox(
    "상태", list(status_labels), format_func=status_labels.get
)

if selected_status != "ALL":
    pbc = pbc[pbc["status"] == selected_status]
    cf = cf[cf["status"] == selected_status]
 
# ---- Summary numbers
c1, c2, c3, c4 = st.columns(4)
c1.metric("PBC 요청", len(pbc))
c2.metric("PBC 부재 정보 요청 중", int((pbc["status"] == "REQUESTED").sum()))
c3.metric("조회서", len(cf))
c4.metric("조회서 회신 대기 중", int((cf["status"] == "SENT").sum()))

# ---- Tables
tab_pbc, tab_cf, tab_eng = st.tabs(["PBC 요청", "조회서", "감사 건"])
with tab_pbc:
    st.dataframe(pbc, hide_index=True)
with tab_cf:
    st.dataframe(cf, hide_index=True)
with tab_eng:
    st.dataframe(eng, hide_index=True)
