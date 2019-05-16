from pytrends.request import TrendReq
import sqlalchemy
import datetime
import pandas  as pd
import random
import pymysql.cursors
from sqlalchemy import desc
import os
import json
import pika

e = os.environ
e['host']='185.230.142.61'
e['login']='externalanna'
e['password']='44iAipyAjHHxkwHgyAPrqPSR5'

e['host_mysql']='clh.datalight.me'
e['user']='reader'
e['password_mysql']='nb7hd-1HG6f'
e['db_mysql']='coins_dict'

e['login_MQ']='google_trends'
e['password_MQ']='X3g6unrboVScnyfe'
e['host_MQ']='parser.datalight.me'
e['queue']='google_trends'
# e['start']='451'
# e['end']='900'


class DB:

    def __init__ (self):
        self.con = self.get_param_for_db()

    def get_already_cuurency(self):
        date=datetime.datetime.now()-datetime.timedelta(days=1)
        date=datetime.datetime.strptime(str(date.date())+' 00:00','%Y-%m-%d %H:%M')
        select=currency.select().with_only_columns([currency.c.currency]).where(currency.c.dttm==date).group_by(currency.c.currency)
        db=self.con.execute(select)
        curren=[]
        for item in db:
            curren.append(item._row[0])
        return curren

    def get_param_for_db (self):
        url = 'postgresql://{}:{}@{}:5432/{}'
        setting = {}
        setting['host'] = e.get('host')
        setting['login'] = e.get('login')
        setting['password'] = e.get('password')
        # setting['host'] = e.get('host')
        # setting['login'] = e.get('login')
        # setting['password'] = e.get('password')
        url = url.format(setting['login'], setting['password'], setting['host'], 'prosphero')
        con = sqlalchemy.create_engine(url, echo=True)
        return con

    def return_connection (self):
        return self.con

    def insert (self, result):
        if len(result)==0:
            return 0
        cur_insert=[]
        for item in result:
            insert = dict(
                currency=item[1],
                not_cited=item[0],
                cited=item[2],
                dttm=item[3],
                on_currency=item[4]
            )
            cur_insert.append(insert)
        self.con.execute(currency.insert(),cur_insert)


DB_postgres = DB()
meta = sqlalchemy.MetaData(bind=DB_postgres.con, reflect=True, schema='google')
currency = meta.tables['google.currency_normalize']


