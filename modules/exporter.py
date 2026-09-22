"""Export báo cáo Excel"""
import io
from datetime import datetime
import pandas as pd


def export_summary_excel(loader):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        kpi = loader.get_total_kpi()
        savings = loader.get_savings()
        rows = []
        for k in savings:
            rows.append({
                "Chỉ tiêu": k,
                "Trước AI": savings[k]["before"],
                "Sau AI": savings[k]["after"],
                "Mức giảm": savings[k]["diff"],
                "Tỷ lệ giảm (%)": round(savings[k]["pct"], 2),
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="KPI_Summary", index=False)
        loader.get_vehicle_summary().to_excel(writer, sheet_name="Vehicle_Summary", index=False)
        loader.get_routes().to_excel(writer, sheet_name="Route_xijk", index=False)
        loader.get_orders().to_excel(writer, sheet_name="Orders", index=False)
        fin = loader.get_financial()
        fin_rows = [
            {"Khoản mục": "Đầu tư ban đầu", "Giá trị": fin["investment"]},
            {"Khoản mục": "Phát triển phần mềm", "Giá trị": fin["software_dev"]},
            {"Khoản mục": "Phân tích dữ liệu", "Giá trị": fin["data_analysis"]},
            {"Khoản mục": "Tiết kiệm/năm", "Giá trị": fin["savings_per_year"]},
            {"Khoản mục": "Tiết kiệm/ngày", "Giá trị": fin["savings_per_day"]},
            {"Khoản mục": "Hoàn vốn (tháng)", "Giá trị": fin["payback_months"]},
            {"Khoản mục": "IRR (%)", "Giá trị": fin["irr_pct"]},
        ]
        pd.DataFrame(fin_rows).to_excel(writer, sheet_name="Financial", index=False)
    buf.seek(0)
    return buf.getvalue()


def generate_filename(prefix="VRPTW_Hanoi_Report"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.xlsx"
