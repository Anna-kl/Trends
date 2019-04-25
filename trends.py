

import datetime
import function_trends
import sys

# load all currency
def get_all_currency ():
    name_currency = function_trends.get_currency_name()

    for item in name_currency:

      try:
        if item['source_id'].lower().replace('$', '').replace('#', '') == item['symbol'].lower().replace('$',
                                                                                                         '').replace(
                '#', '') == False:
            if function_trends.check_currency(item['symbol'].lower().replace('$', '').replace('#', '')):
                dttm_history(item['symbol'].lower().replace('$', '').replace('#', ''))
        else:
            if function_trends.check_currency(item['symbol'].lower().replace('$', '').replace('#', '')) == False:
                dttm_history(item['symbol'].lower().replace('$', '').replace('#', ''))
            if function_trends.check_currency(item['source_id'].lower().replace('$', '').replace('#', '')) == False:
                dttm_history(item['source_id'].lower().replace('$', '').replace('#', ''))
      except:
          continue

def get_currency(name_currency):
    dttm=function_trends.get_last_data(name_currency)
    if dttm<datetime.datetime.now()-datetime.timedelta(days=93):
        function_trends.get_cites_from_dttm(name_currency,dttm)
        dttm=function_trends.get_last_data(name_currency)
        function_trends.get_last_90days(name_currency,dttm)
        function_trends.get_7_days(name_currency)
    elif dttm<datetime.datetime.now()-datetime.timedelta(days=7):
        function_trends.get_last_90days(name_currency, dttm)
        function_trends.get_7_days(name_currency)
    else:
        function_trends.get_7_days(name_currency)


# update all currency
def update():
    dttm=datetime.datetime.now().date()
    dttm=datetime.datetime.strptime(str(dttm.year)+'-'+str(dttm.month)+'-'+str(dttm.day)+' 00:00:00','%Y-%m-%d %H:%M:%S')

    currency_all=function_trends.get_currency_name()
    for item in currency_all:
       try:
        if item['source_id'].lower() == item['symbol'].lower():
            if function_trends.check_currency(item['symbol'].lower()):
                function_trends.get_update_data(item['symbol'].lower(),dttm)
        else:
            if function_trends.check_currency(item['symbol'].lower()):
                function_trends.get_update_data(item['symbol'].lower(),dttm)
            if function_trends.check_currency(item['source_id'].lower()):
                function_trends.get_update_data(item['source_id'].lower(),dttm)
       except Exception as e:
           print('error')
           continue


#Первый запуск программы, сначала загружается Bitcoin
def first_run():
    new_data = datetime.datetime.strptime('2017-12-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    new_data=function_trends.get_last_dttm('bitcoin')
    # dttm_end = new_data-datetime.timedelta(days=60)
    # function_trends.get_btc('bitcoin', new_data, dttm_end)
    # new_data = dttm_end
    date_end = new_data - datetime.timedelta(days=60)
    dttm_end = datetime.datetime.strptime('2017-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    while (date_end >= dttm_end):
        function_trends.get_btc_coef('bitcoin',  date_end,new_data)
        dttm_start = date_end
        date_end = dttm_start - datetime.timedelta(days=60)
    date_end = dttm_end
    function_trends.get_btc_coef('bitcoin', new_data, date_end)




# first_run()
# new_data = function_trends.start_date('bitcoin')
# ##new_data = datetime.datetime.strptime('2017-12-01 00:00:00', '%Y-%m-%d %H:%M:%S')
# dttm_end=datetime.datetime.strptime('2019-03-14 00:00:00', '%Y-%m-%d %H:%M:%S')
# dttm_start=function_trends.get_last_dttm('bitcoin')
# date_end = dttm_start + datetime.timedelta(days=60)
# while(date_end<=dttm_end):
#
#         function_trends.get_btc_coef('bitcoin',date_end,new_data)
#         new_data=date_end
#         date_end = new_data - datetime.timedelta(days=60)
# date_end=dttm_end
# function_trends.get_btc_coef('bitcoin',dttm_start,dttm_end)





def dttm_history(name_currency):
    item_currency=function_trends.find_currency(name_currency)
    dttm_start = datetime.datetime.strptime('2017-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    dttm_end = datetime.datetime.strptime('2019-02-13 00:00:00', '%Y-%m-%d %H:%M:%S')
    date_end=dttm_start+datetime.timedelta(days=60)
    while(date_end<=dttm_end):

        item_currency=function_trends.get_cites_from_dttm(name_currency,dttm_start,date_end,item_currency)
        dttm_start=date_end
        date_end = dttm_start + datetime.timedelta(days=60)
    date_end=dttm_end
    function_trends.get_cites_from_dttm(name_currency, dttm_start, date_end,item_currency)


if __name__ == "__main__":
    if sys.argv[1]=='all':
        get_all_currency()
        print('all currency load')
    elif sys.argv[1]=='update':
        new_data = function_trends.last_date('bitcoin')
        dttm_end = datetime.datetime.now() - datetime.timedelta(days=3)

        if new_data < dttm_end:
            function_trends.get_btc_coef('bitcoin', new_data, dttm_end)
            function_trends.get_7_days_btc()
        elif new_data.date() < (datetime.datetime.now() - datetime.timedelta(days=1)).date():

            function_trends.get_7_days_btc()

        update()


# new_data = function_trends.last_date('bitcoin')
# dttm_end = datetime.datetime.now()-datetime.timedelta(days=3)
#
# if new_data<dttm_end:
#     function_trends.get_btc_coef('bitcoin',new_data,dttm_end)
#     function_trends.get_7_days_btc()
# elif new_data.date()<(datetime.datetime.now()-datetime.timedelta(days=1)).date():
#
#     function_trends.get_7_days_btc()
# update()
# print('complete')
