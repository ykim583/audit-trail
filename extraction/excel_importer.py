from pathlib import Path

import pandas as pd

from extraction.define import SHEETS, WORKBOOK_PATH, OrderStatus


# 감사 자료중에서 이미 Define 하지 않은 컬럼이 있으면, 그 컬럼은 무시하고, 정의된 컬럼만 가져오도록 한다.
def read_sheet(xls: pd.ExcelFile, sheet: str, columns: list[str]) -> pd.DataFrame:
    df = pd.read_excel(xls, sheet_name=sheet)
    optional_columns = {"status"} if sheet == "PBC_Requests" else set()
    missing = [c for c in columns if c not in df.columns and c not in optional_columns]
    if missing:
        raise ValueError(f"[{sheet}] missing columns: {missing}")
    for column in columns:
        if column not in df.columns:
            df[column] = pd.NA
    df = df[columns]
    if sheet == "PBC_Requests":
        required_data = [column for column in columns if column != "status"]
        complete = (
            df[required_data]
            .apply(lambda column: column.astype("string").str.strip().ne("").fillna(False))
            .all(axis=1)
        )
        status = df["status"].replace(r"^\s*$", pd.NA, regex=True)
        missing_status = status.isna()
        status = status.fillna(OrderStatus.REQUESTED.name)
        df["status"] = status.mask(
            missing_status & complete,
            OrderStatus.RECEIVED.name,
        )
    return df  # keep only the pre-defined columns, in our order

# PBC 엑셀 시트의 status 컬럼을 업데이트하고, 엑셀 파일에 저장하는 함수
def save_pbc_statuses(path: Path, pbc: pd.DataFrame) -> None:
    if path.suffix.lower() != ".xlsx":
        raise ValueError("Status changes can only be saved to .xlsx workbooks.")
    with pd.ExcelWriter(
        path, engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        pbc.to_excel(writer, sheet_name="PBC_Requests", index=False)

# 감사 자료 (엑셀 자료)를 Load 하는 함수, 엑셀 파일이 없으면 에러 발생
def load_workbook(path: Path = WORKBOOK_PATH) -> dict[str, pd.DataFrame]:
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")
    with pd.ExcelFile(path) as xls:
        return {sheet: read_sheet(xls, sheet, cols) for sheet, cols in SHEETS.items()}
 
 # 콘솔에 Display 하는 목적, Unit TEST 용도, Streamlit 에서는 사용하지 않음
def display(data: dict[str, pd.DataFrame]) -> None:
    pd.set_option("display.unicode.east_asian_width", True)  # align Korean text
    for sheet, df in data.items():
        print(f"\n=== {sheet} ({len(df)} rows) ===")
        print(df.to_string(index=False))

# 감사 자료의 status 컬럼을 업데이트하는 함수, Streamlit 에서 사용
def status_update(status: OrderStatus) -> str:
    return status.value

if __name__ == "__main__":
    display(load_workbook())
 