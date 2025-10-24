from behave import given, when, then, step
from logic.field_lines.report_dispacher import FieldReportDispatcher
import pandas as pd
import numpy as np

field_report_dispacher = FieldReportDispatcher()

@given('{initial_planned_activities} activities planned to "{year}" in the "{line_name}" initially distributed in the months as')
def step_impl(context, initial_planned_activities, year, line_name):
    context.initial_planned_activities = initial_planned_activities
    context.year = int(year)
    context.line_name = line_name
    data = []
    for row in context.table:
        data.append({
            "Month": row["Month"].strip().lower(),
            "Initially Planned Activities": int(row["Initially Planned Activities"].strip())
        })
    distributed_activities_at_year_from_logic = field_report_dispacher.get_distributed_initial_planned_activities(context.line_name)
    context.planned_activities = pd.DataFrame(data)
    assert np.array_equal(context.planned_activities.values, distributed_activities_at_year_from_logic.values)

@when('the AFECOST avarage from catalog is calculated')
def step_impl(context):
    context.afe_cost_avr = field_report_dispacher.get_afe_cost_avr(context.line_name, context.year)
    pass

@step('the result of AFECOST avarage is "{afe_cost_avr}"')
def step_impl(context, afe_cost_avr):
    assert context.afe_cost_avr == float(afe_cost_avr)

@step('the CPAE of "{month}" is "{cpae_value}"')
def step_impl(context, month, cpae_value):
    context.cpae_value = field_report_dispacher.get_cpae_by_month(context.line_name, month)
    assert context.cpae_value == float(cpae_value)

@then('the budget value of "{next_month}" should be "{budget_value:f}"')
def step_impl(context, next_month, budget_value):
    context.budget_value = field_report_dispacher.get_budget_by_month(context.line_name, next_month)
    assert context.budget_value == budget_value

## Segundo Escenario

@given('that there are "{executed_activities}" executed activities in "{line_name}" in "{month}" and they are')
def step_impl(context, executed_activities, line_name, month):
    context.month = month
    context.line_name = line_name
    context.executed_activities = executed_activities #inservible por el momento
    context.executed_activities_with_cost_by_month = field_report_dispacher.get_executed_activities_and_cost_by_month(context.month, context.line_name)
    context.executed_activities_from_code = context.executed_activities_with_cost_by_month["WELL"].tolist()
    context.table_executed_activities = [row["Well"] for row in context.table if row.get("STATUS", "").strip().lower() == "final"]
    assert context.table_executed_activities == context.executed_activities_from_code

@when('the costs of the executed activities whit status "{status}" in "{month}" are summed and it is "{executed_activity_cost:f}"')
def step_impl(context, status, month, executed_activity_cost):
    context.month = month
    context.executed_activity_cost = executed_activity_cost
    context.month_total_real_cost = field_report_dispacher.get_total_real_cost_by_month(context.month, context.line_name)
    print(context.month_total_real_cost)
    assert context.executed_activity_cost == context.month_total_real_cost ##Ojo que aqui aun no se que hacer con el B&H

@step('the real cost of "{month}" is "{real_cost:f}"')
def step_impl(context, month, real_cost):
    context.month = month
    context.real_cost = real_cost
    real_cost_by_month = field_report_dispacher.get_total_real_cost_by_month(context.month, context.line_name)
    assert context.real_cost == real_cost_by_month

@step('the real cost accumulated of "{prev_mont}" is "{real_cost_accumulated_prev_month:f}"')
def step_impl(context, prev_mont, real_cost_accumulated_prev_month):
    context.prev_mont = prev_mont
    context.real_cost_accumulated = real_cost_accumulated_prev_month
    real_acummulated_cost_prevmonth = field_report_dispacher.get_accumulated_cost_by_month(context.prev_mont, context.line_name)
    assert real_acummulated_cost_prevmonth== context.real_cost_accumulated

@then('the real cost accumulated of "{actual_month}" should be "{real_cost_accumulated:f}"')
def step_impl(context, actual_month, real_cost_accumulated):
    context.actual_month = actual_month
    context.real_cost_accumulated = real_cost_accumulated
    real_acummulated_cost_actualmonth = field_report_dispacher.get_accumulated_cost_by_month(context.actual_month, context.line_name)
    assert real_acummulated_cost_actualmonth == context.real_cost_accumulated

## Tercer Escenario
@given('that there are "{scheduled_executed_activities}" scheduled executed activities in "{line_name}" in "{month}" and they are')
def step_impl(context, scheduled_executed_activities, line_name, month):
    context.scheduled_executed_activities = scheduled_executed_activities
    context.line_name = line_name
    context.month = month
    scheduled_executed_activities_with_cost_by_month = field_report_dispacher.get_df_scheduled_executed_activities_validated(context.month, context.line_name)
    context.schedule_activities_by_month = [row["Well"] for row in context.table]
    assert context.schedule_activities_by_month == scheduled_executed_activities_with_cost_by_month['Well'].tolist()

@when('the Net Total (USD) of the schedule executed activities whit validation "{validation}" in "{month}" are summed')
def step_impl(context, validation, month):
    context.validation = validation
    context.month = month
    context.scheduled_executed_activities_cost = field_report_dispacher.get_total_scheduled_executed_activities_cost_by_month(context.month, context.line_name)
    print(context.scheduled_executed_activities_cost)
    pass

@step('the proyected cost of "{month}" is "{proyected_cost:f}"')
def step_impl(context, month, proyected_cost):
    context.month = month
    context.proyected_cost = proyected_cost
    projected_adjusted_cost = field_report_dispacher.get_total_scheduled_executed_activities_cost_by_month(context.month, context.line_name)
    assert context.proyected_cost == projected_adjusted_cost

@step('the proyected cost of "{prev_month}" is "{proyected_cost_prev_month:f}"')
def step_impl(context, prev_month, proyected_cost_prev_month):
    context.prev_month = prev_month
    context.proyected_cost_prev_month = proyected_cost_prev_month
    projected_adjusted_cost_prevmonth = field_report_dispacher.get_total_scheduled_executed_activities_cost_by_month(context.prev_month, context.line_name)
    assert context.proyected_cost_prev_month == projected_adjusted_cost_prevmonth

@step('the forecast of "{month}" is "{forecast_value_prev_month:f}"')
def step_impl(context, month, forecast_value_prev_month):
    context.month = month
    context.forecast_value_prev_month = forecast_value_prev_month
    projected_adjusted_cost = field_report_dispacher.get_projected_adjusted_by_month(context.month, context.line_name)
    assert context.forecast_value_prev_month == projected_adjusted_cost

@step('the forecast of "{month}" should be "{forecast_value:f}"')
def step_impl(context, month, forecast_value):
    context.month = month
    context.forecast_value = forecast_value
    projected_adjusted_cost = field_report_dispacher.get_projected_adjusted_by_month(context.month, context.line_name)
    assert context.forecast_value == projected_adjusted_cost
