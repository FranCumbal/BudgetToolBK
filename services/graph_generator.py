import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from matplotlib.patches import FancyBboxPatch  # Asegúrate de tenerlo importado arriba
from utils.dates import get_all_months


# Define the function as requested
def generate_budget_graph_als(forecast, budget_data, activities_data, capacity_df, opex_budget):
    all_months = pd.DataFrame({
        "month": ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]
    })
    
    forecast.columns = forecast.columns.str.lower()
    budget_data.columns = budget_data.columns.str.lower()
    activities_data.columns = activities_data.columns.str.lower()

    forecast = all_months.merge(forecast, on='month', how='left')
    budget_data = all_months.merge(budget_data, on='month', how='left')
    activities_data = all_months.merge(activities_data, on='month', how='left')
    forecast['cumulative forecast'] = forecast['forecast'].cumsum()
    budget_data['cumulative actual cost'] = budget_data['actual cost'].cumsum()
    budget_data['cumulative b&h'] = budget_data['b&h_actual'].cumsum()

    monthly_opex = opex_budget / 12
    opex_cumulative = np.cumsum([monthly_opex] * 12)

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.set_xlabel('Month')
    ax1.set_ylabel('Cost (MUSD)', color='tab:blue')
    ax1.set_ylim(-15_000_000, 40_000_000)
    ax1.set_yticks(np.arange(-15_000_000, 41_000_000, 5_000_000))
    ax1.set_yticklabels([f'{int(val / 1_000_000)}' for val in np.arange(-15_000_000, 41_000_000, 5_000_000)])

    x_vals = np.arange(1, 13)

    forecast_color = '#8e44ad'
    plan_color = "#008FF6"#"#25a1e9"
    actual_color = '#e67e22'
    opex_act_color = '#f39c12'
    b_h_color = '#1abc9c' 
    
    ax1.plot(x_vals, forecast['cumulative forecast'], label='Forecast EOY', color=forecast_color, linestyle='--', marker='.')
    ax1.plot(x_vals, budget_data['cumulative actual cost'], label='Actual Cost (with B&H)', color=actual_color, marker='o')
    ax1.plot(x_vals, budget_data['cumulative b&h'], label='B&H Accumulated', color=b_h_color, linestyle='-', marker='s')
    ax1.plot(x_vals, opex_cumulative, label='Planned Cost', color=plan_color, linestyle='-', marker='x')

    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2)

    month_list = all_months['month'].tolist()
    current_month_str = datetime.now().strftime("%B")
    current_idx = month_list.index(current_month_str) if current_month_str in month_list else 0
    closing_idx = max(0, current_idx - 1)
    next_idx = min(11, current_idx + 1)

    annotation_months = {closing_idx, current_idx, next_idx}

    for i in range(12):
        if i in annotation_months:
            x_coord = i + 1
            fc_val = forecast['cumulative forecast'].iloc[i]
            ac_val = budget_data['cumulative actual cost'].iloc[i]
            bh_val = budget_data['cumulative b&h'].iloc[i]
            op_val = opex_cumulative[i]

            if i == closing_idx:
                ax1.annotate(f"{ac_val / 1_000_000:.2f}",
                            xy=(x_coord, ac_val), xytext=(0, -20),
                            textcoords='offset points', ha='center', color=actual_color,
                            arrowprops=dict(arrowstyle='->', color=actual_color))

                ax1.annotate(f"{bh_val / 1_000_000:.2f}",
                            xy=(x_coord, bh_val), xytext=(0, 5),
                            textcoords='offset points', ha='center', color=b_h_color,
                            arrowprops=dict(arrowstyle='->', color=b_h_color))

            elif i in [current_idx, next_idx]:
                ax1.annotate(f"{fc_val / 1_000_000:.2f}",
                            xy=(x_coord, fc_val), xytext=(0, 10),
                            textcoords='offset points', ha='center', color=forecast_color,
                            arrowprops=dict(arrowstyle='->', color=forecast_color))

                ax1.annotate(f"{op_val / 1_000_000:.2f}",
                            xy=(x_coord, op_val), xytext=(0, 30),
                            textcoords='offset points', ha='center', color=plan_color,
                            arrowprops=dict(arrowstyle='->', color=plan_color))


    # 1️⃣ Etiquetas finales personalizadas (para evitar solapamiento)
    final_fc = forecast['cumulative forecast'].iloc[-1]
    final_ac = budget_data['cumulative actual cost'].iloc[-1]

    # Forecast desplazado hacia arriba
    ax1.annotate(f"{final_fc / 1_000_000:.2f}M",
                xy=(12, final_fc), xytext=(10, 15),
                textcoords='offset points', ha='left', color=forecast_color)

    # Actual desplazado hacia abajo
    ax1.annotate(f"{final_ac / 1_000_000:.2f}M",
                xy=(12, final_ac), xytext=(10, -5),
                textcoords='offset points', ha='left', color='tab:orange')

    # 2️⃣ Función auxiliar para los demás
    def annotate_final(x, y, label, color):
        ax1.annotate(f"{y / 1_000_000:.2f}M", xy=(x, y), xytext=(10, 0),
                    textcoords='offset points', ha='left', color=color)

    # Anotar B&H y OPEX normalmente
    annotate_final(12, budget_data['cumulative b&h'].iloc[-1], 'B&H', b_h_color)
    annotate_final(12, opex_cumulative[-1], 'OPEX', plan_color)


    activities_data['cumulative_planned'] = activities_data['planned_activities'].cumsum()
    capacity_df['cumulative_estimated'] = capacity_df['total_activities'].cumsum()
    activities_data['cumulative_executed'] = activities_data['executed_activities'].cumsum()
    activities_data['cumulative_fails'] = activities_data['fails'].cumsum()
    # Ocultar ejecutados y fallas después del mes de cierre
    activities_data.loc[closing_idx+1:, 'cumulative_executed'] = np.nan
    activities_data.loc[closing_idx+1:, 'cumulative_fails'] = np.nan
    # Ocultar actividades pronosticadas antes del mes actual
    capacity_df.loc[:current_idx-1, 'cumulative_estimated'] = np.nan


    ax2 = ax1.twinx()
    ax2.set_ylabel('# Activities', color='tab:purple')
    ax2.set_ylim(0, 150)

    x = np.arange(len(all_months['month'])) + 1
    width = 0.18

    bars1 = ax2.bar(x - 1.5 * width, activities_data['cumulative_planned'], width,
                    label='Planned Activities', color='#95a5a6', alpha=0.7)

    bars2 = ax2.bar(x - 0.5 * width, capacity_df['cumulative_estimated'], width,
                    label='Forecasted Activities (statistics)', color=opex_act_color, alpha=0.7)

    bars3 = ax2.bar(x + 0.5 * width, activities_data['cumulative_executed'], width,
                    label='Executed Activities', color='#27ae60', alpha=0.7)

    bars4 = ax2.bar(x + 1.5 * width, activities_data['cumulative_fails'], width,
                    label='Fails Accumulated', color='tab:red', alpha=0.7)




    # Anotaciones finales en cada barra
    for bar_group, values in zip(
        [bars1, bars2, bars3, bars4],
        [activities_data['cumulative_planned'],
        capacity_df['cumulative_estimated'],
        activities_data['cumulative_executed'],
        activities_data['cumulative_fails']]
    ):
        # Último índice con valor no nulo
        last_idx = values.last_valid_index()
        if last_idx is not None:
            last_val = values.iloc[last_idx]
            bar = bar_group[last_idx]
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                last_val + 5,
                f"{last_val:.0f}",
                ha='center', va='bottom',
                color='black', fontsize=9
            )


    ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3)
    ax1.set_xticks(x)
    ax1.set_xticklabels(x, ha='right')

    # Fancy info box
    info_box_color = '#2ecc71'
    closing_month_name = all_months['month'].iloc[closing_idx]
    current_month_name = all_months['month'].iloc[current_idx]
    next_month_name = all_months['month'].iloc[next_idx]

    # Valores para el fancy info box
    closing_month_name = all_months['month'].iloc[closing_idx]
    current_month_name = all_months['month'].iloc[current_idx]
    next_month_name = all_months['month'].iloc[next_idx]

    current_value = budget_data['actual cost'].iloc[closing_idx] / 1_000_000 if 'actual cost' in budget_data.columns else 0
    next_forecast = forecast['forecast'].iloc[current_idx] / 1_000_000 if 'forecast' in forecast.columns else 0
    following_forecast = forecast['forecast'].iloc[next_idx] / 1_000_000 if 'forecast' in forecast.columns else 0

    # 🔹 Agregamos valores fin de año
    eoy_fc = forecast['cumulative forecast'].iloc[-1] / 1_000_000
    eoy_plan = opex_cumulative[-1] / 1_000_000
    delta = eoy_fc - eoy_plan
    delta_sign = "+" if delta >= 0 else "-"
    delta_text = f"{delta_sign}{abs(delta):.2f} M"


    info_text = (
        f"{closing_month_name}: {current_value:.2f} M\n"
        f"{current_month_name} Forecast: {next_forecast:.2f} M\n"
        f"{next_month_name} Forecast: {following_forecast:.2f} M\n"
        f"=== Year-End Summary: ===\n"
        f"Forecast: {eoy_fc:.3f} M\n"
        f"Planned: {eoy_plan:.2f} M\n"
        f"Difference: {delta_text}"
    )




    fancy_box = FancyBboxPatch((0.05, 0.68), 0.32, 0.30,
                                boxstyle="round,pad=0.02", fc=plan_color, ec="none", alpha=0.8,
                                transform=ax1.transAxes)
    ax1.add_patch(fancy_box)
    ax1.text(0.05 + 0.3 / 2, 0.75 + 0.18 / 2, info_text,
             ha='center', va='center', transform=ax1.transAxes,
             color='white', fontsize=11)


    plt.title('ALS Execution vs Plan')
    ax1.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    return fig