def get_currency_name (start, end):
    result = []
    url_mysql = 'mysql+mysqldb://reader:nb7hd-1HG6f@clh.datalight.me:3306/coins_dict'
    connection = pymysql.connect(host=e.get('host_mysql'),
                                 user=e.get('user'),
                                 password=e.get('password_mysql'),
                                 db=e.get('db_mysql'),
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            # Create a new record
            sql = "SELECT source_id, inside_id, symbol FROM coins_dict.coins_source_id where `source`='google_trends' and inside_id>{} and inside_id<{};".format(start,end)
            cursor.execute(sql)

            for item in cursor:
                result.append(item)

    except Exception as er:
        print('error MySQL')
    finally:
        connection.close()
    return result


def get_cites (name_currency):
    df1 = get_dataframe_from_db()
    pytrend = TrendReq()
    to_list = df1.to_dict()
    for item_name, value in to_list.items():
        pytrend.build_payload(kw_list=[item_name, name_currency], timeframe='2018-09-02 2018-12-30')
        interest_over_time_df = pytrend.interest_over_time()

        get_d_btc = interest_over_time_df[item_name]
        get_currency = interest_over_time_df[name_currency]
        d_currency = get_currency.to_dict()
        count = 0

        for i in range(0, 20):
            key = random.choice(list(d_currency.keys()))
            if d_currency[key] == 0:
                count += 1

        if count > 15:
            continue
        d = get_d_btc.to_dict()
        table_currency = currency.select().with_only_columns([currency.c.dttm, currency.c.cited]).where(
            currency.c.currency == item_name)
        db = DB_postgres.con.execute(table_currency)
        result_db = {}
        for item in db:
            result_db[item[0]] = item[1]

        old_data = datetime.datetime.now() - datetime.timedelta(days=93)
        data_start = datetime.datetime.strptime('2017-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        for k, n in d.items():
            if k < data_start or k > old_data:
                continue
            if d_currency[k] == 0:
                d_currency[k] = 0.5
            mean_d = (d_currency[k] * result_db[k]) / d[k]
            for i in range(0, 7):
                temp_k = k + datetime.timedelta(days=i)
                DB_postgres.insert(mean_d, name_currency, d_currency[k], temp_k, item_name)

        break


def get_data_from_db (name_currency):

    table_currency = currency.select().with_only_columns([currency.c.dttm, currency.c.cited]).where(
        currency.c.currency == name_currency)
    db = DB_postgres.con.execute(table_currency)
    result_db = {}
    for item in db:
        result_db[item[0]] = item[1]
    return result_db


def get_cites_from_dttm (name_currency, dttm_start, dttm_end, on_currency):
    df1 = get_dataframe_from_db()
    name_currency_choose = df1.to_dict()
    pytrend = TrendReq()
    str_date = str(dttm_start.date()) + ' ' + str(dttm_end.date())
    if on_currency == '':
        list_currency = []
        for i, j in name_currency_choose.items():
            list_currency.append(i)
    else:
        list_currency = [on_currency]
    for item_name in list_currency:
        on_currency = item_name
        count = 0
        pytrend.build_payload(kw_list=[item_name, name_currency], timeframe=str_date)
        try:
            interest_over_time_df = pytrend.interest_over_time()
        except Exception as e:
            print(e.args)

        get_d_btc = interest_over_time_df[item_name]
        get_currency = interest_over_time_df[name_currency]
        d_currency = get_currency.to_dict()
        i_count = 0
        if len(list_currency) != 1:
            for i, j in d_currency.items():
                if j == 0:
                    count += 1
                i_count += 1
                if i_count > 20:
                    break
            if count > 2 and item_name != 'miota':
                continue
        d = get_d_btc.to_dict()
        result=[]
        result_db = get_data_from_db(item_name)
        for k, n in d.items():
            temp=[]
            if k >= dttm_start and k <= dttm_end:
                try:
                    mean_d = (d_currency[k] * result_db[k]) / d[k]
                except Exception as e:
                    mean_d = 0.01
                if mean_d == 0:
                    # print(result_db[k])
                    mean_d = 0.01

                result_rb = dict(
                    keyword=name_currency,
                    dttm=str(k),
                    value=mean_d
                )
                result_rb = json.dumps(result_rb)
                insert_rabbit(result_rb)
                temp.append(d_currency[k])

                temp.append(name_currency)
                temp.append(mean_d)
                temp.append(k)
                temp.append(on_currency)
                result.append(temp)
        DB_postgres.insert(result)
        return on_currency


def find_currency (name_currency):
    cursor = currency.select().with_only_columns([currency.c.on_currency]).where(
        currency.c.currency == name_currency).limit(1)
    db = DB_postgres.con.execute(cursor)
    on_currency = ''
    for item in db:
        on_currency = item._row[0]
    return on_currency


def get_on_currency (name_currency):
    cursor = currency.select().with_only_columns([currency.c.on_currency]).where(
        currency.c.currency == name_currency).limit(1)
    db = DB_postgres.con.execute(cursor)
    for item in db:
        on_currency = item._row[0]
    return on_currency


def get_not_cited (name_currency, dttm):
    df1 = get_dataframe_from_db()
    pytrend = TrendReq()
    df = get_dataframe_from_db()
    to_list = df1.to_dict()
    item_name = get_on_currency(name_currency)
    pytrend.build_payload(kw_list=[name_currency], timeframe='today 5-y')
    interest_over_time_df = pytrend.interest_over_time()
    get_d_btc = interest_over_time_df[name_currency]
    get_currency = interest_over_time_df[name_currency]
    d_currency = get_currency.to_dict()
    d = get_d_btc.to_dict()
    dttm = datetime.datetime.strptime(dttm, '%Y-%m-%d %H:%M:%S')
    for k, n in d.items():
        if dttm >= k and dttm < k + datetime.timedelta(days=7):
            return get_currency[k]

    return -1


def get_last_data_db (currency_item, last_date):
    cursor = currency.select().with_only_columns([currency.c.cited, currency.c.not_cited]).where(
        (currency.c.currency == currency_item) & (currency.c.dttm == last_date))
    db = DB_postgres.con.execute(cursor)
    result = {}
    for item in db:
        result['cited'] = item._row[0]
        result['not_cited'] = item._row[1]
        return result


def get_btc (name_currency, dttm_start, dttm_end):
    pytrend = TrendReq()
    str_date = str(dttm_start.date()) + ' ' + str(dttm_end.date())
    pytrend.build_payload(kw_list=['bitcoin'], timeframe=str_date)
    interest_over_time_df = pytrend.interest_over_time()

    get_d_btc = interest_over_time_df['bitcoin']
    get_currency = interest_over_time_df[name_currency]
    d_currency = get_currency.to_dict()

    d = get_d_btc.to_dict()
    result_db = get_last_data_db('bitcoin', dttm_end)
    # coef = result_db['cited'] / d_currency[dttm_end]
    dttm_start = dttm_start + datetime.timedelta(days=1)
    for k, n in d.items():

        if k >= dttm_start and k <= dttm_end:
            mean_d = ((d_currency[k] * 100000) / 100)

            # mean_d=d_currency[k]*coef

            DB_postgres.insert(mean_d, name_currency, d_currency[k], k, name_currency)


def get_btc_coef (name_currency, dttm_start, dttm_end):
    pytrend = TrendReq()
    str_date = str(dttm_start.date()) + ' ' + str(dttm_end.date())
    pytrend.build_payload(kw_list=['bitcoin'], timeframe=str_date)
    interest_over_time_df = pytrend.interest_over_time()

    get_d_btc = interest_over_time_df['bitcoin']
    get_currency = interest_over_time_df[name_currency]
    d_currency = get_currency.to_dict()

    d = get_d_btc.to_dict()
    result_db = get_last_data_db('bitcoin', dttm_start)
    coef = result_db['cited'] / d_currency[dttm_start]
    dttm_start = dttm_start + datetime.timedelta(days=1)
    result=[]
    for k, n in d.items():
        temp=[]
        if k >= dttm_start and k <= dttm_end:
            # mean_d = ((d_currency[k] * 10000) / 100)

            mean_d = d_currency[k] * coef

            temp.append(d_currency[k])

            temp.append(name_currency)
            temp.append(mean_d)
            temp.append(k)
            temp.append(name_currency)
            result.append(temp)
            result_rb = dict(
                keyword=name_currency,
                dttm=str(k),
                value=mean_d
            )
            result_rb = json.dumps(result_rb)
            insert_rabbit(result_rb)
    DB_postgres.insert(result)


def get_cites_dttm_btc (name_currency, dttm_start, dttm_end):
    pytrend = TrendReq()
    str_date = str(dttm_start.date()) + ' ' + str(dttm_end.date())
    pytrend.build_payload(kw_list=['bitcoin'], timeframe=str_date)
    interest_over_time_df = pytrend.interest_over_time()

    get_d_btc = interest_over_time_df['bitcoin']
    get_currency = interest_over_time_df[name_currency]
    d_currency = get_currency.to_dict()

    d = get_d_btc.to_dict()

    for k, n in d.items():

        if k >= dttm_start and k <= dttm_end:
            mean_d = float((d_currency[k] * 10000) / 100)
            DB_postgres.insert(mean_d, name_currency, d_currency[k], k, name_currency)


def insert_rabbit (data_insert):
    credentials = pika.PlainCredentials(e.get('login_MQ'), e.get('password_MQ'))
    parameters = pika.ConnectionParameters(e.get('host_MQ'),
                                           5672,
                                           '/',
                                           credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=e.get('queue'), durable=True, auto_delete=False)

    channel.basic_publish(exchange='',
                          routing_key=e.get('queue'),
                          body=data_insert)
    connection.close()


def get_dataframe_from_db ():
    name_currency = ['btc', 'ethereum', 'bch', 'miota', 'trueusd']
    data = {}
    max = 10000
    for item in name_currency:
        table_currency = currency.select().with_only_columns([currency.c.cited]).where(currency.c.currency == item)
        db = DB_postgres.con.execute(table_currency)
        list_currency = list_from_db(db)

        data[item] = list_currency
        if len(list_currency) < max:
            max = len(list_currency)

    for k, i in data.items():
        data[k] = data[k][0:max]
    df = pd.DataFrame(data, columns=name_currency)
    df1 = df.mean().sort_values(ascending=False)

    return df1


def get_last_dttm (name_currency):
    cursor = currency.select().with_only_columns([currency.c.dttm]).where(
        currency.c.currency == name_currency).order_by(desc(currency.c.dttm))
    db = DB_postgres.con.execute(cursor)
    for item in db:
        last_dttm = item._row[0]
        break
    return last_dttm


def get_coef_btc (dttm):
    pytrend = TrendReq()

    pytrend.build_payload(kw_list=['bitcoin'], timeframe='today 5-y')
    interest_over_time_df = pytrend.interest_over_time()

    get_d_btc = interest_over_time_df['bitcoin']
    get_currency = interest_over_time_df['bitcoin']
    d_currency = get_currency.to_dict()

    d = get_d_btc.to_dict()
    table_currency = currency.select().with_only_columns([currency.c.dttm, currency.c.cited]).where(
        currency.c.currency == 'bitcoin')
    DB_postgres.con.execute(table_currency)

    for k, n in d.items():
        if dttm >= k and dttm < k + datetime.timedelta(days=7):
            mean_d = (d_currency[k] * 1340) / 100
            return mean_d


def get_last_90days_btc (name_currency, dttm):
    pytrend = TrendReq()
    pytrend.build_payload(kw_list=[name_currency], timeframe='today 3-m')
    interest_over_time_df = pytrend.interest_over_time()

    get_d_btc = interest_over_time_df[name_currency]
    get_currency = interest_over_time_df[name_currency]
    d_currency = get_currency.to_dict()

    d = get_d_btc.to_dict()

    not_cited = get_coef_btc(dttm)
    for k, n in d.items():
        if k >= dttm:
            coef = not_cited / d_currency[k]
            break
    for k, n in d.items():
        if k >= dttm:
            mean_d = d_currency[k] * coef
            DB_postgres.insert(mean_d, name_currency, d_currency[k], k, name_currency)


def get_last_data_btc (name_currency):
    new_data = datetime.datetime.now()
    new_data = datetime.datetime.strptime(
        str(new_data.year) + '-' + str(new_data.month) + '-' + str(new_data.day) + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    old_data = new_data - datetime.timedelta(days=93)
    last_dttm = get_last_dttm('bitcoin')

    if last_dttm < old_data:
        get_cites_dttm_btc(name_currency, last_dttm, old_data)
    else:
        get_last_90days_btc(name_currency, last_dttm)


def get_cites_dttm (name_currency, last_dttm, old_data):
    pytrend = TrendReq()
    on_currency = get_on_currency(name_currency)
    str_date = str(last_dttm.date()) + ' ' + str(old_data.date())
    pytrend.build_payload(kw_list=[on_currency, name_currency], timeframe=str_date)
    interest_over_time_df = pytrend.interest_over_time()

    get_d_btc = interest_over_time_df[on_currency]
    get_currency = interest_over_time_df[name_currency]
    d_currency = get_currency.to_dict()
    d = get_d_btc.to_dict()
    result_db = get_data_from_db(name_currency)
    for k, n in d.items():

        if k >= last_dttm and k <= old_data:
            mean_d = (d_currency[k] * result_db[k]) / d[k]

            DB_postgres.insert(mean_d, name_currency, d_currency[k], k, name_currency)


def get_interest (name_currency, param):
    pytrend = TrendReq()
    on_currency = get_on_currency(name_currency)
    pytrend.build_payload(kw_list=[on_currency, name_currency], timeframe=param)
    interest_over_time_df = pytrend.interest_over_time()
    return interest_over_time_df


def get_update_data (name_currency, dttm):
    on_currency = get_on_currency(name_currency)
    dttm = get_last_dttm(name_currency)

    if dttm.date() == (datetime.datetime.now() - datetime.timedelta(days=1)).date():
        return True
    if datetime.datetime.now() - datetime.timedelta(days=7) > dttm:
        dttm_end = datetime.datetime.now() - datetime.timedelta(days=3)
        dttm_end = datetime.datetime.strptime(
            str(dttm_end.year) + '-' + str(dttm_end.month) + '-' + str(dttm_end.day) + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        get_cites_from_dttm(name_currency, dttm, dttm_end, on_currency)
    interest_over_time_df = get_interest(name_currency, 'now 7-d')

    get_d_btc = interest_over_time_df[on_currency]
    get_currency = interest_over_time_df[name_currency]
    d_currency = get_currency.to_dict()
    d = get_d_btc.to_dict()
    table_currency = currency.select().with_only_columns(
        [currency.c.dttm, currency.c.cited, currency.c.not_cited]).where((currency.c.currency == name_currency) & (
            currency.c.dttm >= dttm)).order_by(desc(currency.c.dttm))
    db = DB_postgres.con.execute(table_currency)

    for item in db:
        dest = item._row
    sum = 0
    count = 0
    coef = 0
    result = []
    dttm_new=dttm+datetime.timedelta(days=1)
    for k, n in d.items():
        if k >= dttm_new and k < dttm_new + datetime.timedelta(days=1) and dttm_new + datetime.timedelta(
                days=1) < datetime.datetime.now():

            sum += d_currency[k]
            count += 1
        else:
            if sum > 0:
                coef = sum / count
                sum = 0
                count = 0
                coef = dest[1] / coef
                break
    dttm_new=dttm+datetime.timedelta(days=1)
    for k, n in d.items():
        temp=[]

        if k >= dttm_new and k < dttm_new + datetime.timedelta(days=1) and dttm_new + datetime.timedelta(
                days=1) < datetime.datetime.now():
            sum += d_currency[k]
            count += 1
        else:
            if sum > 0:
                sum = sum / count
                mean_d = sum * coef
                sum = 0
                count = 0

                result_rb = dict(
                    keyword=name_currency,
                    dttm=str(dttm_new),
                    value=mean_d
                )
                result_rb = json.dumps(result_rb)
                insert_rabbit(result_rb)

                temp.append(d_currency[k])

                temp.append(name_currency)
                temp.append(mean_d)
                temp.append(dttm_new)
                temp.append(on_currency)
                result.append(temp)

                dttm_new = dttm_new + datetime.timedelta(days=1)
        if k.date() == (datetime.datetime.now()).date():
            break

    DB_postgres.insert(result)



def get_7_days (name_currency):
    pytrend = TrendReq()
    on_currency = get_on_currency(name_currency)
    pytrend.build_payload(kw_list=[on_currency, name_currency], timeframe='now 7-d')
    interest_over_time_df = pytrend.interest_over_time()
    old_data = datetime.datetime.now()
    old_data = datetime.datetime.strptime(
        str(old_data.year) + '-' + str(old_data.month) + '-' + str(old_data.day) + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    old_data = old_data - datetime.timedelta(days=3)

    get_d_btc = interest_over_time_df[on_currency]
    get_currency = interest_over_time_df[name_currency]
    d_currency = get_currency.to_dict()
    d = get_d_btc.to_dict()
    table_currency = currency.select().with_only_columns(
        [currency.c.dttm, currency.c.cited, currency.c.not_cited]).where((
                                                                                 currency.c.currency == name_currency) & (
                                                                                     currency.c.dttm >= old_data))
    db = DB_postgres.con.execute(table_currency)

    for item in db:
        dest = item._row
    sum = 0
    count = 0
    coef = 0
    for k, n in d.items():
        if k >= old_data and k < old_data + datetime.timedelta(days=1) and old_data + datetime.timedelta(
                days=1) < datetime.datetime.now():

            sum += d_currency[k]
            count += 1
        else:
            if sum > 0:
                coef = sum / count
                sum = 0
                count = 0
                coef = dest[1] / coef
                break
    old_data = old_data + datetime.timedelta(days=1)
    for k, n in d.items():
        if k.date() == (datetime.datetime.now() - datetime.timedelta(days=1)).date():
            break
        if k >= old_data and k < old_data + datetime.timedelta(days=1) and old_data + datetime.timedelta(
                days=1) < datetime.datetime.now():
            sum += d_currency[k]
            count += 1
        else:
            if sum > 0:
                sum = sum / count
                mean_d = sum * coef
                sum = 0
                count = 0
                DB_postgres.insert(mean_d, name_currency, d_currency[k], k, on_currency)

                old_data = old_data + datetime.timedelta(days=1)


def get_last_90days (name_currency, dttm):
    pytrend = TrendReq()

    on_currency = get_on_currency(name_currency)
    pytrend.build_payload(kw_list=[on_currency, name_currency], timeframe='today 3-m')
    interest_over_time_df = pytrend.interest_over_time()

    get_d_btc = interest_over_time_df[on_currency]
    get_currency = interest_over_time_df[name_currency]
    d_currency = get_currency.to_dict()

    d = get_d_btc.to_dict()
    result_db = get_data_from_db(name_currency)

    for k, n in d.items():
        if k >= dttm:
            coef = result_db[k] / d_currency[k]
            break
    dttm = dttm + datetime.timedelta(days=1)
    for k, n in d.items():
        if k >= dttm:
            mean_d = d_currency[k] * coef
            DB_postgres.insert(mean_d, name_currency, d_currency[k], k, on_currency)


def get_7_days_btc ():
    pytrend = TrendReq()
    pytrend.build_payload(kw_list=['bitcoin'], timeframe='now 7-d')
    interest_over_time_df = pytrend.interest_over_time()
    old_data = datetime.datetime.now()
    old_data = datetime.datetime.strptime(
        str(old_data.year) + '-' + str(old_data.month) + '-' + str(old_data.day) + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    old_data = old_data - datetime.timedelta(days=3)

    get_d_btc = interest_over_time_df['bitcoin']

    d = get_d_btc.to_dict()
    table_currency = currency.select().with_only_columns(
        [currency.c.dttm, currency.c.cited, currency.c.not_cited]).where((
                                                                                 currency.c.currency == 'bitcoin') & (
                                                                                     currency.c.dttm >= old_data))
    db = DB_postgres.con.execute(table_currency)

    for item in db:
        dest = item._row
    sum = 0
    count = 0
    coef = 0
    for k, n in d.items():
        if k >= old_data and k < old_data + datetime.timedelta(days=1) and old_data + datetime.timedelta(
                days=1) < datetime.datetime.now():

            sum += d[k]
            count += 1
        else:
            if sum > 0:
                coef = sum / count
                sum = 0
                count = 0
                coef = dest[1] / coef
                break
    old_data = old_data + datetime.timedelta(days=1)
    result=[]
    for k, n in d.items():
        temp=[]

        if k >= old_data and k < old_data + datetime.timedelta(days=1) and old_data + datetime.timedelta(
                days=1) < datetime.datetime.now():
            sum += d[k]
            count += 1
        else:
            if sum > 0:
                sum = sum / count
                mean_d = sum * coef
                sum = 0
                count = 0
                result_rb = dict(
                    keyword='bitcoin',
                    dttm=str(old_data),
                    value=mean_d
                )
                result_rb = json.dumps(result_rb)
                insert_rabbit(result_rb)
                temp.append(coef)

                temp.append('bitcoin')
                temp.append(mean_d)
                temp.append(old_data)
                temp.append('bitcoin')
                result.append(temp)
                old_data = old_data + datetime.timedelta(days=1)
        if k.date() == (datetime.datetime.now()).date():
            break
    DB_postgres.insert(result)


def get_last_data (name_currency):
    new_data = datetime.datetime.now()
    new_data = datetime.datetime.strptime(
        str(new_data.year) + '-' + str(new_data.month) + '-' + str(new_data.day) + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    old_data = new_data - datetime.timedelta(days=93)
    last_dttm = get_last_dttm(name_currency)

    get_cites_dttm(name_currency, last_dttm, old_data)

    get_last_90days(name_currency, last_dttm)
    get_7_days(name_currency)


def last_date (name_currency):
    cursor = currency.select().with_only_columns([currency.c.dttm]).where(
        (currency.c.currency == name_currency)).order_by(desc(currency.c.dttm))
    db = DB_postgres.con.execute(cursor)
    for item in db:
        dttm = item._row[0]
        return dttm


def start_date (name_currency):
    cursor = currency.select().with_only_columns([currency.c.dttm]).where(
        (currency.c.currency == name_currency)).order_by(currency.c.dttm)
    db = DB_postgres.con.execute(cursor)
    for item in db:
        dttm = item._row[0]
        return dttm


def list_from_db (db):
    result = []
    for item in db:
        result.append(item._row[0])
    return result


def check_currency (name_currency):
    table_currency = currency.select().with_only_columns([currency.c.dttm, currency.c.cited]).where(
        currency.c.currency == name_currency)
    db = DB_postgres.con.execute(table_currency)
    if db.rowcount > 0:
        return True
    else:
        return False


def get_all_history (name_currency):
    get_cites(name_currency)
    get_last_data(name_currency)
