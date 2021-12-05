import requests
import json
import csv
from calendar import monthrange
import time
from datetime import date
from dateutil.relativedelta import relativedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


def export_to_gspread(file):
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    credentials = ServiceAccountCredentials.from_json_keyfile_name('metrika-reports-952f7211156b.json', scope)
    client = gspread.authorize(credentials)

    now = datetime.now()
    date_time = now.strftime("%m-%d-%Y_%H-%M-%S")
    filename = 'metrika_rep_' + date_time


    spreadsheet = client.create(filename)
    spreadsheet.share('a.bagaev1989@gmail.com', perm_type='user', role='writer')


    with open(file, 'r') as file_obj:
        content = file_obj.read().encode("utf-8")
        client.import_csv(spreadsheet.id, data=content)

    return f'https://docs.google.com/spreadsheets/d/{spreadsheet.id}/'


def new_dates(date1, date2):
    next_date1 = datetime.strptime(date1, '%Y-%m-%d') + relativedelta(months=1)
    next_date1 = next_date1.strftime('%Y-%m-%d')

    date_start = [int(i) for i in date1.split('-')]

    if date_start[2] > 1:
        date2 = date2
        next_date2 = datetime.strptime(date2, '%Y-%m-%d') + relativedelta(months=1)
        next_date2 = next_date2.strftime('%Y-%m-%d')
        return next_date1, next_date2

    date_start[1] += 1
    date_start[2] = monthrange(date2[0], date2[1])[1]
    next_date2 = date(*date_start)
    next_date2 = next_date2.strftime('%Y-%m-%d')

    return next_date1, next_date2




def number_of_days_in_month(date):
    date = [int(value) for value in date.split('-')]
    year = date[0]
    month = date[1]
    return monthrange(year, month)[1]


def convert_time(seconds):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def make_row(metric, source_name, data, metric_id, startDates):
    trafic = []
    trafic.append(source_name)
    prev_value = None
    last_value = None

    for date in startDates:
        try:
            value = data[source_name][date][metric_id]

            if metric == 'Визиты':
                trafic.append(int(value))
                day_value = round(value / number_of_days_in_month(date))
                trafic.append(day_value)

            else:
                if metric == 'Отказы':
                    bounce_value = f'{round(value, 2)}%'.replace('.', ',')
                    trafic.append(bounce_value)

                if metric == 'Глубина':
                    depth_value = round(value, 1)
                    depth_value = str(depth_value).replace('.', ',')
                    trafic.append(depth_value)

                if metric == 'Время на сайте':
                    time_value = convert_time(value)
                    trafic.append(time_value)

                trafic.append('-')
        except:
            value = '-'
            trafic.append(value)
            trafic.append(value)

        prev_value = last_value
        last_value = value
    try:
        progress_value = f'{round((last_value / prev_value - 1) * 100, 1)}%'.replace('.', ',')
        trafic.append(progress_value)
    except:
        trafic.append('-')
    return trafic


def get_data_and_dates_metrika(token, ids, date1, date2, months):

    header_token = {
        'Authorization': f'OAuth {token}',
    }

    dates = None
    data = None

    for i in range(months):

        if dates is None:
            dates = []
        if data is None:
            data = {}

        parameters = {
            'date1': date1,
            'date2': date2,
        }

        views = {
            'all': {},
            'source_detail': {'dimensions': 'ym:s:lastTrafficSource'},
            'yandex': {'filters': "ym:s:SearchEngineRootName=='Яндекс'"},
            'google': {'filters': "ym:s:SearchEngineRootName=='Google'"}
        }

        payload_new = {
            'metrics': 'ym:s:visits, ym:s:bounceRate, ym:s:pageDepth, ym:s:avgVisitDurationSeconds',
            'date1': parameters['date1'],
            'date2': parameters['date2'],
            'ids': ids,
            'accuracy': 'full',
            'pretty': 'true',
        }

        for view in views.keys():
            payload = payload_new.copy()
            payload.update(views[view])

            request = requests.get('https://api-metrika.yandex.ru/stat/v1/data', params=payload, headers=header_token)
            my_json = json.loads(request.content)

            for item in my_json['data']:

                if 'filters' in payload.keys():
                    source = payload['filters']
                    date = date1

                elif 'dimensions' in payload.keys():
                    source = item['dimensions'][0]['name']
                    date = date1

                else:
                    source = 'Всего по сайту'
                    date = date1

                metrics = item['metrics']

                if source not in data.keys():
                    data[source] = {}
                    data[source][date] = metrics
                else:
                    data[source][date] = metrics

        dates.append(date1)
        date1, date2 = new_dates(date1, date2)

    return data, dates


def write_csv(data, dates, project_name):

    dates = sorted(dates)
    startDates = dates
    modify_dates = [' ', ]
    for date in startDates:
        modify_dates.append(date)
        modify_dates.append(' ')

    periods = ['Всего', 'За сутки']


    with open(f'{project_name}.csv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t', dialect='excel')
        writer.writerow(modify_dates)
        periods_row = [' '] + periods * len(startDates) + ['Изменение']
        writer.writerow(periods_row)

        metrics = ['Визиты', 'Отказы', 'Глубина', 'Время на сайте']


        source_detail = ["ym:s:SearchEngineRootName=='Яндекс'", "ym:s:SearchEngineRootName=='Google'",]

        for metric_id, metric in enumerate(metrics):
            writer.writerow([metric, ])
            source_name = 'Всего по сайту'
            trafic = make_row(metric, source_name, data, metric_id, startDates)
            writer.writerow(trafic)

            for source_name in data.keys():
                source_name = source_name

                trafic = None

                if source_name in source_detail or source_name == 'Всего по сайту':
                    continue

                if source_name == 'Переходы из поисковых систем':
                    trafic = make_row(metric, source_name, data, metric_id, startDates)
                    writer.writerow(trafic)

                    for source_name_detail in source_detail:
                        trafic = make_row(metric, source_name_detail, data, metric_id, startDates)
                        writer.writerow(trafic)
                        trafic = None
                else:
                    trafic = make_row(metric, source_name, data, metric_id, startDates)
                    writer.writerow(trafic)