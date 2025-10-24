SQL_QUERY_BUDGET = """
    Select 
    ITEM_NAME AS 'POZO'
    , START_DATETIME AS 'DATE'
    , YEAR AS 'Year' 
    , MONTH AS 'Month' 
    , RIG AS 'Rig' 
    , WORK_STAT_SLB AS 'Status Trabajos SLB' 
    , ACTIVITY AS 'Activity' 
    , TYPE_EX AS 'Type' 
    , BUDGET AS 'Budget' 
    , AFE_ESP AS 'AFE Especifico' 
    , ACT_COST AS 'Actual Cost' 
    , BUDGET_DEV AS 'Budget Deviation' 
    , AFE_DEV AS 'AFE Deviation' 
    , AFE_DEV_MOC AS 'AFE Deviation+MOC' 
    , ALS_BYH AS 'ALS B&H' 
    , MOC AS 'MOC' 
    , COV_SAVINGS AS 'Covered by Savings' 
    , COV_CONTIGENCY AS 'Covered by contingency' 
    , CPS_BYH2 AS 'CPS B&H2' 
    , ACT_COST_WO_BH AS 'ACTUAL COST WO/B&h' 
    , COST_BUDGET AS 'Costo vs Budget' 
    , COST_AFE_ESP AS 'Costo vs AFE Especifico' 
    , WI_RIG_1_1 AS '1.1 WI RIG' 
    , MI_SWACO_1_2 AS '1.2 M-I Swaco' 
    , COMPLET_1_03 AS '1.03 Completions' 
    , BIT_DRIL_RE_1_4 AS '1.4 Bits, Drilling Tools & Remedial (B,D &R)' 
    , SURF_SYS_1_5 AS '1.5 Surface Systems (CSUR)' 
    , WIRELINE_1_6 AS '1.6 Wireline' 
    , WS_1_7 AS '1.7 Well Services (WS)' 
    , TEST_F_1_8 AS '1.8 Testing & Fluid Analysis' 
    , TUBULARS_1_9 AS '1.09 Tubulars' 
    , SERVICES_1_10 AS '1.10 Services' 
    , ENVIROMENT_1_11 AS '1.11 Environment' 
    , FIN_1_12 AS '1.12 Finance (SHE + ARCH)' 
    , ATL_1_13 AS '1.13 Artificial Lift' 
    , ISM_1_14 AS '1.14 Integrated Services Management' 
    , TT_1_15 AS '1.15 Tanks and Trunks' 
    , OFS_SERVICES AS 'OFS SERVICES' 
    , T_PRT_SERV AS '3rd Party SERVICES' 
    , PROD_PLAN AS 'Production Plan (bopd)' 
    , REAL_PROD AS 'Production Real (bopd)' 
    , COMMENT AS 'Comment on Production' 
    , PLAN_TIME AS 'Time Plan (Days)' 
    , REAL_TIME AS 'Time Real (Days)' 
    , COMMENT_TC AS 'Comment on Time / Cost' 
    , CURVE AS 'Curve'
    
    from VT_EXEC_REPORT_en_US
    
    ORDER BY START_DATETIME
"""

SQL_QUERY_FAILS = """
        DECLARE @START_DATETIME DATETIME, @END_DATETIME DATETIME
        SET @START_DATETIME = '01/01/2024'
        SET @END_DATETIME = '12/31/2024'

        SELECT DATETIME AS MENSUAL,
        (
        SELECT top 1 CAST(OIL AS FLOAT) FROM tmp_V_TEMP_TOTALS
        WHERE MENSUAL = D.DATETIME 
        ) OIL,
        D.DAYS_IN_MONTH DM,
        (
        SELECT CAST(ISNULL(LEV1,0) AS FLOAT)  FROM [dbo].[V_FAILS_ELEMENT_STATISTICS]
        WHERE MENSUAL = D.DATETIME
        ) FAILS,
        (
            (
            CASE
            WHEN D.DATETIME >= '01/01/2016' AND D.DATETIME < '01/01/2018' THEN
            (SELECT ROUND(Ifmp,2) FROM V_FAILS_IFmovil mov
            where mov.MENSUAL = D.DATETIME
            )
            ELSE
                CAST(
                ((
                SELECT ISNULL(LEV1,0) FROM [dbo].[V_FAILS_ELEMENT_STATISTICS]
                WHERE MENSUAL = D.DATETIME
                ) * 12)
                AS FLOAT) / 
                (
                SELECT CAST(OIL AS FLOAT) FROM tmp_V_TEMP_TOTALS
                WHERE MENSUAL = D.DATETIME 
                )
            END
            )
        ) IFmp,
        (
            (
            CASE
            WHEN D.DATETIME >= '01/01/2016' AND D.DATETIME < '01/01/2018' THEN
            (SELECT ROUND(Ifmov,2) FROM V_FAILS_IFmovil mov
            where mov.MENSUAL = D.DATETIME
            )
            ELSE
            (SELECT SUM(A_FAILS.N_FAILS) FROM 
                    (
                        SELECT TOP 12 MENSUAL,  ISNULL(LEV1,0)  N_FAILS FROM [dbo].[V_FAILS_ELEMENT_STATISTICS]
                        WHERE YEAR(MENSUAL) >= YEAR(D.DATETIME)-1 AND MENSUAL <= D.DATETIME
                        ORDER BY MENSUAL DESC
                    )A_FAILS)/
                    (
                        SELECT AVG(CAST(OIL AS FLOAT)) FROM (
                        SELECT top 12 OIL FROM tmp_V_TEMP_TOTALS 
                        WHERE YEAR(MENSUAL)>= YEAR(D.DATETIME)-1 AND MENSUAL <= D.DATETIME
                        ORDER BY MENSUAL DESC
                        )DATA 
                    )
            END
            )
        )IFmov
        FROM DATE_INFO D
        WHERE D.DATE_TYPE = 'M'
        AND DATETIME >= @START_DATETIME
        AND DATETIME <= @END_DATETIME
        ORDER BY DATETIME
"""