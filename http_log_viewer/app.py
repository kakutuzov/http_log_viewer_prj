from flask import Flask, render_template, request, jsonify
import http_searcher as s
from datetime import datetime, date, timedelta
import logging

app = Flask(__name__)

@app.route('/', methods = ['GET'])
def index():
    query_path = request.args.get("path") 
    query_username = request.args.get("username")
    query_ip = request.args.get("ip")
    query_qs = request.args.get("qs")
    query_date = request.args.get("date")
    query_time_from = request.args.get("time_f")
    query_time_to = request.args.get("time_to")
    time_from = None
    try:
        time_from = datetime.strptime(query_time_from, '%H:%M')
    except Exception, e:
        # time_from = N
        logging.debug(e)

    query_time_from = request.args.get("time_to")
    time_to = None
    try:
        time_to = datetime.strptime(query_time_to, '%H:%M')
    except Exception, e:
        # time_to = N
        logging.debug(e)
    
    skip = int(request.args.get("skip") if request.args.get("skip") else 0)
    rpp = int(request.args.get("rpp") if request.args.get("rpp") else 10)
    requests = s.search_by_params(cURL = query_path, cU = query_username, \
        cIP=query_ip, cQS=query_qs, \
        db_date = query_date, \
        tE_min = time_from, tE_max = time_to, \
        skip=skip, limit=rpp)
    return render_template('index.html', requests = requests, \
        skip = skip, rpp = rpp, dates = \
        [db_name.strip('ati_log_') for db_name in [''] + s.get_db_names()])

# @app.route('/_get_more_rows', methods = ['GET'])
# def get_more_rows(): + 
#     return jsonify(result = s.search(q))
# # def get_more_rows(guid, q, skip, count):
#     # s.search(q)

@app.route('/_get_more_info', methods = ['GET'])
def get_more_info():
    db_date = request.args.get('db_date')
    row_id = request.args.get('row_id')
    # print(db_date, row_id)
    row = s.search_by_id(db_date, row_id)
    fields = {'client&nbsp;ip':row['cIP'], \
        'server&nbsp;ip':row['sIP'], \
        'start&nbsp;time': str(row['tB']), \
        'end&nbsp;time': str(row['tE']), \
        'cookie': row['cC'], \
        'waiting&nbsp;time': "%s msec" % row['tT'], \
        'verb': row['cM'], \
	'code' : row['scS'], \
        'post': row['cPOST'] if row['cM'] in ['post', 'put'] else ''
        }
    return jsonify(request = \
        "<table class='mi-info table-condensed'><tbody> %s </tbody></table>" % \
        ''.join(['<tr><td class="mi-field-name"><b>%s</b></td> \
            <td class="mi-field-value">%s</td></tr>' \
            % (key, value) for (key, value) in fields.items()]))

if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0')
    # app.run('127.0.0.1')
