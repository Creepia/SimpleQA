from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit,send,join_room,leave_room
from random import randint
import json,time

app = Flask(__name__)
socketio = SocketIO(app)
Rooms = {
    "000000":{
        "master":"123.123.123.123",
        "players":[
            { "name": 'Alex', "ip": '123.4.56.78' ,"score":10},
            { "name": 'Bob', "ip": '100.2.88.9' ,"score":20},
            { "name": 'Carol', "ip": '102.0.231.114',"score":30 }
        ],
        "questions":[
            {
                "type": "SMC",
                "question": "What is the capital of France?",
                "options": ["Paris", "London", "Rome", "Madrid"],
                "answer": "A"
            },
        ],
        "status":-1,
        "timer":0
    }
}

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

@app.route('/ScoreShow.html')
def score_show():
    room_id=request.args.get("room_id")
    user_ip = request.remote_addr
    i=0
    for player in Rooms[room_id]["players"]:
        if(player["ip"]==user_ip):
            name=player["name"]
            score=player["score"]
            rank=i
            break
        i+=1
    # 如果还没完成最后一题，则玩家方跳转到SimpleScoreShow.html；如果已经完成最后一题，则玩家方跳转到FinalScoreShow.html
    if(Rooms[room_id]["status"]<len(Rooms[room_id]["questions"])-1):
        return render_template('SimpleScoreShow.html',qtn_order=Rooms[room_id]["status"],name=name,score=score)
    else:
        return render_template('FinalScoreShow.html',qtn_order=Rooms[room_id]["status"],name=name,score=score,rank=rank+1)

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
def to_rank():
    room_id=request.args.get("room_id")
    # 如果还没完成最后一题，则房主方跳转到SimpleRank.html；如果已经完成最后一题，则房主方跳转到FinalRank.html
    if(Rooms[room_id]["status"]<len(Rooms[room_id]["questions"])-1):
        return render_template('SimpleRank.html',room_id=room_id,qtn_order=Rooms[room_id]["status"])
    else:
        return render_template('FinalRank.html',room_id=room_id)

@app.route('/RoomJoin.html')
def room_join():
    return render_template('RoomJoin.html')

@app.route('/Prestart.html')
def prestart():
    return render_template('Prestart.html')

@app.route('/PreAnswer.html')
def preanswer():
    return render_template('PreAnswer.html')

@socketio.on("checkRoomStatus")
def checkRoomStatus(room_id):
    if room_id in Rooms:
        room_status = Rooms[room_id]['status']
        return room_status
    else:
        # 返回-2表示房间不存在
        return -2
    
@socketio.on("checkPlayersData")
def checkPlayers(room_id):
    if room_id in Rooms:
        players = Rooms[room_id]['players']
        return players
    else:
        # 返回-2表示房间不存在
        return -2

@socketio.on("checkRankPlayers")
def checkRankPlayers(room_id):
    # 将改房间的玩家list按分数大到小排序
    Rooms[room_id]["players"].sort(key=lambda player:player["score"],reverse=True)
    top3_players_data={
        "p1_name":"","p1_score":0,
        "p2_name":"","p2_score":0,
        "p3_name":"","p3_score":0
    }
    for i in range(1,4):
        try:
            top3_players_data[f"p{i}_name"]=Rooms[room_id]["players"][i-1]["name"]
            top3_players_data[f"p{i}_score"]=Rooms[room_id]["players"][i-1]["score"]
        except:
            break
    print(top3_players_data)
    return top3_players_data

@socketio.on("checkRoomExists")
def checkRoomExists(data):
    room_id = data["room_id"]
    if room_id in Rooms:
        user_name = data["name"]
        print(user_name)
        if(user_name !=""):
            # 进入回答第一个问题，加入玩家
            user_ip = request.remote_addr
            Rooms[room_id]["players"].append({"ip":user_ip,"name":user_name,"score":0})
            return {'room_exists': True,'isReady':True}
        else:
            return {'room_exists': True,'isReady':False}
    else:
        return {'room_exists': False}

@socketio.on("removePlayer")
def removePlayer(data):
    room_id=data["room_id"]
    ip=data["ip"]
    print(ip)
    for p in Rooms[room_id]["players"]:
        if(p["ip"]==ip):
            Rooms[room_id]["players"].remove(p)
            break

@socketio.on("newQuestion")
def newQuestion(room_id):
    start_time=time.time()
    print(start_time)
    Rooms[room_id]["timer"]=start_time

@socketio.on("getSecondsLeft")
def getSecondsLeft(data):
    room_id=data["room_id"]
    current_time=time.time()
    left_seconds=int(Rooms[room_id]["timer"]+15-current_time)
    if(left_seconds>0):
        return left_seconds
    else:
        return 0

@socketio.on("toNextQuestion")
def toNextQuestion(room_id):
    socketio.emit("toNextQuestion_res")

@socketio.on('process_newroom')
def process_newroom(data):
    # 取得房间id
    # print("start process_newroom")
    room_id=data["room_id"]
    Rooms[room_id]={"status":-1,"players":[],"questions":[]}
    # 取得问题集json
    # print("start process_json")
    qtn_file = data['file']
    try:
        data = json.loads(qtn_file)
        # print(data)
        # 在这里对 JSON 数据进行处理
        Rooms[room_id]["questions"]=data
        # print(request.sid)
        join_room(room_id)
        return {'sucess': True}
    except Exception as e:
        # 客户端状态回传（待优化）
        return {'sucess': False,'error_msg':str(e)}

@socketio.on("refreshRoomDataShow")
def refreshRoomDataShow(data):
    return Rooms

@socketio.on("checkAnswerIfCorrect")
def checkAnswerIfCorrect(data):
    answer=data["chosen_answer"]
    room_id=data["room_id"]
    print(answer)
    print(room_id)
    qtn_order=Rooms[room_id]["status"]
    real_ans=Rooms[room_id]["questions"][qtn_order]["answer"]
    if(real_ans==answer):
        user_ip = request.remote_addr
        for player in Rooms[room_id]["players"]:
            if(player["ip"]==user_ip):
                player["score"]+=10
                break
    return(real_ans)

if __name__ == '__main__':
    # app.run(host='0.0.0.0',debug=1)
    # socketio.run(app, host='0.0.0.0', port=5000,debug=1)
    socketio.run(app,debug=1)
