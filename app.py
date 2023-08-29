from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, send, join_room, leave_room
from random import randint
import json
import time


class Player:
    def __init__(self, name: str, ip: str, score: int = 0):
        self.__name = name
        self.__ip = ip
        self.__score = score

    def getName(self) -> str:
        return (self.__name)

    def setName(self, name: str):
        self.__name = name

    def getIp(self) -> str:
        return (self.__ip)

    def getScore(self) -> int:
        return (self.__score)

    def addScore(self, score: int) -> None:
        self.__score += score


class Question:
    def __init__(self, type: str, showncode: str, text: str, remain: int = 15):
        '''
        Question类是问题、提示页面等的基础类.\n
        必须先确认三个基本参数：\n
            type:类型，值为"SMC"（单项选择）,"YN"（判断）等等.\n
            showncode:题号，一般为"Q1","First Question","1."等等.\n
            text:显示文本，如"Which is the biggest mammal?".\n
        另外有remain参数为该页面的停留时间，时间到达将跳过这个页面，默认为15，单位为s.
        '''
        self.type = type
        self.showncode = showncode
        self.text = text
        self.remain = remain

    def getType(self) -> str:
        return (self.type)

    def getShowncode(self) -> str:
        return (self.showncode)

    def getText(self) -> str:
        return (self.text)

    def getRemain(self) -> int:
        return (self.remain)


class SMC(Question):
    def __init__(self, type: str, showncode: str, text: str, remain: int, options: list, answer: str):
        super().__init__(type, showncode, text, remain)
        self.options = options
        self.answer = answer
    def getOptions(self)->list:
        return(self.options)
    def getAnswer(self)->str:
        return(self.answer)
    
class MMC(Question):
    def __init__(self, type: str, showncode: str, text: str, remain: int, options: list, answers: list):
        super().__init__(type, showncode, text, remain)
        self.options = options
        self.answers = answers
    def getOptions(self)->list:
        return(self.options)
    def getAnswer(self)->list:
        return(self.answers)

class YN(Question):
    def __init__(self, type: str, showncode: str, text: str, remain: int, answer: str):
        super().__init__(type, showncode, text, remain)
        self.answer = answer
    def getAnswer(self)->str:
        return(self.answer)
    
class STAT(Question):
    def __init__(self, type: str, showncode: str, text: str, remain: int, state: str):
        super().__init__(type, showncode, text, remain)
        self.state = state
    def getAnswer(self)->str:
        return(self.state)

class Room:
    def __init__(self, room_id: str, master_ip: str = "0.0.0.0"):
        self.__room_id = room_id
        self.__player_list = []
        self.__question_list = []
        self.__master_ip = master_ip
        self.status = -1
        self.timer = 0

    def getId(self) -> str:
        return (self.__room_id)

    def getPlayers(self) -> list:
        return (self.__player_list)

    def hasPlayerByName(self, player_name: str) -> bool:
        if (len(self.__player_list) == 0):
            return (False)
        for inlist_player in self.__player_list:
            if (inlist_player.getName() == player_name):
                return (True)
        return (False)

    def addPlayer(self, player: Player) -> int:
        '''
        成功添加玩家後返回0，否则返回-1.
        '''
        if (self.hasPlayerByName(player.getName()) == False):
            self.player_list.append(player)
            return (0)
        return (-1)

    def removePlayerByName(self, player_name: str) -> None:
        try:
            for inlist_player in self.__player_list:
                if (inlist_player.getName() == player_name):
                    self.player_list.remove(inlist_player)
        except:
            raise KeyError("移除玩家失敗")

    def getQuestions(self) -> list:
        return (self.__question_list)

    def setQuesions(self, question_list: list) -> None:
        self.__question_list = question_list

    def getMasterIp(self) -> str:
        return (self.__master_ip)

    def getStatus(self) -> int:
        return (self.status)

    def incStatus(self, increment: int = 1) -> None:
        self.status += increment

    def setStatus(self, number: int) -> None:
        self.status = number

    def getTimer(self) -> int:
        return (self.timer)

    def setTimer(self, number: int) -> None:
        self.timer = number


app = Flask(__name__)
app.config["SECRET_KEY"] = "korekoso_himituda"
socketio = SocketIO(app)
Rooms = {
    "000000": {
        "master": "123.123.123.123",
        "players": [
            {"name": 'Alex', "ip": '123.4.56.78', "score": 10},
            {"name": 'Bob', "ip": '100.2.88.9', "score": 20},
            {"name": 'Carol', "ip": '102.0.231.114', "score": 30}
        ],
        "questions": [
            {
                "showncode": "uno",
                "type": "SMC",
                "question": "What is the capital of France?",
                "options": ["Paris", "London", "Rome", "Madrid"],
                "answer": "A"
            },
            {
                "showncode": "dois",
                "type": "MMC",
                "question": "Which colors are primary colors? (Select all that apply)",
                "options": ["Red", "Green", "Blue", "Yellow"],
                "answer": ["A", "C", "D"]
            }
        ],
        "status": -1,
        "timer": 0
    }
}


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


