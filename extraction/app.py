from pathlib import Path
import pandas as pd
import streamlit as st

from define import (
    ALLOWED,
    ADMIN_DIR,
    FK_ENGAGEMENT_ID,
    OrderStatus,
    WORKBOOK_PATH,
)
from excel_importer import (
    load_workbook,
    save_pbc_statuses,
    status_update,
)

# ---- HTML page configuration
st.set_page_config(page_title="Audit Trail", layout="wide")
st.title("Excel Data Uploader")
st.title("Audit Trail — 감사 자료 현황")

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
            st.session_state["selected_workbook"] = upload_path # --- After upload, set the selected workbook to the newly uploaded file
            st.success(f"File saved to {upload_path}")
            st.write(f"**Rows:** {df.shape[0]} | **Columns:** {df.shape[1]}")
            st.dataframe(df)
    except (OSError, ValueError, ImportError) as error:
        st.error(f"Could not read or save the uploaded Excel file: {error}")

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
    key="selected_workbook",
)


# --- Load the detailed data from the selected workbook
data = get_data(str(selected_workbook))
eng, all_pbc, cf = data["Engagements"], data["PBC_Requests"], data["Confirmations"]
pbc = all_pbc.copy()
 
# ---- Sidebar filters
with st.sidebar:
    labels = {"ALL": "전체"} | dict( # --- 감사건 풀네임 (ID + client_name)s
        zip(
            eng[FK_ENGAGEMENT_ID],
            eng[FK_ENGAGEMENT_ID] + " · " + eng["client_name"],
        )
    )
    selected = st.selectbox("감사 건", list(labels), format_func=labels.get) # --- 감사건 선택시, 해당 감사건에 속한 PBC 요청과 조회서만 표시
    if selected != "ALL":
        eng = eng[eng[FK_ENGAGEMENT_ID] == selected]
        pbc = pbc[pbc[FK_ENGAGEMENT_ID] == selected]
        cf = cf[cf[FK_ENGAGEMENT_ID] == selected]

    status_names = list( # --- 감사 자료의 status 컬럼에 있는 모든 상태값을 가져와서, Streamlit selectbox 에 표시
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
    selected_status = st.selectbox(
        "상태", list(status_labels), format_func=status_labels.get
    )
    if selected_status != "ALL":
        pbc = pbc[pbc["status"] == selected_status]
        cf = cf[cf["status"] == selected_status]
 
# ---- Front End: 열별 통계 (Metrics)
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("전체 감사건", len(eng))
c2.metric("PBC 전체", len(pbc))
c3.metric("PBC 부재 정보 요청 중", int((pbc["status"] == "REQUESTED").sum()))
c4.metric("조회서", len(cf))
c5.metric("조회서 회신 대기 중", int((cf["status"] == "SENT").sum()))


# ---- Front End: 필터링된 감사 자료를 탭으로 표시
tab_pbc, tab_cf, tab_eng = st.tabs(["PBC 요청", "조회서", "감사 건"])
with tab_pbc:
    edited_pbc = st.data_editor(
        pbc,
        column_config={ # --- status 컬럼은 Selectbox 로 표시되도록 설정
            "status": st.column_config.SelectboxColumn(
                "상태",
                options=[
                    OrderStatus.REQUESTED.name, # --- 안에 Response는 .value 로 표시되도록, 내부적으로는 name 으로 저장
                    OrderStatus.RECEIVED.name,
                    OrderStatus.REVIEWED.name,
                ],
            ),
        },
        disabled=[column for column in pbc if column != "status"], # --- status 컬럼만 편집 가능하도록 설정
        hide_index=True,
        key=f"pbc_editor_{selected_workbook.name}",
    )

    # --- Check for status changes and validate against allowed transitions 
    changes = edited_pbc.set_index("request_id")["status"].to_dict()
    previous = all_pbc.set_index("request_id")["status"].to_dict()
    changes = {
        request_id: status
        for request_id, status in changes.items() 
        if previous[request_id] != status
    }

    invalid = [
        (previous[request_id], status)
        for request_id, status in changes.items()
        if (previous[request_id], status) not in ALLOWED
    ]
    if invalid:
        st.error(f"Status transition is not allowed: {invalid}")
    elif changes: # --- If there are valid changes, update the status in the original DataFrame and save to Excel
        all_pbc["status"] = all_pbc["request_id"].map(changes).fillna(all_pbc["status"])
        try:
            save_pbc_statuses(selected_workbook, all_pbc)
        except (OSError, ValueError) as error:
            st.error(f"Could not save PBC status changes: {error}")
        else:
            get_data.clear()
            st.rerun()
with tab_cf:
    st.dataframe(cf, hide_index=True)
with tab_eng:
    st.dataframe(eng, hide_index=True)
