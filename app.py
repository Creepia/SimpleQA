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
        self.__type = type
        self.__showncode = showncode
        self.__text = text
        self.__remain = remain

    def getType(self) -> str:
        return (self.__type)

    def getShowncode(self) -> str:
        return (self.__showncode)

    def getText(self) -> str:
        return (self.__text)

    def getRemain(self) -> int:
        return (self.__remain)


class SMC(Question):
    def __init__(self, type: str, showncode: str, text: str, remain: int, options: list, answer: str):
        super().__init__(type, showncode, text, remain)
        self.__options = options
        self.__answer = answer

    def getOptions(self) -> list:
        return (self.__options)

    def getAnswer(self) -> str:
        return (self.__answer)


class MMC(Question):
    def __init__(self, type: str, showncode: str, text: str, remain: int, options: list, answers: list):
        super().__init__(type, showncode, text, remain)
        self.__options = options
        self.__answers = answers

    def getOptions(self) -> list:
        return (self.__options)

    def getAnswers(self) -> list:
        return (self.__answers)


class YN(Question):
    def __init__(self, type: str, showncode: str, text: str, remain: int, answer: str):
        super().__init__(type, showncode, text, remain)
        self.__answer = answer

    def getAnswer(self) -> str:
        return (self.__answer)


class STAT(Question):
    def __init__(self, type: str, showncode: str, text: str, remain: int, state: str):
        super().__init__(type, showncode, text, remain)
        self.state = state

    def getAnswer(self) -> str:
        return (self.state)


class Room:
    def __init__(self, room_id: str, master_ip: str = "0.0.0.0"):
        self.__room_id = room_id
        self.__player_list: list[Player] = []
        self.__question_list: list[Question] = []
        self.__master_ip = master_ip
        self.__status = -1
        self.__timer = 0

    def getId(self) -> str:
        return (self.__room_id)

    def getPlayers(self) -> list[Player]:
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
            self.__player_list.append(player)
            return (0)
        return (-1)

    def removePlayerByName(self, player_name: str) -> None:
        try:
            for inlist_player in self.__player_list:
                if (inlist_player.getName() == player_name):
                    self.__player_list.remove(inlist_player)
        except:
            raise KeyError("移除玩家失敗")

    def sortPlayers(self) -> None:
        """
        将房间中的玩家按分数由大到小原地排序.
        """
        self.__player_list.sort(
            key=lambda player: player.getScore(), reverse=True)

    def getQuestions(self) -> list[Question]:
        return (self.__question_list)

    def __addQuesion(self, question: dict) -> None:
        self.__question_list.append(question)

    def setQuestionsFromJson(self, json_file) -> None:
        try:
            data = json.loads(json_file)
            for question in data:
                if (question["type"] == "SMC"):
                    self.__addQuesion(SMC(question["type"], question["showncode"], question["text"],
                                      question["remain"], question["options"], question["answer"]))
                elif (question["type"] == "MMC"):
                    self.__addQuesion(MMC(question["type"], question["showncode"], question["text"],
                                      question["remain"], question["options"], question["answers"]))
                elif (question["type"] == "YN"):
                    self.__addQuesion(
                        YN(question["type"], question["showncode"], question["text"], question["remain"], question["answer"]))
                elif (question["type"] == "STAT"):
                    self.__addQuesion(STAT(
                        question["type"], question["showncode"], question["text"], question["remain"], question["state"]))
        except:
            pass

    def getCurrentQuestion(self) -> Question | SMC | MMC | YN | STAT:
        if (self.__status > -1 and self.__status < len(self.__question_list)):
            return (self.__question_list[self.__status])

    def getMasterIp(self) -> str:
        return (self.__master_ip)

    def getStatus(self) -> int:
        return (self.__status)

    def incStatus(self, increment: int = 1) -> None:
        self.__status += increment

    def setStatus(self, number: int) -> None:
        self.__status = number

    def getTimer(self) -> int:
        return (self.__timer)

    def setTimer(self, number: int) -> None:
        self.__timer = number


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
    if (room_id in Rooms):
        room = Rooms[room_id]
        cq = room.getCurrentQuestion()
        # 展示第一个问题时，status==0
        if (room.getStatus() < len(room.getQuestions())-1):
            room.incStatus()
            # 不同问题类型渲染不同页面
            if (cq.getType() == "SMC"):
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
    else:
        return render_template('Ingame/QuestionShow.html')


