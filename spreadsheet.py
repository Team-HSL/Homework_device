#参考にしたサイト
#https://tanuhack.com/python/operate-spreadsheet/

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

#スプレッドシートを編集する関数
#引数は日時(month/day;string)と生徒(int)の出席番号
def spreadsheet(date,student_num):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('homework-b9734e35d0c4.json', scope)
    gc = gspread.authorize(credentials)

    #共有設定したスプレッドシートキーを変数[SPREADSHEET_KEY]に格納する。
    SPREADSHEET_KEY = '1MUx-mK_u2MaON5KUqtLM0IczSPyj_89v3hiRcIzAotI'

    #共有設定したスプレッドシートのシート1を開く
    ws = gc.open_by_key(SPREADSHEET_KEY).sheet1

    values_list = ws.row_values(1) #1列目の要素を取得
    try:
        date_index = values_list.index(date)
        date = datetime.datetime.today().strftime("%m/%d")
        ws.update_cell(student_num + 1, date_index + 1, date + ' 提出')
        student_name = ws.cell(student_num + 1, 2).value
        message = "出席番号" + str(student_num) + "番の" + student_name + "さん，宿題よくがんばりました"

    except ValueError:
        message = "シートに該当の日付が存在しません"

    return message


