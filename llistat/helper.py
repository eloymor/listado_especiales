from datetime import datetime
import pandas as pd


def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, '%d/%m/%y').date()  # dd/mm/yy
    except ValueError:
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()  # dd/mm/yyyy
        except ValueError:
            return None

def costumers_delay(dataframe: pd.DataFrame, n=10) -> (pd.DataFrame, pd.DataFrame):
    """returns 2 dataframes with top n customers and their delays"""

    df = dataframe.copy()
    df_peticionario = df.groupby(by='Peticionario')['OM']\
                        .agg({'count'})\
                        .sort_values(by='count', ascending=False)[:n]
    df_pet_delay = (df.loc[(df['Fecha_Fin_Prevista'] < datetime.today()) & (
                    df['Peticionario'].isin(df_peticionario.index)
                    )]
                    .groupby('Peticionario')['OM']
                    .agg({'count'}).sort_values(by='count', ascending=False))

    no_delay = {}
    for idx in df_peticionario.index:
        if idx not in df_pet_delay.index:
            no_delay[idx] = 0

    df_pet_delay = pd.concat([pd.DataFrame(no_delay, index=[0]).T.rename(columns={0: 'count'}),
                              df_pet_delay], axis=0).\
                                sort_values(by='count', ascending=False)

    df_pet_no_delay = df_peticionario - df_pet_delay
    return df_pet_no_delay, df_pet_delay
