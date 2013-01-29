from pymongo import Connection
from pymongo import *
from bson.objectid import ObjectId
import ast
import logging
from datetime import date, time, datetime, timedelta
import pymongo
import sys


FIELD_IP = "cIP"
FIELD_START = "tB"
FIELD_ID = "_id"
FIELD_TIME = 'tT'
FIELD_QS = 'cQS'
FIELD_URL = "cURL"
FIELD_SERVER = "sIP"
FIELD_USERNAME = 'cU'

CONNECTION = "mongodb://192.168.0.158:27017/?slaveOk=true"


def get_connection():
    c = Connection(CONNECTION)
    #c = Connection('mongodb://192.168.222.40:27017')
    #c = Connection()
    return c

def get_db_names():
    c = get_connection()
    return sorted(filter(lambda name: 'ati_log_20' in name, c.database_names()))


def get_db(db_date):
    c = get_connection()
    db_name = 'ati_log_%s' % db_date
    db = c[db_name]
    if db and db.name in get_db_names():
        return db
    else:
        return None


def get_latest_db():
    c = get_connection()
    db_names = sorted(filter(\
        lambda db_name: db_name.startswith('ati_log_'),c.database_names()),\
                          reverse=True)
    latest_db_name = db_names[0] if db_names else None
    return c[latest_db_name]

def get_top_requests(mins, top):
    db = get_latest_db()
    r_groups = []
    count = 0
    db_name = 'Undefined'
    if db and db.requests and db.requests.count() > 0:
        #fields = [FIELD_IP, FIELD_START, FIELD_TIME, FIELD_URL, \
                      #FIELD_QS, FIELD_SERVER, FIELD_USERNAME]
        fields = [FIELD_IP, FIELD_START]
        print(datetime.now())
        print("find starts: {0}".format(datetime.now()))
        requests = db.requests.find(limit=1000000,\
                                        fields = fields, \
                                        sort=[(FIELD_ID,pymongo.DESCENDING)])
        time_start = requests[0][FIELD_START]
        print("find ends: {0}".format(datetime.now()))
        time_finish = time_start - timedelta(seconds=mins*60)
        print("time stop: {0}".format(time_finish))      # remove line debug only
        r_by_ip = {}
        for r in requests:
            #print(r[FIELD_START]) # remove
            if not r[FIELD_START] or r[FIELD_START] < time_finish:
                break
            else:
                count += 1
                ip = r[FIELD_IP]
                if ip not in r_by_ip:
                    r_by_ip[ip] = [str(r[FIELD_ID])]
                else:
                    r_by_ip[ip].append(str(r[FIELD_ID]))
        print("sorted start: {0}".format(datetime.now()))
        r_groups = sorted(\
            r_by_ip.items(), key = lambda (k,v):len(v), reverse=True)[:top]
        print("sorted finish: {0}".format(datetime.now()))
    return (r_groups, db_name, count)

def get_requests_by_ids(ids = []):
    db = get_latest_db()
    requests = []
    if db and db.requests:
        fields = [FIELD_IP, FIELD_START, FIELD_TIME, FIELD_URL, \
                      FIELD_QS, FIELD_SERVER, FIELD_USERNAME]
        query = {FIELD_ID : {'$in':[ObjectId(id) for id in ids]}}
        requests = db.requests.find(query, fields= fields, limit = 1000)
    return requests

def search_by_params(cURL = '',  cU = '', cIP= '', cQS = '', \
        db_date = '', tE_min = None, \
        tE_max = None, skip = 0, limit = 10):

    c = get_connection()
    print(db_date)
    db = get_db(db_date = db_date)
    if db:
        collection = db.requests

        query = {}

        # query by user
        if cU and cU.strip():
            query['cU'] = cU

        # query by ip
        if cIP and cIP.strip():
            query['cIP'] = cIP

        # query by url
        if cURL and cURL.strip():
            query['cURL'] = cURL

        # datetime

        date = datetime.strptime(db_date, "%Y_%m_%d")

        #query by time - lower bound
        if tE_min:
            date_min = datetime.combine(date, \
                time(hour=tE_min.hour, minute=tE_min.minute))
            query['tE'] = {'$gt':date_min}

        #query by time - upper bound
        print(tE_max)
        if tE_max:
            date_max = datetime.combine(date, \
                time(hour=tE_max.hour, minute=tE_max.minute))
            query['tE'] = {'$lt':date_max}

        print (query)

        return collection.find(query).skip(skip).limit(limit).sort("tE",\
            ASCENDING)
    else:
        db_name = 'tmp'
        return c[db_name].requests.find()

def search_by_id(db_date, row_id):
    db = get_db(db_date)
    if db:
        return db.requests.find_one(ObjectId(row_id))

def search_by_query(collection, query):
    if query and len(query) > 0 and '' not in query.values():
        return collection.find(query, fields={'_id':1})
    else:
        return None

# divide and conquer algorithm
def search_by_params_dc(cURL = '',  cU = '', cIP= '', cQS = '', \
        date = date.today() - timedelta(days=1), tE_min = None, \
        tE_max = None, skip = 0, limit = 10):

    db = get_db(date = date)
    collection = db.requests
    queries = [collection.find(fields={'_id':1})]

    # find by user
    queries.append(search_by_query(collection, {'cU':cU}))

    # find by ip
    queries.append(search_by_query(collection, {'cIP':cIP}))

    # find by url
    queries.append(search_by_query(collection, {'cURL':cURL}))

    #find by time - lower bound
    if tE_min: 
        date_min = datetime.combine(date, \
            time(hour=tE_min.hour, minute=tE_min.minute))
        queries.append(search_by_query({'tE':{'$gt':date_min}}))

    #find by time - upper bound
    if tE_max:
        date_max = datetime.combine(date, \
            time(hour=tE_max.hour, minute=tE_max.minute))
        queries.append(search_by_query({'tE':{'$lt':date_max}}))

    # if cU and cU.strip(): query['cU'] = {'$regex': "^{0}$".format(cU)};
    # if cQS and cQS.strip(): query['cQS'] = {'$regex':cQS}
    # return db.requests.find(query).skip(skip).limit(limit).sort("tE", pymongo.ASCENDING)

    # return search_by_queries(collection, queries, skip = skip, limit = limit)

    return db.requests.find(query).skip(skip).limit(limit).sort("tE", \
        pymongo.ASCENDING)

def search_by_queries(collection, queries, skip, limit):
    sorted_by_count = sorted(queries, \
        key= lambda query: query.count() if query else sys.maxint)
    # min_count = sorted_by_count[0]
    i = 0
    result = []
    for row in sorted_by_count[0]:
        i += 1
        if i <= skip:
            pass
        else:
            if i > limit:
                break
            else:
                result.append(collection.find_one(row['_id']))
    return result
    # print(sorted_by_count)

# def search(query_string, skip = 0, count = 10):
#     c = Connection('mongodb://127.0.0.1')
#     db = c['ati_log']
#     # app.logger.debug(query_string)
#     # query_string = query_string if query_string else ""
#     query = ast.literal_eval(query_string if query_string else "{}")
#     return db.requests.find(query).skip(skip).limit(count)


if __name__ == '__main__':
    result = search_by_params(cURL='', cIP='192.168.0.3')
    result.count()
    for row in result[:]:
        print(row['cIP'], row['cU'], row['cURL'])