Feature: Generación del forecast de la linea 104
    As ingeniero responsable de la linea 104
    I want to generar el forecast de mi linea
    To evaluar el rendimiento monetario de la misma

    Scenario: Generar budget para cada mes del anio
        Given que se tiene "6225.8065" como costo planeado por actividad ejecutada en "ITEM 104 Std. Valve"
        And en "March" se han planificado "3" actividad
        When el CPAE de "March" sea "18677.42" 
        And el budget de "February" sea "18677.42"
        Then el budget de "March" debe ser "37354.84"

    Scenario: Generar el costo real acumulado para cada mes del anio
        Given que existen actividades ejecutadas en "ITEM 104 Std. Valve" en "March" y son
        | Well    | ITEM 104 Std. Valve_Productos | ITEM 104 Std. Valve_Servicios|
        | ACA-020 |                0              | 326.40                       |
        | CHEA-007 |               0              | 252.55                       |
        | ACAQ-114 |               0              | 12152.40                     |
        When se suman los costos de las actividades ejecutadas en "March"
        And el costo real acumulado de "February" es "10011.40"
        Then el costo real acumulado de "March" debe ser "22742.75" 

    Scenario: Generar el presupuesto ajustado para cada mes del anio
        Given que el costo real de "March" es "12731.35" de "ITEM 104 Std. Valve"
        When el presupuesto proyectado de "March" sea "12731.35"
        And el presupuesto ajustado de "February" sea "10011.40"
        Then el presupuesto ajustado de "March" debe ser "22742.75"


    Scenario: Generar grafico de forecast de la linea 104
        Given que se tiene el df_df_budget, df_forecast, df_real_cost_accumulated, df_executed_activities, df_planned_activities, title de "ITEM 104 Std. Valve"
        When se genera el grafico de forecast para "ITEM 104 Std. Valve"
        #Then el grafico debe mostrar los valores correctos

'''
    Este escenario es igual al de arriba, y tambien pasa con los datos que se tienen.

    Scenario: Generar el presupuesto ajustado cuando no exista costo real
    Given que el costo real de "April" es "0" de "ITEM 104 Std. Valve"
            When el presupuesto proyectado de "April" sea "18677.43"
            And el presupuesto ajustado de "March" sea "22742.75"
            Then el presupuesto ajustado de "April" debe ser "41420.18"

'''

