import itertools
import numexpr
import pandas as pd
import numpy as np

def check_arbitrage(df_arbitrage, list_bet_name):
    col_team1 = 'team_name_1'
    col_team2 = 'team_name_2'

    bet_value = 100

    columns = np.array(
        [[f'{bet}_odd_{i}' for i in range(1, 4)] for bet in list_bet_name]
    )

    divcols = []
    suffixo = '_div1'
    for d in columns.flatten():
        new_column = f'{d}{suffixo}'
        df_arbitrage[new_column] = (1 / df_arbitrage[d]).astype(np.float64)
        divcols.append(new_column)

    compare_columns = np.array(divcols).reshape(columns.shape)
    itercols = itertools.product(*compare_columns.T)

    table = pd.concat(
        [df_arbitrage[col] for col in map(list, itercols)], ignore_index=True, copy=False
    ).fillna(0)

    more_than_1 = numexpr.evaluate(
        'sum(table, 1)',
        global_dict={},
        local_dict={'table': table},
    )

    less_than_1 = numexpr.evaluate(
        'more_than_1<1', global_dict={}, local_dict={'more_than_1': more_than_1}
    )

    good_results = table[less_than_1]

    table_columns = pd.DataFrame(
        np.tile(table.columns, ((len(good_results)), 1))
    )

    not_zero = numexpr.evaluate(
        'good_results != 0',
        global_dict={},
        local_dict={'good_results': good_results},
    )

    good_ind = np.where(not_zero)

    good_results_np_array = np.array(
        [good_results.iat[*h] for h in zip(*good_ind)]
    ).reshape((-1, 3))

    good_results_np_array_col = np.array(
        [table_columns.iat[*h] for h in zip(*good_ind)]
    ).reshape((-1, 3))

    allresults = []

    for col, number in zip(good_results_np_array_col, good_results_np_array):
        original = [x[: -len(suffixo)] for x in col]

        win = df_arbitrage.loc[
            (df_arbitrage[col[0]] == number[0])
            & (df_arbitrage[col[1]] == number[1])
            & (df_arbitrage[col[2]] == number[2])
        ][list((col_team1, col_team2, *col, *original))]
        if not win.empty:
            win.columns = [
                'team1',
                'team2',
                'odd0',
                'odd1',
                'odd2',
                'odd_casa0',
                'odd_casa1',
                'odd_casa2'
            ]
        else:
            print('vazio')
        win['porcentagem'] = win[['odd0', 'odd1', 'odd2']].sum(axis=1)
        for i in range(len(col)):
            win[f'casa{i}'] = col[i]
            win[f'div{i}'] = win[f'odd{i}'] / win[f'porcentagem']
            win[f'aposta{i}'] = bet_value * win[f'div{i}']
            win[f'lucro{i}'] = win[f'aposta{i}'] * win[f'odd_casa{i}'] - 100
        allresults.append(win)
    try:
        df_final = (
            pd.concat(allresults).sort_values(by=f'porcentagem').reset_index(drop=True)
        )
        print('ARBITRAGEM------------')
        unique = df_final[['team1', 'team2', 'casa0', 'casa1', 'casa2', 'odd_casa0', 'odd_casa1', 'odd_casa2', 'aposta0', 'aposta1', 'aposta2', 'lucro0', ]]
        print(unique)
    except Exception:
        df_final = pd.DataFrame()
        print('NÃO HÁ ARBITRAGENS NO MOMENTO')