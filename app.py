from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room
from package import *
import time

app = Flask(__name__)
app.config["SECRET_KEY"] = "korekoso_himituda"
socketio = SocketIO(app)

# 房间"000000"为测试房间
Rooms = {"000000": Room("000000")}
Rooms["000000"].setQuestionsFromJson('''
[
  {
    "showncode":"uno",
    "type": "SMC",
    "text": "What is the capital of France?",
    "options": [
      "Paris",
      "London",
      "Rome",
      "Madrid"
    ],
    "answer": "A",
    "remain":15
  },
  {
    "showncode":"uno",
    "type": "SMC",
    "text": "What is the capital of Japan?",
    "options": [
      "Tokyo",
      "Beijing",
      "Seoul",
      "New Delhi"
    ],
    "answer": "A",
    "remain":30
  },
  {
    "showncode":"uno",
    "type": "SMC",
    "text": "Which planet is known as the Red Planet?",
    "options": [
      "Mars",
      "Venus",
      "Jupiter",
      "Saturn"
    ],
    "answer": "A",
    "remain":15
  }
]
''')


@app.route('/lobby')
def lobby():
    return render_template('lobby.html', Rooms=Rooms)


@app.route('/')
def index():
    user_ip = request.remote_addr
    return render_template('index.html', user_ip=user_ip)


@app.route('/RoomCreate')
def room_create():
    return render_template('RoomCreate.html')


@app.route('/QuestionShow')
def qsn_start_game():
    room_id = request.args.get("room_id")
    # print(room_id)
    if (room_id in Rooms):
        room = Rooms[room_id]
        # 展示第一个问题前，status==-1
        if (room.getStatus() < len(room.getQuestions())-1):
            room.incStatus()
            # 展示第一个问题时，status==0
            cq = room.getCurrentQuestion()
            # 不同问题类型渲染不同页面
            if (cq.getType() == "SMC"):
                # print("Now we go to SMC Page.")
                return render_template('Ingame/QuestionShow_SMC.html',
                                       shcd=cq.getShowncode(),
                                       txt=cq.getText(),
                                       opt=cq.getOptions(),
                                       ans=cq.getAnswer(),
                                       rmn=cq.getRemain())
            elif (cq.getType() == "MMC"):
                return render_template('Ingame/QuestionShow_MMC.html',
                                       shcd=cq.getShowncode(),
                                       txt=cq.getText(),
                                       opt=cq.getOptions(),
                                       ans=cq.getAnswers(),
                                       rmn=cq.getRemain())
            elif (cq.getType() == "YN"):
                return render_template('Ingame/QuestionShow_YN.html',
                                       shcd=cq.getShowncode(),
                                       txt=cq.getText(),
                                       ans=cq.getAnswer(),
                                       rmn=cq.getRemain())
            elif (cq.getType() == "STAT"):
                return render_template('Ingame/QuestionShow_STAT.html',
                                       shcd=cq.getShowncode(),
                                       txt=cq.getText(),
                                       rmn=cq.getRemain(),
                                       stat=cq.getState())
    else:
        return render_template('Ingame/QuestionShow.html')


@app.route('/AnswerShow')
def ans_start_game():
    room_id = request.args.get("room_id")
    if (room_id in Rooms):
        room = Rooms[room_id]
        cq = room.getCurrentQuestion()
        # print(cq.getType())
        # 展示第一个问题时，status==0，不同问题类型渲染不同页面
        if (cq.getType() == "SMC"):
            return render_template('Ingame/AnswerShow_SMC.html',
                                   shcd=cq.getShowncode(),
                                   txt=cq.getText(),
                                   opt=cq.getOptions(),
                                   ans=cq.getAnswer(),
                                   rmn=cq.getRemain())
        elif (cq.getType() == "MMC"):
            return render_template('Ingame/AnswerShow_MMC.html',
                                   shcd=cq.getShowncode(),
                                   txt=cq.getText(),
                                   opt=cq.getOptions(),
                                   ans=cq.getAnswers(),
                                   rmn=cq.getRemain())
        elif (cq.getType() == "YN"):
            return render_template('Ingame/AnswerShow_YN.html',
                                   shcd=cq.getShowncode(),
                                   txt=cq.getText(),
                                   ans=cq.getAnswer(),
                                   rmn=cq.getRemain())
        elif (cq.getType() == "STAT"):
            return render_template('Ingame/AnswerShow_STAT.html',
                                   shcd=cq.getShowncode(),
                                   txt=cq.getText(),
                                   rmn=cq.getRemain(),
                                   stat=cq.getState())
    else:
        return render_template('Ingame/AnswerShow.html')


@app.route('/Rank')
def to_rank():
    room_id = request.args.get("room_id")
    # 如果还没完成最后一题，则房主方跳转到SimpleRank.html；如果已经完成最后一题，则房主方跳转到FinalRank.html
    if (Rooms[room_id].getStatus() < len(Rooms[room_id].getQuestions())-1):
        return render_template('SimpleRank.html', room_id=room_id, qtn_order=Rooms[room_id].getStatus())
    else:
        return render_template('FinalRank.html', room_id=room_id)


@app.route('/RoomJoin')
def room_join():
    return render_template('RoomJoin.html')


@app.route('/Prestart')
def prestart():
    return render_template('Prestart.html')


@app.route('/PreAnswer')
def preanswer():
    return render_template('PreAnswer.html')


@socketio.on("checkRoomStatus")
def checkRoomStatus(room_id):
    if room_id in Rooms:
        return Rooms[room_id].getStatus()
    else:
        # 返回-2表示房间不存在
        return -2

# 这里有问题待修复


