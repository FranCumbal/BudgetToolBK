from behave import step, given, when, then
from logic.field_lines.report_dispacher import FieldReportDispatcher

report_dispacher = FieldReportDispatcher()
## Primer Escenario
@given('que se tiene "{costo_planeado_por_actividad:f}" como costo planeado por actividad ejecutada en "{nombre_de_la_linea}"')
def step_impl(context, costo_planeado_por_actividad, nombre_de_la_linea):
    context.costo_planeado_por_actividad = costo_planeado_por_actividad
    context.nombre_de_la_linea = nombre_de_la_linea
    costo_planeado_por_actividad_en_linea = report_dispacher.get_activity_cost_by_line(context.nombre_de_la_linea)
    assert costo_planeado_por_actividad == costo_planeado_por_actividad_en_linea

@step('en "{mes}" se han planificado "{actividades_planeadas_en_mes:d}" actividad')
def step_impl(context, mes, actividades_planeadas_en_mes): 
    context.actividades_planeadas_en_mes = actividades_planeadas_en_mes
    context.mes = mes
    report_dispacher.get_activities_planned_by_month(context.mes, context.nombre_de_la_linea) #REVISAR
    assert actividades_planeadas_en_mes == report_dispacher.get_activities_planned_by_month(context.mes, context.nombre_de_la_linea)

@when('el CPAE de "{mes}" sea "{costo_por_actividad_ejecutada:f}"')
def step_impl(context, mes, costo_por_actividad_ejecutada):
    context.costo_por_actividad_ejecutada = costo_por_actividad_ejecutada
    context.mes = mes
    costo_planeado_por_actividad_en_linea = report_dispacher.get_cpae_by_month(context.nombre_de_la_linea, context.mes)
    assert context.costo_por_actividad_ejecutada == costo_planeado_por_actividad_en_linea

@step('el budget de "{mes_anterior}" sea "{budget_mes_anterior:f}"')
def step_impl(context, mes_anterior, budget_mes_anterior):
    context.mes_anterior = mes_anterior
    context.budget_mes_anterior = budget_mes_anterior
    budget_mes_anterior_calculado = report_dispacher.get_budget_by_month(context.nombre_de_la_linea, context.mes_anterior)
    print(budget_mes_anterior_calculado)
    print(context.budget_mes_anterior)
    assert context.budget_mes_anterior == budget_mes_anterior_calculado

@then('el budget de "{mes}" debe ser "{budget_mes:f}"')
def step_impl(context, mes, budget_mes):    
    context.mes = mes
    context.budget_mes = budget_mes
    budget_mes_calculado = report_dispacher.get_budget_by_month(context.nombre_de_la_linea, context.mes)
    assert context.budget_mes == budget_mes_calculado

##Segundo Escenario 
@given('que existen actividades ejecutadas en "{nombre_de_la_linea}" en "{mes}" y son')
def step_impl(context, nombre_de_la_linea, mes):  # Parámetros en orden correcto
    context.mes = mes
    context.nombre_de_la_linea = nombre_de_la_linea
    context.executed_activities_with_cost_by_month = report_dispacher.get_executed_activities_and_cost_by_month(context.mes, context.nombre_de_la_linea)
    context.executed_activities_by_month = context.executed_activities_with_cost_by_month["WELL"].tolist()
    context.table_executed_activities = [row["Well"] for row in context.table]
    assert context.executed_activities_by_month == context.table_executed_activities
    
@when('se suman los costos de las actividades ejecutadas en "{mes}"')
def step_impl(context, mes):
    context.mes = mes
    context.executed_activities_with_cost_by_month = report_dispacher.get_executed_activities_and_cost_by_month(context.mes, context.nombre_de_la_linea)
    context.month_total_real_cost = report_dispacher.get_total_real_cost_by_month(context.mes, context.nombre_de_la_linea)

@step('el costo real acumulado de "{mes_anterior}" es "{costo_real_acumulado_mes_anterior:f}"')
def step_impl(context, mes_anterior, costo_real_acumulado_mes_anterior):
    context.mes = mes_anterior
    context.costo_real_acumulado_mes_anterior = costo_real_acumulado_mes_anterior
    costo_real_acumulado_mes_anterior_in_a_month = report_dispacher.get_accumulated_cost_by_month(context.mes, context.nombre_de_la_linea)
    assert costo_real_acumulado_mes_anterior_in_a_month== context.costo_real_acumulado_mes_anterior

