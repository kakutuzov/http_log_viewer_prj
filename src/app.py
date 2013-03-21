#!/usr/bin/python
# -*- encoding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, redirect, url_for
import http_searcher as s
from datetime import datetime, date, timedelta
import logging

app = Flask(__name__)

@app.route('/', methods = ['GET'])
def defualt():
    return "http log viewer"

@app.route('/log', methods = ['GET'])
def log():
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


@app.route("/log/top/ajax_requests_by_ids", methods=['POST'])
def ajax_requests_by_ids():
    print("ajax_requests_by_ids start")
    print(request.data)
    print(request.json)
    print(request.method)
    print([x for x in request.form])
    ids = request.form.get('ids')
    requests = s.get_requests_by_ids(ids.split(','))
    table_html = """<blockquote><table class='table'><thead>
		  <tr>
		    <th>Login</th>
		    <th>Server</th>
		    <th>Time(UTC)</th>
                    <th>Method</th>
                    <th>Status</th>
                    <th>UserAgent</th>
		    <th>URL</th>
		    <th>QS</th>
		  </tr>
		</thead><tbody> %s </tbody></table></blockquote>"""
    tr_html = """<tr>
		    <td>%s</td>
		    <td>%s:%s</td>
		    <td class="tr-result-ip-time">%s</td>
                    <td>%s</td>
                    <td>%s</td>
		    <td>%s</td>
		    <td>%s</td>
		    <td><div class="tr-result-ip-qs">%s</div></td>
		  </tr>"""
    json = jsonify(html = table_html % \
                       ''.join([ tr_html % \
                                   (r[s.FIELD_USERNAME], \
                                        r[s.FIELD_SERVER], \
                                        r[s.FIELD_SERVER_PORT], \
                                        r[s.FIELD_START], \
                                        r[s.FIELD_END], \
                                        (r[s.FIELD_METHOD] or '').upper(), \
                                        r[s.FIELD_STATUS], \
                                        r[s.FIELD_USERAGENT], \
                                        r[s.FIELD_URL], \
                                        r[s.FIELD_QS]) for r in requests]))
    print("ajax_requests_by_ids finish")
    return json


@app.route("/top_log")
def top_log():
    return redirect(url_for('log_top'))

@app.route("/log/top")
def log_top():
    mins = int(request.args.get('mins') or 5)
    top = int(request.args.get('top') or 50)
    print("mins = %s, top = %s" % (mins , top))
    (requests_groups, db_name, requests_count) = s.get_top_requests(mins, top)
    print(len(requests_groups))
    return render_template('log_top.html', \
                               requests_groups = requests_groups, \
                               db_name = db_name, \
                               requests_count = requests_count, \
                               mins = mins, \
                               top = top)


@app.route("/log/search/url")
def log_search_url():
    print("log_search_url starts: %s" % (datetime.now()))
    secs = int(request.args.get('secs') or 5)
    url = request.args.get('url') or 'txt='
    print("secs=%s, url=%s" % (secs, url))
    (requests, db_name, count_processed) = s.search_by_url(secs, url)
    return render_template('log_search_url.html', \
                           requests = requests, \
                           secs = secs, \
                           url = url, \
                           count = count_processed)
    
#app.debug = True


if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0')
    # app.run('127.0.0.1')
