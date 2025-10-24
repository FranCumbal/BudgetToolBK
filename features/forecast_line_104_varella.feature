Feature: make forecast graph to the varillera line
    As an engineer responsible for the Varillera line
    I want to make a forecast for my line
    To evaluate its monetary performance

    Scenario: Generate budget by month in the year
        Given "5" activities planned to "2025" in the "ITEM 104 Varillera" initially distributed in the months as
        | Month     | Initially Planned Activities |
        | january   |             1                |
        | february  |             1                |
        | march     |             1                |
        | april     |             1                |
        | may       |             1                |
        | june      |             0                |
        | july      |             0                |
        | august    |             0                |
        | september |             0                |
        | october   |             0                |
        | november  |             0                |
        | december  |             0                |
      
        When the AFECOST avarage from catalog is calculated
        And the result of AFECOST avarage is "1333.33" 
        And the CPAE of "January" is "1333.33"
        And the CPAE of "February" is "1333.33"
        Then the budget value of "February" should be "2666.66" 
    
    Scenario: Generate Real Cost Accumulated for each month in the year
        Given that there are "2" executed activities in "ITEM 104 Varillera" in "April" and they are
        | Well     | STATUS  | ITEM 104 Varillera_Productos | ITEM 104 Varillera_Servicios| ITEM 104 Varillera_B&H Cost |
        | CNOI-040 | Final   |          0.0                 | 29457.17                    |             0.0             |
        | ACAJ-271 | Pending |          0.0                 | 80000.00                    |             0.0             |
        When the costs of the executed activities whit status "Final" in "April" are summed and it is "29457.17"
        And the real cost of "April" is "29457.17"
        And the real cost accumulated of "March" is "432909.00"
        Then the real cost accumulated of "April" should be "462366.17"

    Scenario: Generate forecast in a month in the year
        Given that there are "1" scheduled executed activities in "ITEM 104 Varillera" in "June" and they are
        |   Well   | Net Total (USD) |  Validation |
        | PTLA-002 |    38749.67     |     Yes     |
        When the Net Total (USD) of the schedule executed activities whit validation "Yes" in "June" are summed
        And the proyected cost of "June" is "38749.67"
        And the proyected cost of "May" is "107366.09"
        And the forecast of "May" is "107366.09"
        Then the forecast of "June" should be "146115.76" 
        '''

    '''Falta un escenario tal vez. Este debe generar el df de las Scheduled Executed Activities'''