@then('el costo real acumulado de "{mes}" debe ser "{costo_real_acumulado:f}"')
def step_imp(context, mes, costo_real_acumulado):
    context.mes = mes
    context.costo_real_acumulado = costo_real_acumulado
    costo_real_acumulado_in_a_month = report_dispacher.get_accumulated_cost_by_month(context.mes, context.nombre_de_la_linea)
    assert costo_real_acumulado_in_a_month == context.costo_real_acumulado

# Tercer Escenario
@given('que el costo real de "{mes}" es "{costo_real:f}" de "{nombre_de_la_linea}"')
def step_imp(context, mes, costo_real, nombre_de_la_linea):
    context.mes = mes
    context.costo_real = costo_real
    context.nombre_de_la_linea = nombre_de_la_linea
    costo_real_por_mes = report_dispacher.get_total_real_cost_by_month(context.mes, context.nombre_de_la_linea)
    assert context.costo_real == costo_real_por_mes

@when('el presupuesto proyectado de "{mes}" sea "{presupuesto_proyectado:f}"')
def step_imp(context, mes, presupuesto_proyectado):
    context.mes = mes
    context.presupuesto_proyectado = presupuesto_proyectado
    presupuesto_proyectado_por_mes = report_dispacher.get_projected_by_month(context.mes, context.nombre_de_la_linea)
    assert presupuesto_proyectado_por_mes == context.presupuesto_proyectado
@step('el presupuesto ajustado de "{mes_anterior}" sea "{proyectado_ajustado_mes_anterior:f}"')
def step_imp(context, mes_anterior, proyectado_ajustado_mes_anterior):
    context.mes_anterior = mes_anterior
    context.proyectado_ajustado_mes_anterior = proyectado_ajustado_mes_anterior
    proyectado_ajustado_mes_anterior_metodo = report_dispacher.get_projected_adjusted_by_month(context.mes_anterior, context.nombre_de_la_linea)
    assert proyectado_ajustado_mes_anterior_metodo == context.proyectado_ajustado_mes_anterior

@then('el presupuesto ajustado de "{mes}" debe ser "{proyectado_ajustado:f}"')
def step_imp(context, mes, proyectado_ajustado):
    context.mes = mes
    context.proyectado_ajustado = proyectado_ajustado
    proyectado_ajustado_por_mes = report_dispacher.get_projected_adjusted_by_month(context.mes, context.nombre_de_la_linea)
    assert proyectado_ajustado_por_mes == context.proyectado_ajustado

# Cuarto Escenario

@given('que se tiene el df_df_budget, df_forecast, df_real_cost_accumulated, df_executed_activities, df_planned_activities, title de "{nombre_de_la_linea}"')
def step_impl(context, nombre_de_la_linea):
    context.nombre_de_la_linea = nombre_de_la_linea
    context.df_budget = report_dispacher.generate_budget_data_frame(context.nombre_de_la_linea)
    context.df_forecast = report_dispacher.generate_projected_data_frame(context.nombre_de_la_linea)
    context.df_real_cost_accumulated = report_dispacher.generate_accumulated_real_cost_data_frame(context.nombre_de_la_linea)
    context.df_executed_activities = report_dispacher.get_accumulated_executed_activities_data_frame(context.nombre_de_la_linea)
    context.df_planned_activities = report_dispacher.generate_planned_activities_data_frame(context.nombre_de_la_linea)
    context.title = f"Forecast Line {context.nombre_de_la_linea}"

@when('se genera el grafico de forecast para "{nombre_de_la_linea}"')
def step_impl(context, nombre_de_la_linea):
    context.nombre_de_la_linea = nombre_de_la_linea
    context.df_real_cost_accumulated = report_dispacher.generate_accumulated_real_cost_data_frame(context.nombre_de_la_linea)
    context.figure = report_dispacher.generate_graph(context.nombre_de_la_linea)
    print(context.figure)  # Para verificar que se ha generado la figura correctamente