@app.route('/ScoreShow')
def score_show():
    room_id = request.args.get("room_id")
    user_ip = request.remote_addr
    i = 0
    for player in Rooms[room_id]["players"]:
        if (player["ip"] == user_ip):
            name = player["name"]
            score = player["score"]
            rank = i
            break
        i += 1
    # 如果还没完成最后一题，则玩家方跳转到SimpleScoreShow.html；如果已经完成最后一题，则玩家方跳转到FinalScoreShow.html
    if (Rooms[room_id]["status"] < len(Rooms[room_id]["questions"])-1):
        return render_template('SimpleScoreShow.html', qtn_order=Rooms[room_id]["status"], name=name, score=score)
    else:
        return render_template('FinalScoreShow.html', qtn_order=Rooms[room_id]["status"], name=name, score=score, rank=rank+1)


@app.route('/QuestionShow')
def qsn_start_game():
    room_id = request.args.get("room_id")
    if (room_id in Rooms):
        number_of_questions = len(Rooms[room_id]["questions"])
        # 展示第一个问题时，status==0
        if (Rooms[room_id]["status"] < number_of_questions-1):
            Rooms[room_id]["status"] += 1
            qtn_order = Rooms[room_id]["status"]
            if (Rooms[room_id]["questions"][qtn_order]["type"] == "SMC"):
                qtn = Rooms[room_id]["questions"][qtn_order]["question"]
                opt = Rooms[room_id]["questions"][qtn_order]["options"]
                ans = Rooms[room_id]["questions"][qtn_order]["answer"]
                return render_template('Ingame/QuestionShow_SMC.html', showncode=Rooms[room_id]["questions"][qtn_order]["showncode"], qtn=qtn, opt=opt, ans=ans)
            elif (Rooms[room_id]["questions"][qtn_order]["type"] == "MMC"):
                qtn = Rooms[room_id]["questions"][qtn_order]["question"]
                opt = Rooms[room_id]["questions"][qtn_order]["options"]
                ans = Rooms[room_id]["questions"][qtn_order]["answer"]
                return render_template('Ingame/QuestionShow_MMC.html', showncode=Rooms[room_id]["questions"][qtn_order]["showncode"], qtn=qtn, opt=opt, ans=ans)
            elif (Rooms[room_id]["questions"][qtn_order]["type"] == "YN"):
                qtn = Rooms[room_id]["questions"][qtn_order]["question"]
                ans = Rooms[room_id]["questions"][qtn_order]["answer"]
                return render_template('Ingame/QuestionShow_YN.html', showncode=Rooms[room_id]["questions"][qtn_order]["showncode"], qtn=qtn, ans=ans)
    else:
        return render_template('Ingame/QuestionShow.html')


@app.route('/AnswerShow')
def ans_start_game():
    room_id = request.args.get("room_id")
    if (room_id in Rooms):
        # 展示第一个问题时，status==0
        qtn_order = Rooms[room_id]["status"]
        if (Rooms[room_id]["questions"][qtn_order]["type"] == "SMC"):
            qtn = Rooms[room_id]["questions"][qtn_order]["question"]
            opt = Rooms[room_id]["questions"][qtn_order]["options"]
            ans = Rooms[room_id]["questions"][qtn_order]["answer"]
            return render_template('Ingame/AnswerShow_SMC.html', showncode=Rooms[room_id]["questions"][qtn_order]["showncode"], qtn=qtn, opt=opt, ans=ans)
        elif (Rooms[room_id]["questions"][qtn_order]["type"] == "MMC"):
            qtn = Rooms[room_id]["questions"][qtn_order]["question"]
            opt = Rooms[room_id]["questions"][qtn_order]["options"]
            ans = Rooms[room_id]["questions"][qtn_order]["answer"]
            return render_template('Ingame/AnswerShow_MMC.html', showncode=Rooms[room_id]["questions"][qtn_order]["showncode"], qtn=qtn, opt=opt, ans=ans)
        elif (Rooms[room_id]["questions"][qtn_order]["type"] == "YN"):
            qtn = Rooms[room_id]["questions"][qtn_order]["question"]
            ans = Rooms[room_id]["questions"][qtn_order]["answer"]
            return render_template('Ingame/AnswerShow_YN.html', showncode=Rooms[room_id]["questions"][qtn_order]["showncode"], qtn=qtn, ans=ans)
    else:
        return render_template('Ingame/AnswerShow.html')


