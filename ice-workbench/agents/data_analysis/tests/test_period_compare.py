import pytest
from tools.period_compare import shift_dates_in_sql


def test_shift_wow():
    sql = "SELECT dt, SUM(dau) FROM t WHERE dt >= '20260415' AND dt <= '20260421' GROUP BY dt"
    result = shift_dates_in_sql(sql, 7)
    assert "'20260408'" in result
    assert "'20260414'" in result


def test_shift_yoy():
    sql = "SELECT dt, SUM(dau) FROM t WHERE dt >= '20260415' AND dt <= '20260421' GROUP BY dt"
    result = shift_dates_in_sql(sql, 365)
    assert "'20250415'" in result or "'20250416'" in result


def test_shift_preserves_non_date_content():
    sql = "SELECT dt, SUM(dau) AS dau FROM iceberg_table WHERE dt >= '20260415' AND is_app_dau_2024=1 GROUP BY dt"
    result = shift_dates_in_sql(sql, 7)
    assert "iceberg_table" in result
    assert "is_app_dau_2024=1" in result
    assert "SUM(dau)" in result


def test_shift_no_dates():
    sql = "SELECT COUNT(*) FROM t WHERE active=1"
    result = shift_dates_in_sql(sql, 7)
    assert result == sql


def test_shift_single_date():
    sql = "SELECT * FROM t WHERE dt = '20260420'"
    result = shift_dates_in_sql(sql, 28)
    assert "'20260323'" in result