def create_budget_forecast_graph(forecast, budget_data, plan_data, activities_data, title, capacity_data=None):
    all_months = pd.DataFrame({"MONTH": get_all_months()})

    forecast.columns = forecast.columns.str.upper()
    budget_data.columns = budget_data.columns.str.upper()
    plan_data.columns = plan_data.columns.str.upper()
    activities_data.columns = activities_data.columns.astype(str).str.upper()

    if capacity_data is not None:
        capacity_data.columns = capacity_data.columns.str.upper()

    forecast = all_months.merge(forecast, on='MONTH', how='left')
    budget_data = all_months.merge(budget_data, on='MONTH', how='left')
    plan_data = all_months.merge(plan_data, on='MONTH', how='left')
    activities_data = all_months.merge(activities_data, on='MONTH', how='left')
    if capacity_data is not None:
        capacity_data = all_months.merge(capacity_data, on='MONTH', how='left')

    forecast['CUMULATIVE FORECAST'] = forecast['BUDGET'].fillna(0).cumsum()
    plan_data['CUMULATIVE PLAN'] = plan_data['PLANNED_COST'].fillna(0).cumsum()
    budget_data['CUMULATIVE ACTUAL COST'] = budget_data['ACTUAL_COST'].fillna(0).cumsum()

    fig, ax1 = plt.subplots(figsize=(12, 7))
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Cost (MUSD)", color='#2c3e50')
    ax1.tick_params(axis='y', labelcolor='#2c3e50')
    ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1_000_000:.1f}'))

    x_values = np.arange(1, 13)

    current_month_str = datetime.now().strftime("%B").upper()
    current_idx = all_months[all_months['MONTH'].str.upper() == current_month_str].index[0] if current_month_str in all_months['MONTH'].str.upper().values else 0
    closing_idx = max(0, current_idx - 1)
    next_idx = min(11, current_idx + 1)

    forecast_color = '#8e44ad'
    plan_color = "#008FF6" # #0ba6ff #3498db #1ca4ff
    actual_color = '#e67e22'
    opex_act_color = '#f39c12'

    ax1.plot(x_values, forecast['CUMULATIVE FORECAST'], label='Forecast EOY', color=forecast_color, linestyle='--', marker='.')
    ax1.plot(x_values, plan_data['CUMULATIVE PLAN'], label='Planned Cost', color=plan_color, linestyle='-', marker='x')
    ax1.plot(x_values[:closing_idx+1], budget_data['CUMULATIVE ACTUAL COST'].iloc[:closing_idx+1], label='Actual Cost', color=actual_color, marker='.')

    def annotate(ax, x, y, text, color, offset=(20, 0)):
        ax.annotate(f"{text:.2f}", xy=(x, y), xytext=offset,
                    textcoords='offset points', ha='left', color=color,
                    fontsize=9, arrowprops=dict(arrowstyle='->', color=color))

    annotate(ax1, closing_idx + 1, budget_data['CUMULATIVE ACTUAL COST'].iloc[closing_idx], budget_data['CUMULATIVE ACTUAL COST'].iloc[closing_idx]/1_000_000, actual_color, offset=(0, -30))
    annotate(ax1, current_idx + 1, forecast['CUMULATIVE FORECAST'].iloc[current_idx], forecast['CUMULATIVE FORECAST'].iloc[current_idx]/1_000_000, forecast_color, offset=(20, 5))
    annotate(ax1, next_idx + 1, forecast['CUMULATIVE FORECAST'].iloc[next_idx], forecast['CUMULATIVE FORECAST'].iloc[next_idx]/1_000_000, forecast_color, offset=(20, -30))
    annotate(ax1, 12, forecast['CUMULATIVE FORECAST'].iloc[-1], forecast['CUMULATIVE FORECAST'].iloc[-1]/1_000_000, forecast_color, offset=(10, -10))

    annotate(ax1, current_idx + 1, plan_data['CUMULATIVE PLAN'].iloc[current_idx], plan_data['CUMULATIVE PLAN'].iloc[current_idx]/1_000_000, plan_color, offset=(-30, 5))
    annotate(ax1, next_idx + 1, plan_data['CUMULATIVE PLAN'].iloc[next_idx], plan_data['CUMULATIVE PLAN'].iloc[next_idx]/1_000_000, plan_color, offset=(-30, -30))
    annotate(ax1, 12, plan_data['CUMULATIVE PLAN'].iloc[-1], plan_data['CUMULATIVE PLAN'].iloc[-1]/1_000_000, plan_color, offset=(10, 10))

    closing_month_name = all_months['MONTH'].iloc[closing_idx]
    current_month_name = all_months['MONTH'].iloc[current_idx]
    next_month_name = all_months['MONTH'].iloc[next_idx]

    current_value = budget_data['ACTUAL_COST'].iloc[closing_idx] / 1_000_000
    current_fc = forecast['FORECAST_COST'].iloc[current_idx] / 1_000_000
    next_fc = forecast['FORECAST_COST'].iloc[next_idx] / 1_000_000

    eoy_fc = forecast['CUMULATIVE FORECAST'].iloc[-1] / 1_000_000
    eoy_plan = plan_data['CUMULATIVE PLAN'].iloc[-1] / 1_000_000
    delta = eoy_fc - eoy_plan
    delta_sign = "+" if delta >= 0 else "-"
    delta_text = f"{delta_sign}{abs(delta):.2f} M"

    info_text = (
        f"{closing_month_name} (closing): {current_value:.3f} M\n"
        f"Forecast\n"
        f"{current_month_name}: {current_fc:.2f} M\n"
        f"{next_month_name}: {next_fc:.2f} M\n"
        f"=== Year-End Summary: ===\n"
        f"Forecast: {eoy_fc:.2f} M\n"
        f"Planned: {eoy_plan:.2f} M\n"
        f"Difference: {delta_text}"
    )

    fancy_box = FancyBboxPatch((0.05, 0.68), 0.32, 0.30,
                                boxstyle="round,pad=0.02", fc=plan_color, ec="none", alpha=0.8,
                                transform=ax1.transAxes)
    ax1.add_patch(fancy_box)
    ax1.text(0.05 + 0.3 / 2, 0.75 + 0.18 / 2, info_text,
             ha='center', va='center', transform=ax1.transAxes,
             color='white', fontsize=11)
    
    

    activities_data['CUMULATIVE_PLANNED'] = activities_data['PLANNED_ACTIVITIES'].cumsum()
    activities_data['CUMULATIVE_EXECUTED'] = activities_data['EXECUTED_ACTIVITIES'].cumsum()
    activities_data.loc[current_idx:, 'CUMULATIVE_EXECUTED'] = np.nan

    # Si hay capacity_data, también aplicar la lógica de mostrar solo desde el mes actual
    if capacity_data is not None:
        capacity_data['CUMULATIVE_FORECASTED_OPEX_ACT'] = capacity_data['FORECASTED_OPEX_ACT'].fillna(0).cumsum()
        # Ocultar actividades pronosticadas antes del mes actual
        capacity_data.loc[:current_idx-1, 'CUMULATIVE_FORECASTED_OPEX_ACT'] = np.nan


    ax2 = ax1.twinx()
    ax2.set_ylabel('# Activities', color='#2c3e50', fontsize=12)
    ax2.set_ylim(0, 150)

    width = 0.2
    x = np.arange(1, 13)
    bars_planned = ax2.bar(x - width, activities_data['CUMULATIVE_PLANNED'], width=0.2, label='Planned Activities', color='#95a5a6', alpha=0.7)
    bars_executed = ax2.bar(x, activities_data['CUMULATIVE_EXECUTED'], width=0.2, label='Executed Activities', color='#27ae60', alpha=0.7)

    if capacity_data is not None:
        bars_opex = ax2.bar(x + width, capacity_data['CUMULATIVE_FORECASTED_OPEX_ACT'], width=0.2, label='Forecasted Opex Act', color=opex_act_color, alpha=0.7)
        final_val = capacity_data['CUMULATIVE_FORECASTED_OPEX_ACT'].iloc[-1]
        ax2.annotate(f"{final_val:.0f}", xy=(12, final_val), xytext=(0, 5), textcoords='offset points', fontsize=9, color='#000000')

    for bar in bars_planned:
        if bar.get_height() > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3, f"{bar.get_height():.0f}", ha='center', fontsize=8)

    for bar in bars_executed:
        if pd.notna(bar.get_height()):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3, f"{bar.get_height():.0f}", ha='center', fontsize=8, color='#2c3e50')

    ax1.set_xticks(x)
    ax1.set_xticklabels([str(i) for i in x], fontsize=10)
    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)
    ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=10)

    ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
    plt.title(title, fontsize=14, pad=20)
    plt.tight_layout()
    return fig
