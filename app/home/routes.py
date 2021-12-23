# -*- encoding: utf-8 -*-
import os
import json
from app.home import blueprint
from flask import render_template, redirect, url_for, Response, request, flash, jsonify
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from flask import send_from_directory
import cv2
from app.base.models import SenserData
import xlsxwriter
import io
#######################传感器数据实时更新代码片段################################

from app import socketio, mqtt
from run import add_senserdata

import threading
topic = "IoT/gateway"

online_flag = False

@socketio.on('publish')
def handle_publish(json_str):
    data = json.loads(json_str)
    mqtt.publish(data['topic'], data['message'])


@socketio.on('subscribe')
def handle_subscribe(json_str):
    data = json.loads(json_str)
    mqtt.subscribe(data['topic'])


@socketio.on('unsubscribe_all')
def handle_unsubscribe_all():
    mqtt.unsubscribe_all()


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe(topic)


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    recv = json.loads(message.payload.decode())
    params = recv['params']
    ts = recv['ts'] // 1000
    res = {**{'time':ts}, **params}
    res['humidity'] /= 10
    res['temp'] /= 10
    res['windSpeed'] /=100
    #print('res:',res)
    socketio.emit('mqtt_message', data=res)
    t = threading.Thread(target=add_senserdata, args=(res,))
    t.start()


@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    print(level, buf)

######################################传感器数据展示################################################
@blueprint.route('/sensorData', methods=['GET','POST'], strict_slashes=False)
def sensorData():

    return render_template('sensor-data.html')


@blueprint.route('/init_sensorData', methods=['GET','POST'], strict_slashes=False)
def init_sensorData():
    res = SenserData.query.all()[-1]
    res = res.to_json()
    return res


@blueprint.route('/query_sensorData', methods=['GET','POST'], strict_slashes=False)
def query_sensorData():
    time_dict = {'1h':1,'2h':2,'3h':3,'6h':6,'12h':12,'24h':24,'2 days ago':48, '7 days ago':168,'14 days ago':336,'30 days ago':720,}
    print(request.get_data())
    print(json.loads(request.get_data(as_text=True)))
    request_data = json.loads(request.get_data(as_text=True))
    request_time = request_data["time"]
    if request_time:
        time_interval = time_dict[request_time]
    else:
        time_interval = time_dict["6h"]
    query_time = time.time() - time_interval * 60 * 60
    sensordatas = SenserData.query.filter(SenserData.time >= query_time).all()
    sensordatas_json = []
    for sensordata in sensordatas:
        sensordatas_json.append(sensordata.to_json())
    print(len(sensordatas_json))

    return jsonify({"sensordatas": json.dumps(sensordatas_json), "datalength": len(sensordatas)})



@blueprint.route('/download_sensorData/<request_time>')
def download_sensorData(request_time):

    filename = "{}.xlsx".format(time.time())
    time_dict = {'1h': 1, '2h': 2, '3h': 3, '6h': 6, '12h': 12, '24h': 24, '2 days ago': 48, '7 days ago': 168,
                 '14 days ago': 336, '30 days ago': 720, }


    print(request_time)
    if request_time:
        time_interval = time_dict[request_time]
    else:
        time_interval = time_dict["6h"]
    query_time = time.time() - time_interval * 60 * 60
    sensordatas = SenserData.query.filter(SenserData.time >= query_time).all()
    print(sensordatas)
    # sensordatas_json = []
    # for sensordata in sensordatas:
    #     sensordatas_json.append(sensordata.to_json())

    fp = io.BytesIO()
    book = xlsxwriter.Workbook(filename)
    worksheet = book.add_worksheet('hitory_data')
    # 生成表头
    header_list = ["时间戳(Second)","湿度", "温度","风速","风向"]
    for col,header in enumerate(header_list):
        worksheet.write(0,col,header)

    # 生成数据
    sensordata_tuple = []
    for sensordata in sensordatas:
        sensordata_tuple.append(sensordata.to_tuple())
    for row_number, row_tuple in enumerate(sensordata_tuple):
        for col, per_student_info in enumerate(row_tuple):
            worksheet.write(row_number+1, col, per_student_info)

    book.close()
    fp.seek(0)
    directory = os.getcwd()
    print(directory)
    return send_from_directory(directory,filename, as_attachment=True)



#####################此处是首页的路由函数#################################
@blueprint.route('/index')
@login_required
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('base_blueprint.login'))
    return render_template('index.html')


import time
import queue
#######################实时监控代码片段#################################
q = queue.Queue()
def  reveive_frames():
    # camera1 = cv2.VideoCapture("rtsp://admin:qwer1234@192.168.1.64/Streaming/Channels/2")
    # print("This is video_url",video_url)
    camera1 = cv2.VideoCapture("rtsp://admin:qwer1234@192.168.1.64/Streaming/Channels/2")
    ret, frame = camera1.read()
    q.put(frame)
    while ret:
        ret, frame = camera1.read()
        if not ret or frame is None:
            #print('video is all read')
            continue
        if q.qsize()<10:
            q.put(frame)

def gen_frames():
    while True:
        if q.empty() != True:
            # print("Queue size is:",q.qsize())
            frame = q.get()
            success, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# camera1 = cv2.VideoCapture("rtsp://admin:qwer1234@192.168.1.64/Streaming/Channels/2")
# def gen_frames():
#     while True:
#         ret, frame = camera1.read()
#         if not ret:
#             break
#         else:
#             success, buffer = cv2.imencode('.jpg',frame)
#             frame = buffer.tobytes()
#
#             yield (b'--frame\r\n'
#                     b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

@blueprint.route('/live_camera')
def live_camera():
    p1 = threading.Thread(target=reveive_frames)
    p1.start()
    return Response(gen_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame')



@blueprint.route('/<template>')
def route_template(template):

    if not current_user.is_authenticated:
        return redirect(url_for('base_blueprint.login'))

    try:

        return render_template(template + '.html')

    except TemplateNotFound:
        return render_template('page-404.html'), 404
    
    except:
        return render_template('page-500.html'), 500
