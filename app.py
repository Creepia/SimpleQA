from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from random import randint
import json,time

app = Flask(__name__)
socketio = SocketIO(app)
Rooms = {
    "000000":{
        "master":"123.123.123.123",
        "players":{
            "123.222.0.1":"Alice",
            "20.151.8.1":"Bob",
            "123.31.4.5":"Charlie"
            },
        "questions":[
            {
                "type": "SMC",
                "question": "What is the capital of France?",
                "options": ["Paris", "London", "Rome", "Madrid"],
                "answer": "A"
            },
        ],
        "status":-1
    }
}

'''# 处理客户端点击 NEXT 按钮的事件
@socketio.on('next_question')
def next_question(data):
    room_id = data['room_id']
    # 在此处处理进入下一题的逻辑
    # 更新题目信息，开始新一轮的计时

# 处理客户端回答问题的事件
@socketio.on('answer_question')
def answer_question(data):
    room_id = data['room_id']
    question_number = data['question_number']
    # 在此处处理客户端回答问题的逻辑
    # 计算玩家得分等操作'''

# 这个函数用于启动计时器
def start_timer():
    time_remaining = 15
    while time_remaining > 0:
        time.sleep(1)
        time_remaining -= 1
        socketio.emit('timer_update', {'time': time_remaining}, broadcast=True)

@app.route('/lobby.html')
def lobby():
    return render_template('lobby.html', Rooms=Rooms)

@app.route('/')
def index():
    user_ip = request.remote_addr
    return render_template('index.html',user_ip=user_ip)

@app.route('/RoomCreate.html')
def room_create():
    return render_template('RoomCreate.html')

@app.route('/QuestionShow.html')
def qsn_start_game():
    room_id=request.args.get("room_id")
    if(room_id in Rooms):
        number_of_questions=len(Rooms[room_id]["questions"])
        # 展示第一个问题时，status==0
        if(Rooms[room_id]["status"]<number_of_questions-1):
           Rooms[room_id]["status"]+=1
           qtn_order=Rooms[room_id]["status"]
           if(Rooms[room_id]["questions"][qtn_order]["type"]=="SMC"):
                qtn=Rooms[room_id]["questions"][qtn_order]["question"]
                opt=Rooms[room_id]["questions"][qtn_order]["options"]
                ans=Rooms[room_id]["questions"][qtn_order]["answer"]
                
        return render_template('QuestionShow.html',qtn_order=qtn_order,qtn=qtn,opt=opt,ans=ans)
    else:
        return render_template('QuestionShow.html')

@app.route('/AnswerShow.html')
def ans_start_game():
    room_id=request.args.get("room_id")
    if(room_id in Rooms):
        # 展示第一个问题时，status==0
        qtn_order=Rooms[room_id]["status"]
        if(Rooms[room_id]["questions"][qtn_order]["type"]=="SMC"):
            qtn=Rooms[room_id]["questions"][qtn_order]["question"]
            opt=Rooms[room_id]["questions"][qtn_order]["options"]
            ans=Rooms[room_id]["questions"][qtn_order]["answer"]
        return render_template('AnswerShow.html',qtn_order=qtn_order,qtn=qtn,opt=opt,ans=ans)
    else:
        return render_template('AnswerShow.html')

@app.route('/Rank.html')
def simple_rank():
    room_id=request.args.get("room_id")
    if(Rooms[room_id]["status"]<len(Rooms[room_id]["questions"])-1):
        return render_template('SimpleRank.html',room_id=room_id)
    else:
        return render_template('FinalRank.html',room_id=room_id)

@app.route('/RoomJoin.html')
def room_join():
    return render_template('RoomJoin.html')

@app.route('/Prestart.html')
def prestart():
    return render_template('Prestart.html')

'''@app.route('/FinalRank.html')
def final_rank():
    room_id=request.args.get("room_id")
    return render_template('FinalRank.html',room_id=room_id)'''


@app.route('/PreAnswer.html')
def preanswer():
    return render_template('PreAnswer.html')


@app.route('/check_room_status/<string:room_id>', methods=['GET'])
def check_room_status(room_id):
    if room_id in Rooms:
        room_status = Rooms[room_id]['status']
        return jsonify({'status': room_status})
    else:
        return jsonify({'status': -1})  # 返回-1表示房间不存在


@app.route('/process_json', methods=['POST'])
def process_json():
    # 取得房间id
    room_id = request.form['room_id']
    Rooms[room_id]={"status":-1,"players":{},"questions":[]}
    # print(f"Added new room {room_id}")
    
    # 取得问题集json
    print("start process_json")
    qtn_file = request.files['file']
    if qtn_file and qtn_file.filename.endswith('.json'):
        try:
            data = json.load(qtn_file)
            print(data)
            # 在这里对 JSON 数据进行处理
            Rooms[room_id]["questions"]=data
            return jsonify({'success': True})
        except Exception as e:
            error_message = str(e)
    else:
        error_message = 'Invalid file format. Please upload a .json file.'
    
    return jsonify({'success': False, 'error': error_message})

@app.route('/check_room',methods=['POST'])
def checkRoomExist():
    data = request.get_json()
    room_id = data.get('room_id')
    if room_id in Rooms:
        user_name = data.get('name')
        if(user_name !=""):
            # 进入回答第一个问题，加入玩家
            user_ip = request.remote_addr
            Rooms[room_id]["players"][user_ip]=user_name
            return jsonify({'room_exists': True,'isReady':True})
        else:
            return jsonify({'room_exists': True,'isReady':False})
    else:
        return jsonify({'room_exists': False})





if __name__ == '__main__':
    # app.run(host='0.0.0.0',debug=1)
    socketio.run(app, host='0.0.0.0', port=5000,debug=1)