@socketio.on("checkPlayersData")
def checkPlayers(room_id):
    # print("Checking Players Data")
    if room_id in Rooms:
        players = [p.__dict__() for p in Rooms[room_id].getPlayers()]
        # print(players)
        return players
    else:
        # 返回-2表示房间不存在
        return -2


@socketio.on("checkRankPlayers")
def checkRankPlayers(room_id):
    # 将改房间的玩家list按分数大到小排序
    room = Rooms[room_id]
    room.sortPlayers()
    top3_players_data = {
        "p1_name": "", "p1_score": 0,
        "p2_name": "", "p2_score": 0,
        "p3_name": "", "p3_score": 0
    }
    for i in range(1, 4):
        try:
            top3_players_data[f"p{i}_name"] = (
                room.getPlayers()[i-1]).getName()
            top3_players_data[f"p{i}_score"] = (
                room.getPlayers()[i-1]).getScore()
        except:
            break
    print(top3_players_data)
    return top3_players_data


@socketio.on("checkRoomExists")
def checkRoomExists(data):
    room_id = data["room_id"]
    if room_id in Rooms:
        room = Rooms[room_id]
        user_name = data["name"]
        # print(user_name)
        # 禁止user_name爲空或已被占用的玩家加入游戲
        for p in room.getPlayers():
            if (user_name == p.getName()):
                return {'room_exists': True, 'isReady': False}
        if (user_name == ""):
            return {'room_exists': True, 'isReady': False}
        # 进入回答第一个问题，加入玩家
        user_ip = request.remote_addr
        player = Player(user_name, user_ip)
        room.addPlayer(player)
        return {'room_exists': True, 'isReady': True}
    else:
        return {'room_exists': False}


@socketio.on("removePlayer")
def removePlayer(data):
    room_id = data["room_id"]
    name = data["name"]
    print(name)
    Rooms[room_id].removePlayerByName(name)


@app.route('/ScoreShow')
def score_show():
    room_id = request.args.get("room_id")
    user_ip = request.remote_addr
    room = Rooms[room_id]
    i = 0
    for player in room.getPlayers():
        if (player.getIp() == user_ip):
            score = player.getScore()
            rank = i
            break
        i += 1
    # 如果还没完成最后一题，则玩家方跳转到SimpleScoreShow.html；如果已经完成最后一题，则玩家方跳转到FinalScoreShow.html
    if (room.getStatus() < len(room.getQuestions())-1):
        return render_template('SimpleScoreShow.html', score=score)
    else:
        return render_template('FinalScoreShow.html', score=score, rank=rank+1)


@socketio.on("newQuestion")
def newQuestion(room_id):
    start_time = time.time()
    # print(start_time)
    Rooms[room_id].setTimer(start_time)


@socketio.on("getSecondsLeft")
def getSecondsLeft(data):
    room_id = data["room_id"]
    current_time = time.time()
    qtn_remain = Rooms[room_id].getCurrentQuestion().getRemain()
    left_seconds = int(Rooms[room_id].getTimer() + qtn_remain - current_time)
    if (left_seconds > 0):
        return left_seconds
    else:
        return 0


@socketio.on("toNextQuestion_toclient")
def toNextQuestion(room_id):
    socketio.emit("toNextQuestion_toclient_res")


@socketio.on('process_newroom')
def process_newroom(data):
    # print("start process_newroom")
    room_id = data["room_id"]
    user_ip = request.remote_addr
    Rooms[room_id] = Room(room_id, user_ip)
    # 取得问题集json
    # print("start process_json")
    qtn_file = data['file']
    try:
        # print(qtn_file)
        Rooms[room_id].setQuestionsFromJson(qtn_file)
        join_room(room_id)
        return {'sucess': True}
    except Exception as e:
        # 客户端状态回传（待优化）
        return {'sucess': False, 'error_msg': str(e)}


@socketio.on("checkAnswerIfCorrect")
def checkAnswerIfCorrect(data):
    answer = data["chosen_answer"]
    room_id = data["room_id"]
    room = Rooms[room_id]
    print(answer)
    print(room_id)
    real_ans = room.getCurrentQuestion().getAnswer()
    if (real_ans == answer):
        user_ip = request.remote_addr
        for player in room.getPlayers():
            if (player.getIp() == user_ip):
                player.addScore(10)
                break
    return (real_ans)


@socketio.on("checkMultiAnswersIfCorrect")
def checkMultiAnswerIfCorrect(data):
    answers = data["chosen_answers"]
    room_id = data["room_id"]
    room = Rooms[room_id]
    print(answers)
    print(room_id)
    real_ans = room.getCurrentQuestion().getAnswers()
    if (real_ans == answers):
        user_ip = request.remote_addr
        for player in room.getPlayers():
            if (player.getIp() == user_ip):
                player.addScore(10)
                break
    return (real_ans)


@socketio.on("checkAnswersData")
def checkAnswersData(room_id):
    question = Rooms[room_id].getCurrentQuestion()
    data = {"answer_list": question.getAnswers(
    ), "option_list": question.getOptions()}
    print(data)
    return (data)


@socketio.on("refreshRoomDataShow")
def refreshRoomDataShow(p):
    data = [room.__dict__() for room in Rooms.values()]
    # print(str(data))
    return str(data)


@socketio.on("DeleteRoomData")
def DeleteRoomData(room_id):
    if (room_id in Rooms):
        del Rooms[room_id]


if __name__ == '__main__':
    # app.run(host='0.0.0.0',debug=1)
    # socketio.run(app, host='0.0.0.0', port=5000,debug=1)
    socketio.run(app, host='0.0.0.0', port=80, debug=1)
