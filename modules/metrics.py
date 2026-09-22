"""Tính toán KPI cho dashboard"""
import pandas as pd


def compute_route_stats(routes_df):
    if routes_df.empty:
        return pd.DataFrame()
    grp = routes_df.groupby("vehicle").agg(
        total_distance_km=("distance_km", "sum"),
        num_stops=("to", "count"),
        start_time=("arrival_time", "first"),
        end_time=("arrival_time", "last"),
    ).reset_index()
    grp["distance_km"] = grp["total_distance_km"].round(2)
    return grp


def compute_vehicle_efficiency(vs):
    if vs.empty:
        return pd.DataFrame()
    df = vs.copy()
    df["utilization_pct"] = (df["load_kg"] / df["capacity_kg"] * 100).round(2)
    df["cost_per_km"] = df.apply(
        lambda r: round(r["cost_vnd"] / r["distance_km"], 0) if r["distance_km"] > 0 else 0,
        axis=1,
    )
    df["co2_per_km"] = df.apply(
        lambda r: round(r["co2_kg"] / r["distance_km"], 4) if r["distance_km"] > 0 else 0,
        axis=1,
    )
    df["co2_per_order"] = df.apply(
        lambda r: round(r["co2_kg"] / r["num_orders"], 4) if r["num_orders"] > 0 else 0,
        axis=1,
    )
    return df


def compute_area_distribution(orders):
    if orders.empty:
        return pd.DataFrame()
    return orders.groupby("Area").agg(
        num_orders=("Order_ID", "count"),
        total_weight_kg=("Weight_kg", "sum"),
        avg_service_min=("Service_min", "mean"),
    ).reset_index().round(2)


def compute_time_window_stats(orders):
    if orders.empty:
        return pd.DataFrame()
    return orders.groupby("Time_Window").agg(
        num_orders=("Order_ID", "count"),
        avg_weight_kg=("Weight_kg", "mean"),
        total_weight_kg=("Weight_kg", "sum"),
    ).reset_index().round(2)


def compute_vehicle_type_stats(vs):
    if vs.empty:
        return pd.DataFrame()
    return vs.groupby("type").agg(
        total_vehicles=("vehicle", "count"),
        used_vehicles=("used", lambda s: (s == "Có").sum()),
        total_distance=("distance_km", "sum"),
        total_cost=("cost_vnd", "sum"),
        total_co2=("co2_kg", "sum"),
        total_orders=("num_orders", "sum"),
    ).reset_index().round(2)


def compute_co2_equivalents(co2):
    return {
        "trees_per_year": round(co2 / 21, 2),
        "km_car_equiv": round(co2 / 0.12, 1),
        "kg_per_month": round(co2 * 30, 1),
        "ton_per_year": round(co2 * 300 / 1000, 3),
    }


def compute_cost_breakdown(vs):
    if vs.empty:
        return {}
    df = vs[vs["used"] == "Có"]
    return {
        "fuel_total": float(df["cost_vnd"].sum()),
        "fuel_moto": float(df[df["type"] == "Xe máy"]["cost_vnd"].sum()),
        "fuel_truck": float(df[df["type"] == "Xe tải nhỏ"]["cost_vnd"].sum()),
        "co2_moto": float(df[df["type"] == "Xe máy"]["co2_kg"].sum()),
        "co2_truck": float(df[df["type"] == "Xe tải nhỏ"]["co2_kg"].sum()),
        "orders_moto": int(df[df["type"] == "Xe máy"]["num_orders"].sum()),
        "orders_truck": int(df[df["type"] == "Xe tải nhỏ"]["num_orders"].sum()),
    }
