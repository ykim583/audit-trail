from pathlib import Path

import pandas as pd

from extraction.define import SHEETS, WORKBOOK_PATH, OrderStatus


# 감사 자료중에서 이미 Define 하지 않은 컬럼이 있으면, 그 컬럼은 무시하고, 정의된 컬럼만 가져오도록 한다. 단, 이후에 정의되지 않은 컬럼도 자동추가하는 기능을 구현 목표
def read_sheet(xls: pd.ExcelFile, sheet: str, columns: list[str]) -> pd.DataFrame:
    df = pd.read_excel(xls, sheet_name=sheet)
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"[{sheet}] missing columns: {missing}")
    return df[columns]  # keep only the pre-defined columns, in our order
 
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

def status_update(status: OrderStatus) -> str:
    responses = {
        OrderStatus.REQUESTED: "자료 요청",
        OrderStatus.RECEIVED: "자료 수령",
        OrderStatus.REVIEWED: "자료 검토",
        OrderStatus.DRAFT: "조회서 작성",
        OrderStatus.SENT: "조회서 전송",
        OrderStatus.RETURNED: "회신 완료",
        OrderStatus.RECONCILED: "감사 최종 완료",
        OrderStatus.FAILURE: "자료 오류",
    }
    return responses[status]

if __name__ == "__main__":
    display(load_workbook())
 