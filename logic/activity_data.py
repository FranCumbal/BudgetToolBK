import calendar
import pandas as pd
def build_activities_dataframe(data_loader, plan_actividades, year):
    """
    Construye un DataFrame consolidado con:
    - Actividades planificadas (plan_actividades)
    - Actividades ejecutadas (data_loader.load_executed_activities)
    - Fallas por mes (data_loader.fetch_fails_by_year)

    Retorna un DataFrame con columnas:
    - MONTH
    - PLANNED_ACTIVITIES
    - EXECUTED_ACTIVITIES
    - FAILS
    """
    try:
        # 1️⃣ Planificadas desde plan_actividades
        '''
        print(plan_actividades, "HOLAxs")
        if(plan_actividades.sheet_name == f"Plan{year}"):
            distribucion_df = plan_actividades.plan_df
        else: 
            distribucion_df = plan_actividades.calcular_distribucion_por_tipo(year=year)
        '''
        distribucion_df = plan_actividades.calcular_distribucion_por_tipo(year=year)
        columnas_meses = [c for c in distribucion_df.columns if c not in ['No.', 'Tipo de Actividad', 'Total']]
        total_por_mes = {month: distribucion_df[month].sum() for month in columnas_meses}
        planned_df = pd.DataFrame({
            "MONTH": list(total_por_mes.keys()),
            "PLANNED_ACTIVITIES": list(total_por_mes.values())
        })
        print(planned_df, "total por mes")

        # 2️⃣ Ejecutadas desde Excel
        executed_df = data_loader.load_executed_activities(year)
        executed_df.columns = executed_df.columns.str.upper()

        # 3️⃣ Fallas desde SQL
        fails_df = data_loader.fetch_fails_by_year(year)
        fails_df["MONTH"] = fails_df["Month"].apply(lambda x: calendar.month_name[x])
        fails_df.drop(columns=["Month"], inplace=True)
        fails_df.rename(columns={"TotalFails": "FAILS"}, inplace=True)
        fails_df.columns = fails_df.columns.str.upper()

        # 4️⃣ Unificar también nombres de columnas del plan
        planned_df.columns = planned_df.columns.str.upper()

        # 5️⃣ Merge
        df = planned_df.merge(executed_df, on="MONTH", how="left")
        df = df.merge(fails_df, on="MONTH", how="left")
        df.fillna(0, inplace=True)

        # Convertir a enteros
        df["PLANNED_ACTIVITIES"] = df["PLANNED_ACTIVITIES"].astype(int)
        df["EXECUTED_ACTIVITIES"] = df["EXECUTED_ACTIVITIES"].astype(int)
        df["FAILS"] = df["FAILS"].astype(int)
        print("MIRAAA")
        print(df)
        # Restar una actividad al mes de noviembre en la columna PLANNED ACTIVITIES
        df.loc[df["MONTH"] == "November", "PLANNED_ACTIVITIES"] -= 1

        return df

    except Exception as e:
        print(f"❌ Error al construir dataframe de actividades: {e}")
        return pd.DataFrame()
