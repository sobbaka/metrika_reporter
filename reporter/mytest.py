from utils import get_data_and_dates_metrika, write_csv, export_to_gspread
import os

project_name = 'ter_4'
ids = 13969186
token = 'AgAAAAAJilIoAAQAJ2jq_d6Askoco_k2NHLSNdc'

months = 3
date1 = '2021-08-02'
date2 = '2021-09-01'


data, dates = get_data_and_dates_metrika(token, ids, date1, date2, months)

write_csv(data, dates, project_name)

file_exists = os.path.exists(f'./{project_name}.csv')

if file_exists:
    link = export_to_gspread(f'{project_name}.csv')
    print(link)
