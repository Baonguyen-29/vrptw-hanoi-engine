"""VRPTW HANOI ENGINE - Flask app đầy đủ"""
import io
from flask import Flask, render_template, jsonify, send_file, request
from modules.data_loader import VRPTWDataLoader
from modules.metrics import (compute_route_stats, compute_vehicle_efficiency,
                              compute_area_distribution, compute_time_window_stats,
                              compute_vehicle_type_stats, compute_co2_equivalents,
                              compute_cost_breakdown)
from modules.charts import (chart_before_after, chart_savings_pie,
                             chart_vehicle_efficiency, chart_area_distribution,
                             chart_cost_co2_by_vehicle, chart_route_timeline,
                             chart_route_map, chart_cost_breakdown_pie,
                             chart_co2_by_type, chart_npv_sensitivity)
from modules.optimizer import VRPTWOptimizer
from modules.exporter import export_summary_excel, generate_filename

app = Flask(__name__)
loader = VRPTWDataLoader()
FUEL_PRICE = 25630


def _ctx():
    kpi = loader.get_total_kpi()
    savings = loader.get_savings()
    financial = loader.get_financial()
    veh_df = loader.get_vehicle_summary()
    veh_eff = compute_vehicle_efficiency(veh_df) if not veh_df.empty else veh_df
    routes_df = loader.get_routes()
    route_stats = compute_route_stats(routes_df) if not routes_df.empty else routes_df
    orders_df = loader.get_orders()
    area_df = compute_area_distribution(orders_df) if not orders_df.empty else orders_df
    tw_df = compute_time_window_stats(orders_df) if not orders_df.empty else orders_df
    type_df = compute_vehicle_type_stats(veh_df) if not veh_df.empty else veh_df
    breakdown = compute_cost_breakdown(veh_df) if not veh_df.empty else {}
    co2_equiv = compute_co2_equivalents(kpi["after"]["Phát thải CO₂ (kg)"])
    return {
        "kpi": kpi, "savings": savings, "financial": financial,
        "charts": {
            "before_after": chart_before_after(kpi),
            "savings_pie": chart_savings_pie(savings),
            "vehicle_eff": chart_vehicle_efficiency(veh_df),
            "area_dist": chart_area_distribution(area_df),
            "cost_co2": chart_cost_co2_by_vehicle(veh_df),
            "route_timeline": chart_route_timeline(routes_df),
            "route_map": chart_route_map(routes_df, orders_df),
            "cost_breakdown": chart_cost_breakdown_pie(breakdown),
            "co2_by_type": chart_co2_by_type(breakdown),
            "npv_sensitivity": chart_npv_sensitivity(financial["npv"]),
        },
        "vehicles": veh_eff.to_dict("records") if not veh_eff.empty else [],
        "route_stats": route_stats.to_dict("records") if not route_stats.empty else [],
        "areas": area_df.to_dict("records") if not area_df.empty else [],
        "time_windows": tw_df.to_dict("records") if not tw_df.empty else [],
        "vehicle_types": type_df.to_dict("records") if not type_df.empty else [],
        "breakdown": breakdown, "co2_equiv": co2_equiv,
    }


@app.route("/")
def index():
    return render_template("index.html", **_ctx())


@app.route("/vehicles")
def vehicles():
    return render_template("vehicles.html", **_ctx())


@app.route("/routes")
def routes():
    return render_template("routes.html", **_ctx())


@app.route("/analysis")
def analysis():
    return render_template("analysis.html", **_ctx())


@app.route("/simulator")
def simulator():
    return render_template("simulator.html", **_ctx())


@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy", "version": "9.8.0",
        "orders": len(loader.get_orders()),
        "vehicles": len(loader.get_vehicles()),
        "routes": len(loader.get_routes()),
    })


@app.route("/api/kpi")
def api_kpi():
    return jsonify(loader.get_total_kpi())


@app.route("/api/savings")
def api_savings():
    return jsonify(loader.get_savings())


@app.route("/api/vehicles")
def api_vehicles():
    df = loader.get_vehicle_summary()
    if df.empty:
        return jsonify([])
    return jsonify(compute_vehicle_efficiency(df).to_dict("records"))


@app.route("/api/routes")
def api_routes():
    df = loader.get_routes()
    return jsonify(df.to_dict("records") if not df.empty else [])


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    data = request.get_json(silent=True) or {}
    alpha = float(data.get("alpha", 0.5))
    num_orders = int(data.get("num_orders", 50))
    orders = loader.get_orders()
    vehicles = loader.get_vehicles()
    if orders.empty or vehicles.empty:
        return jsonify({"error": "Thiếu dữ liệu"}), 400
    opt = VRPTWOptimizer(orders.head(num_orders), vehicles, None, {})
    return jsonify(opt.solve(alpha=alpha, max_seconds=20))


@app.route("/api/export")
def api_export():
    try:
        data = export_summary_excel(loader)
        return send_file(
            io.BytesIO(data),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=generate_filename(),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