@app.route('/AnswerShow')
def ans_start_game():
    room_id = request.args.get("room_id")
    if (room_id in Rooms):
        room = Rooms[room_id]
        cq = room.getCurrentQuestion()
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
    if room_id in Rooms:
        players = Rooms[room_id].getPlayers()
        return players
    else:
        # 返回-2表示房间不存在
        return -2


@socketio.on("checkRankPlayers")
def checkRankPlayers(room_id):
    # 将改房间的玩家list按分数大到小排序
    room=Rooms[room_id]
    room.sortPlayers()
    top3_players_data = {
        "p1_name": "", "p1_score": 0,
        "p2_name": "", "p2_score": 0,
        "p3_name": "", "p3_score": 0
    }
    for i in range(1, 4):
        try:
            top3_players_data[f"p{i}_name"] = (room.getPlayers()[i-1]).getName()
            top3_players_data[f"p{i}_score"] = (room.getPlayers()[i-1]).getScore()
        except:
            break
    print(top3_players_data)
    return top3_players_data


@socketio.on("checkRoomExists")
def checkRoomExists(data):
    room_id = data["room_id"]
    if room_id in Rooms:
        room=Rooms[room_id]
        user_name = data["name"]
        print(user_name)
        # 禁止user_name爲空或已被占用的玩家加入游戲
        for p in room.getPlayers():
            if (user_name == p.getName()):
                return {'room_exists': True, 'isReady': False}
        if (user_name == ""):
            return {'room_exists': True, 'isReady': False}
        # 进入回答第一个问题，加入玩家
        user_ip = request.remote_addr
        player=Player(user_name,user_ip)
        room.addPlayer(player)
        return {'room_exists': True, 'isReady': True}
    else:
        return {'room_exists': False}


@socketio.on("removePlayer")
def removePlayer(data):
    room_id = data["room_id"]
    name=data["name"]
    print(name)
    Rooms[room_id].removePlayerByName(name)


@app.route('/ScoreShow')
def score_show():
    room_id = request.args.get("room_id")
    user_ip = request.remote_addr
    room=Rooms[room_id]
    i = 0
    for player in room.getPlayers():
        if (player.getIp == user_ip):
            name = player["name"]
            score = player["score"]
            rank = i
            break
        i += 1
    # 如果还没完成最后一题，则玩家方跳转到SimpleScoreShow.html；如果已经完成最后一题，则玩家方跳转到FinalScoreShow.html
    if (room.getStatus() < len(room.getQuestions())-1):
        return render_template('SimpleScoreShow.html', qtn_order=room.getStatus(), name=name, score=score)
    else:
        return render_template('FinalScoreShow.html', qtn_order=room.getStatus(), name=name, score=score, rank=rank+1)


@socketio.on("newQuestion")
def newQuestion(room_id):
    start_time = time.time()
    print(start_time)
    Rooms[room_id].setTimer(start_time)


@socketio.on("getSecondsLeft")
def getSecondsLeft(data):
    room_id = data["room_id"]
    current_time = time.time()
    left_seconds = int(Rooms[room_id].getTimer()+15-current_time)
    if (left_seconds > 0):
        return left_seconds
    else:
        return 0


@socketio.on("toNextQuestion")
def toNextQuestion(room_id):
    socketio.emit("toNextQuestion_res")


@socketio.on('process_newroom')
def process_newroom(data):
    # print("start process_newroom")
    room_id = data["room_id"]
    user_ip = request.remote_addr
    Rooms[room_id] = Room(room_id,user_ip)
    # 取得问题集json
    # print("start process_json")
    qtn_file = data['file']
    try:
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
    room=Rooms[room_id]
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
    room=Rooms[room_id]
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
    question=Rooms[room_id].getCurrentQuestion()
    data = {"answer_list": question.getAnswers(), "option_list": question.getOptions()}
    print(data)
    return (data)


if __name__ == '__main__':
    # app.run(host='0.0.0.0',debug=1)
    # socketio.run(app, host='0.0.0.0', port=5000,debug=1)
    socketio.run(app, host='0.0.0.0', port=80, debug=1)
