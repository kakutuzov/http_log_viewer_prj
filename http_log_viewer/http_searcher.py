from pymongo import Connection
from pymongo import *
from bson.objectid import ObjectId
import ast
import logging
from datetime import date, time, datetime, timedelta
import sys

def get_connection():
    c = Connection('mongodb://192.168.0.158:27017,192.168.0.159:27017/?slaveOk=true;replicaSet=ati_log')
    # c = Connection('mongodb://192.168.222.40:27017')
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
