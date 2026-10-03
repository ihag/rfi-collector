import html
from datetime import datetime

import pandas as pd

from src.common.config import BUDGET_UNSET_MAX, MIN_BUDGET_EXCL_VAT

COLUMNS_A_TO_R = [chr(i) for i in range(ord("A"), ord("R") + 1)]


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    """컬럼이 없거나 비어 있어도 안전하게 문자열 Series로 꺼낸다."""
    if name in df.columns:
        return df[name].fillna("").astype(str).str.strip()
    return pd.Series("", index=df.index)


def build_rfi_table(items, target_dates, today=None):
    """API 원본 items -> 엑셀 A~R 형식의 DataFrame. 대상이 없으면 None."""
    if not items:
        return None
    today = today or datetime.now()
    df = pd.DataFrame(items)

    # 식별번호(J): 사전규격등록번호, 없으면 발주계획번호
    reg_no, plan_no = _col(df, "bfSpecRgstNo"), _col(df, "oderPlanNo")
    df["J"] = reg_no.where(reg_no != "", plan_no)

    # 등록일(E): 접수일, 없으면 등록일
    rcpt, rgst = _col(df, "rcptDt"), _col(df, "rgstDt")
    df["E"] = rcpt.where(rcpt != "", rgst).str[:10].str.replace("/", "-", regex=False)

    # 중복 제거 (식별번호가 비어 있는 행끼리는 서로 중복으로 보지 않음)
    duplicated = df.duplicated(subset=["J"], keep="first") & (df["J"] != "")
    df = df[~duplicated]
    df = df[df["E"].isin(target_dates)].reset_index(drop=True)
    if df.empty:
        return None

    for col in COLUMNS_A_TO_R:
        if col not in df.columns:
            df[col] = ""

    df["C"] = today.strftime("%Y-%m-%d")
    df["F"] = _col(df, "opninRgstClseDt").str[:10]
    df["L"] = _col(df, "prdctClsfcNoNm").map(html.unescape)
    df["M"] = _col(df, "rlDminsttNm").map(html.unescape)
    df["O"] = df["L"]
    df["Q"] = (
        pd.to_numeric(_col(df, "asignBdgtAmt").str.replace(",", "", regex=False), errors="coerce")
        .fillna(0)
        .astype("int64")
    )

    # ---- 1차 자동 판별: 비대상이면 R = 0 ----
    under_budget = (df["Q"] > BUDGET_UNSET_MAX) & (df["Q"] < MIN_BUDGET_EXCL_VAT)
    no_spec_file = _col(df, "specDocFileUrl1") == ""
    # 0(비대상)과 ""(직접 판별 필요)이 섞인 열이므로 리스트로 만들어 object dtype 유지
    df["R"] = [0 if excluded else "" for excluded in (under_budget | no_spec_file)]

    df = df.sort_values(by=["E", "J"], ascending=[False, False]).reset_index(drop=True)
    df["A"] = range(1, len(df) + 1)
    return df[COLUMNS_A_TO_R]


def summarize(df: pd.DataFrame):
    """(전체, 1차 비대상, 직접 판별 필요) 건수."""
    total = len(df)
    excluded = int(df["R"].eq(0).sum())
    return total, excluded, total - excluded
