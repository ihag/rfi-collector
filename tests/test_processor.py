from datetime import datetime

from src.rfi.processor import build_rfi_table, summarize

TODAY = datetime(2025, 3, 11)
DATES = ["2025-03-10"]


def _item(**kw):
    base = {
        "bfSpecRgstNo": "R1",
        "rgstDt": "2025-03-10 09:00:00",
        "opninRgstClseDt": "2025-03-20 18:00:00",
        "prdctClsfcNoNm": "소프트웨어 &amp; 개발",
        "rlDminsttNm": "A기관",
        "asignBdgtAmt": "150000000",
        "specDocFileUrl1": "http://example.com/spec.hwp",
    }
    base.update(kw)
    return base


def _r(df, no):
    return df.loc[df["J"] == no, "R"].iloc[0]


def test_first_pass_filtering():
    items = [
        _item(bfSpecRgstNo="R1"),                                  # 대상
        _item(bfSpecRgstNo="R2", asignBdgtAmt="50000000"),         # 금액 미달
        _item(bfSpecRgstNo="R3", specDocFileUrl1=""),              # 규격서 없음
        _item(bfSpecRgstNo="R1"),                                  # 중복
        _item(bfSpecRgstNo="", oderPlanNo="P1", asignBdgtAmt="0"), # 금액 미입력 -> 제외하지 않음
        _item(bfSpecRgstNo="R9", rgstDt="2025-03-01 09:00:00"),    # 대상 기간 아님
    ]
    df = build_rfi_table(items, DATES, today=TODAY)

    assert len(df) == 4
    assert _r(df, "R1") == ""
    assert _r(df, "R2") == 0
    assert _r(df, "R3") == 0
    assert _r(df, "P1") == ""
    assert df["A"].tolist() == [1, 2, 3, 4]
    assert summarize(df) == (4, 2, 2)


def test_html_unescape_and_columns():
    df = build_rfi_table([_item()], DATES, today=TODAY)
    assert df.loc[0, "L"] == "소프트웨어 & 개발"
    assert df.loc[0, "O"] == df.loc[0, "L"]
    assert df.loc[0, "C"] == "2025-03-11"
    assert df.loc[0, "F"] == "2025-03-20"
    assert list(df.columns) == [chr(i) for i in range(ord("A"), ord("R") + 1)]


def test_budget_boundary():
    items = [
        _item(bfSpecRgstNo="LOW", asignBdgtAmt="90909090"),
        _item(bfSpecRgstNo="OK", asignBdgtAmt="90909091"),
    ]
    df = build_rfi_table(items, DATES, today=TODAY)
    assert _r(df, "LOW") == 0
    assert _r(df, "OK") == ""


def test_missing_spec_url_column_with_noncontiguous_index():
    """회귀 테스트: 규격서 URL 컬럼이 없고 필터링으로 인덱스가 불연속일 때도 동작해야 한다."""
    items = [
        _item(bfSpecRgstNo="OLD", rgstDt="2025-03-01 09:00:00"),
        _item(bfSpecRgstNo="NEW"),
    ]
    for it in items:
        it.pop("specDocFileUrl1")
    df = build_rfi_table(items, DATES, today=TODAY)
    assert len(df) == 1
    assert _r(df, "NEW") == 0  # 규격서 없음 -> 비대상


def test_rows_without_any_id_are_not_collapsed():
    items = [_item(bfSpecRgstNo=""), _item(bfSpecRgstNo="")]
    df = build_rfi_table(items, DATES, today=TODAY)
    assert len(df) == 2


def test_no_target_returns_none():
    assert build_rfi_table([], DATES) is None
    assert build_rfi_table([_item(rgstDt="2025-01-01 00:00:00")], DATES, today=TODAY) is None
