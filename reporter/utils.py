import requests, json, csv, os, gspread, time
from dotenv import load_dotenv
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from yametrep.settings import BASE_DIR

load_dotenv()

def gsreap_auth():
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    GOOGLE_JSON = os.environ.get('GOOGLE_JSON')
    json_key_file = BASE_DIR / f'reporter/{GOOGLE_JSON}'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_key_file, scope)
    client = gspread.authorize(credentials)
    return client


def delete_gspread_file(link):
    client = gsreap_auth()
    if link.gs_id != 'no-id':
        client.del_spreadsheet(link.gs_id)


def export_to_gspread(file, name, email):

    client = gsreap_auth()
    now = datetime.now()
    date_time = now.strftime("%m-%d-%Y_%H-%M-%S")
    filename = f'{name}_' + date_time

    spreadsheet = client.create(filename)
    spreadsheet.share(email, perm_type='user', role='writer')

    with open(file, 'r') as file_obj:
        content = file_obj.read().encode("utf-8")
        client.import_csv(spreadsheet.id, data=content)

    return f'https://docs.google.com/spreadsheets/d/{spreadsheet.id}/', filename, spreadsheet.id


def new_dates(date1, date2):
    nxt_date_1 = datetime.strptime(date1, '%Y-%m-%d') + relativedelta(months=1)
    nxt_date_2 = datetime.strptime(date2, '%Y-%m-%d') + relativedelta(months=1)
    if nxt_date_1.day == 1:
        nxt_date_2 = nxt_date_2.replace(day=monthrange(nxt_date_2.year, nxt_date_2.month)[1])
    return nxt_date_1.strftime('%Y-%m-%d'), nxt_date_2.strftime('%Y-%m-%d')


def number_of_days_in_month(date):
    date = datetime.strptime(date, '%Y-%m-%d')
    return monthrange(date.year, date.month)[1]


def convert_time(seconds):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def make_row(metric, source_name, data, metric_id, startDates):
    trafic = []
    trafic.append(source_name)
    prev_value = None
    current_value = None
    dayly_prev_value = None
    dayly_current_value = None

    for date in startDates:
        try:
            value = data[source_name][date][metric_id]

            if metric == 'Визиты':
                trafic.append(int(value))
                day_value = round(value / number_of_days_in_month(date))
                dayly_prev_value, dayly_current_value = dayly_current_value, day_value
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
            trafic += 2 * [value]

        prev_value, current_value = current_value, value

    try:
        progress_value = f'{round((current_value / prev_value - 1) * 100, 1)}%'.replace('.', ',')
        trafic.append(progress_value)

    except:
        trafic.append('-')

    try:
        if dayly_prev_value is not None:
            progress_value = f'{round((dayly_current_value / dayly_prev_value - 1) * 100, 1)}%'.replace('.', ',')
            trafic.append(progress_value)
        else:
            progress_value = f'{round((current_value / prev_value - 1) * 100, 1)}%'.replace('.', ',')
            trafic.append(progress_value)
    except:
        trafic.append('-')
    return trafic


def greater_than_today(date):
    now = datetime.now()
    date = datetime.strptime(date, '%Y-%m-%d')
    return now < date


def get_data_and_dates_metrika(token, ids, date1, date2, months):

    header_token = {
        'Authorization': f'OAuth {token}',
    }

    dates = None
    data = None

    for i in range(months):

        if dates is None: dates = []
        if data is None: data = {}

        parameters = {
            'date1': date1,
            'date2': date2,
        }

        views = {
            'all': {},
            'source_detail': {'dimensions': 'ym:s:lastsignTrafficSource'},
            'yandex': {'filters': "ym:s:<attribution>SearchEngineRootName=='Яндекс'"},
            'google': {'filters': "ym:s:<attribution>SearchEngineRootName=='Google'"}
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
                    source = 'Яндекс' if payload['filters'] == "ym:s:<attribution>SearchEngineRootName=='Яндекс'" else 'Google'
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

        if greater_than_today(date2):
            return data, dates

    return data, dates


def write_csv(data, dates, project_name):

    startDates = sorted(dates)
    modify_dates = [' ', ]
    for date in startDates:
        modify_dates.extend([date, ' '])

    periods = ['Всего', 'За сутки']


    with open(BASE_DIR / f'reporter/tempfiles/{project_name}.csv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t', dialect='excel')
        writer.writerow(modify_dates)
        periods_row = [' '] + periods * len(startDates) + ['Изменение за месяц'] + ['Изменение за сутки']
        writer.writerow(periods_row)

        metrics = ['Визиты', 'Отказы', 'Глубина', 'Время на сайте']

        source_detail = ['Яндекс', 'Google']

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