import pytest
from tools.auto_drilldown import _inject_group_by


def test_inject_group_by_with_existing_group():
    sql = "SELECT dt, SUM(dau) AS dau FROM table WHERE dt >= '20260401' GROUP BY dt ORDER BY dt"
    result = _inject_group_by(sql, "is_new_2024")
    assert "is_new_2024" in result
    assert "GROUP BY is_new_2024, dt" in result or "GROUP BY is_new_2024," in result


def test_inject_group_by_without_group():
    sql = "SELECT SUM(dau) AS dau FROM table WHERE dt >= '20260401' ORDER BY dt"
    result = _inject_group_by(sql, "app_launch_way")
    assert "app_launch_way" in result
    assert "GROUP BY app_launch_way" in result


def test_inject_group_by_select_gets_dimension():
    sql = "SELECT SUM(dau) AS dau FROM table WHERE dt >= '20260401'"
    result = _inject_group_by(sql, "province")
    assert result.startswith("SELECT province,") or "SELECT province, " in result


def test_inject_group_by_preserves_original_sql():
    sql = "SELECT dt, SUM(dau) AS dau FROM table WHERE dt >= '20260401' GROUP BY dt"
    result = _inject_group_by(sql, "is_new_2024")
    assert "SUM(dau)" in result
    assert "WHERE dt >= '20260401'" in result