@app.route('/Rank')
def to_rank():
    room_id = request.args.get("room_id")
    # 如果还没完成最后一题，则房主方跳转到SimpleRank.html；如果已经完成最后一题，则房主方跳转到FinalRank.html
    if (Rooms[room_id]["status"] < len(Rooms[room_id]["questions"])-1):
        return render_template('SimpleRank.html', room_id=room_id, qtn_order=Rooms[room_id]["status"])
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
    Rooms[room_id]["players"].sort(
        key=lambda player: player["score"], reverse=True)
    top3_players_data = {
        "p1_name": "", "p1_score": 0,
        "p2_name": "", "p2_score": 0,
        "p3_name": "", "p3_score": 0
    }
    for i in range(1, 4):
        try:
            top3_players_data[f"p{i}_name"] = Rooms[room_id]["players"][i-1]["name"]
            top3_players_data[f"p{i}_score"] = Rooms[room_id]["players"][i-1]["score"]
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
        # 禁止user_name爲空或已被占用的玩家加入游戲
        for p in Rooms[room_id]["players"]:
            if (user_name in p["name"]):
                return {'room_exists': True, 'isReady': False}
        if (user_name == ""):
            return {'room_exists': True, 'isReady': False}
        # 进入回答第一个问题，加入玩家
        user_ip = request.remote_addr
        Rooms[room_id]["players"].append(
            {"ip": user_ip, "name": user_name, "score": 0})
        return {'room_exists': True, 'isReady': True}
    else:
        return {'room_exists': False}


@socketio.on("removePlayer")
def removePlayer(data):
    room_id = data["room_id"]
    ip = data["ip"]
    print(ip)
    for p in Rooms[room_id]["players"]:
        if (p["ip"] == ip):
            Rooms[room_id]["players"].remove(p)
            break


@socketio.on("newQuestion")
def newQuestion(room_id):
    start_time = time.time()
    print(start_time)
    Rooms[room_id]["timer"] = start_time


@socketio.on("getSecondsLeft")
def getSecondsLeft(data):
    room_id = data["room_id"]
    current_time = time.time()
    left_seconds = int(Rooms[room_id]["timer"]+15-current_time)
    if (left_seconds > 0):
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
    room_id = data["room_id"]
    Rooms[room_id] = {"status": -1, "players": [], "questions": []}
    # 取得问题集json
    # print("start process_json")
    qtn_file = data['file']
    try:
        data = json.loads(qtn_file)
        # print(data)
        # 在这里对 JSON 数据进行处理
        Rooms[room_id]["questions"] = data
        # print(request.sid)
        join_room(room_id)
        return {'sucess': True}
    except Exception as e:
        # 客户端状态回传（待优化）
        return {'sucess': False, 'error_msg': str(e)}


@socketio.on("refreshRoomDataShow")
def refreshRoomDataShow(data):
    return Rooms


@socketio.on("checkAnswerIfCorrect")
def checkAnswerIfCorrect(data):
    answer = data["chosen_answer"]
    room_id = data["room_id"]
    print(answer)
    print(room_id)
    qtn_order = Rooms[room_id]["status"]
    real_ans = Rooms[room_id]["questions"][qtn_order]["answer"]
    if (real_ans == answer):
        user_ip = request.remote_addr
        for player in Rooms[room_id]["players"]:
            if (player["ip"] == user_ip):
                player["score"] += 10
                break
    return (real_ans)


@socketio.on("checkMultiAnswersIfCorrect")
def checkAnswerIfCorrect(data):
    answers = data["chosen_answers"]
    room_id = data["room_id"]
    print(answers)
    print(room_id)
    qtn_order = Rooms[room_id]["status"]
    real_ans = Rooms[room_id]["questions"][qtn_order]["answer"]
    if (real_ans == answers):
        user_ip = request.remote_addr
        for player in Rooms[room_id]["players"]:
            if (player["ip"] == user_ip):
                player["score"] += 10
                break
    return (real_ans)


@socketio.on("checkAnswersData")
def checkAnswerIfCorrect(room_id):
    qtn_order = Rooms[room_id]["status"]
    answer_list = Rooms[room_id]["questions"][qtn_order]["answer"]
    option_list = Rooms[room_id]["questions"][qtn_order]["options"]
    data = {"answer_list": answer_list, "option_list": option_list}
    print(data)
    return (data)


if __name__ == '__main__':
    # app.run(host='0.0.0.0',debug=1)
    # socketio.run(app, host='0.0.0.0', port=5000,debug=1)
    socketio.run(app, host='0.0.0.0', port=80, debug=1)
