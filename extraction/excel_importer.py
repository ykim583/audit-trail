from pathlib import Path
 
import pandas as pd


# --- Path to the workbook to be imported 
WORKBOOK_PATH = Path(__file__).resolve().parent.parent / "admin" / "audit_dummy_clean.xlsx"
 
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
 
 
def read_sheet(xls: pd.ExcelFile, sheet: str, columns: list[str]) -> pd.DataFrame:
    df = pd.read_excel(xls, sheet_name=sheet)
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"[{sheet}] missing columns: {missing}")
    return df[columns]  # keep only the pre-defined columns, in our order
 
 
def load_workbook(path: Path = WORKBOOK_PATH) -> dict[str, pd.DataFrame]:
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")
    with pd.ExcelFile(path) as xls:
        return {sheet: read_sheet(xls, sheet, cols) for sheet, cols in SHEETS.items()}
 
 
def display(data: dict[str, pd.DataFrame]) -> None:
    pd.set_option("display.unicode.east_asian_width", True)  # align Korean text
    for sheet, df in data.items():
        print(f"\n=== {sheet} ({len(df)} rows) ===")
        print(df.to_string(index=False))
 
 
if __name__ == "__main__":
    display(load_workbook())
 