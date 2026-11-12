from enum import Enum
from pathlib import Path

# --- Status of the audit process
class OrderStatus(Enum):
    REQUESTED = "자료 요청"
    RECEIVED = "자료 수령"
    REVIEWED = "검토 완료"
    DRAFT = "조회서 작성"
    SENT = "조회서 전송 완료"
    RETURNED = "회신 완료"
    RECONCILED = "감사 최종 완료"
    FAILURE = "자료 오류"

# --- Path to the workbook to be imported 
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ADMIN_DIR = PROJECT_ROOT / "admin"
WORKBOOK_PATH = ADMIN_DIR / "audit_dummy_clean.xlsx"
 
# ---- Foreing key, 어떤 문서에 있건, FK 하나로 감사 문서가 어디에 속해있는지 알수있음
FK_ENGAGEMENT_ID = "engagement_id"
 
# ---- Pre-defined columns per entity: [primary key, (foreign key), fields]
ENGAGEMENT_COLUMNS = [
    FK_ENGAGEMENT_ID,  # primary key of Engagements, foreign key in the other two sheets
    "client_name", "fiscal_year", "engagement_manager", "start_date", "report_due_date",
]
PBC_COLUMNS = [
    "request_id", FK_ENGAGEMENT_ID,
    "item_name", "account", "client_contact",
    "requested_date", "due_date", "received_date", "file_name", "status",
]
CONFIRMATION_COLUMNS = [
    "confirmation_id", FK_ENGAGEMENT_ID,
    "confirmation_type", "counterparty", "book_amount_krw", "reply_amount_krw",
    "sent_date", "returned_date", "status",
]
 
SHEETS = {
    "Engagements": ENGAGEMENT_COLUMNS,
    "PBC_Requests": PBC_COLUMNS,
    "Confirmations": CONFIRMATION_COLUMNS,
}