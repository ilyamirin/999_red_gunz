import pandas as pd
from pandas import read_excel
from datetime import datetime
import db_connector as dbc


def filter_none(text):
    if not text or text != text:  # None or NAN
        raise ValueError('Пустая строка в BILL_ID или TITLE')
    else:
        return text


def filter_to_bool(x):
    if x not in ['0', '1', 0, 1]:
        raise ValueError('Ошибка в значениях is_note, is_pdf')
    elif x == '0' or x == 0:
        return False
    else:
        return True


def filter_date(date):
    try:
        if type(date) == str:
            _ = datetime.strptime(date, "%Y-%m-%d")
            return date
        elif type(date) == type(pd.Timestamp(1)):
            date = date.date().__str__()
            return date
        else:
            raise TypeError('Тип даты не распознан!')
    except Exception as e:
        raise e


def filter_vote(vote):
    try:
        return int(vote)
    except Exception as e:
        raise e


def add_bill_excel(sheet):
    try:
        page = read_excel(sheet)
        correct_titles = ['BILL_ID', 'TITLE', 'DATE', 'IS_NOTE', 'IS_PDF', 'IS_SECRET', 'VOTE_FOR', 'VOTE_AGAINST',
                          'NOT_VOTED','ABSTAINED']
        if page.columns.to_list() != correct_titles:
            raise ValueError('Неверно указаны заголовки.')
        bill = page.iloc[0]
        bill_data = {
            'bill_id': filter_none(bill['BILL_ID']),
            'title': filter_none(bill['TITLE']),
            'date': filter_date(bill['DATE']),
            'is_note': filter_to_bool(bill['IS_NOTE']),
            'note_id': None,
            'is_pdf': filter_to_bool(bill['IS_PDF']),
            'pdf_id': None,
            'is_secret': filter_to_bool(bill['IS_SECRET']),
            'vote_for': filter_vote(bill['VOTE_FOR']),
            'vote_against': filter_vote(bill['VOTE_AGAINST']),
            'not_voted': filter_vote(bill['NOT_VOTED']),
            'abstained': filter_vote(bill['ABSTAINED']),
        }
        is_bill = dbc.check_bill(bill_data['bill_id'])
        return is_bill, bill_data, None
    except Exception as e:
        return False, {}, e


# ФУНКЦИИ ДЛЯ ОБРАБОТКИ РЕЗУЛЬТАТОВ ГОЛОСОВАНИЯ ДЕПУТАТОВ

parties = read_excel('app_data/deputies_parties.xlsx')
deputies_region = read_excel('app_data/deputies_region.xlsx')


def get_deputies_by_region(region: str):
    try:
        deps = deputies_region[deputies_region['REGIONS'] == region]
        if len(deps) == 0:
            raise ValueError('Регион указан неверно!')
        deps = deps['DEPUTIES'].to_list()[0]
        return deps.split(', '), None
    except Exception as e:
        return None, e


def get_parties_by_deps(deps: list):
    try:
        result = {}
        for dep in deps:
            result[dep] = parties[parties['DEPUTIES'] == dep].PARTI_ABB.values[0]
        return result, None
    except Exception as e:
        return None, e


def filter_votes(vote: float):
    correct_votes = {
        1.0: 'За',
        -1.0: 'Против',
        0: 'Воздержался'
    }
    try:
        return correct_votes[vote]
    except:
        return 'Не голосовал'


def get_deputies_votes(bill_id, deps):
    votes = read_excel(f"vote_results/{bill_id}.xlsx")
    votes = votes[votes['DEPUTIES'].isin(deps)]

    corrected_votes = [filter_votes(i) for i in votes.VOTES]

    deps_votes = {}
    for i in range(len(deps)):
        deps_votes[deps[i]] = corrected_votes[i]
    return deps_votes


def get_deps_data(bill_id, region):
    deps, e = get_deputies_by_region(region)
    if e:
        raise e
    parties_deps, e = get_parties_by_deps(deps)
    if e:
        raise e
    votes = get_deputies_votes(bill_id, deps)

    deps_data = []
    for dep in parties_deps.keys():
        deps_data.append(f"{dep}({parties_deps[dep]}) - {votes[dep]}")
    return deps_data


def filter_deps_data(deps_data):
    df = read_excel(deps_data)
    if df.columns.to_list() != ['DEPUTIES', 'VOTES']:
        raise ValueError('Ошибка с заголовками!')
    if df.dtypes['DEPUTIES'].name != 'object' or df.dtypes['VOTES'] not in ['float64', 'int64']:
        raise TypeError('Ошибка типов значений в колонках.')
    if df.shape != (444,2):
        raise ValueError('Количество строк в таблице не равно 444')
    return True
