"""
这是一个为了SimpleQA而做出来的依赖库.\n
含Player,Room,Question三大类以及一些他们的子类.
"""

import json


class Player:
    def __init__(self, name: str, ip: str, score: int = 0):
        self.__name = name
        self.__ip = ip
        self.__score = score
        self.__ready = False

    def __repr__(self) -> str:
        return str({"name": self.__name,
                    "ip": self.__ip,
                    "score": self.__score,
                    "ready": self.__ready})

    def __dict__(self) -> dict[str, str | int]:
        return {"name": self.__name,
                "ip": self.__ip,
                "score": self.__score,
                "ready": self.__ready}

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

    def hasReady(self) -> bool:
        return (self.__ready)

    def setReady(self, stat: bool) -> None:
        self.__ready = stat


class Question:
    def __init__(self, type: str, showncode: str, text: str, remain: int = 15):
        '''
        Question类是问题、提示页面等的基础类.\n
        必须先确认三个基本参数：\n
            type:类型，值为"SMC"（单项选择）,"YN"（判断）等等.\n
            showncode:题号，一般为"Q1","First Question","1."等等.\n
            text:显示文本，如"Which is the biggest mammal?".\n
        另外有remain参数为该页面的停留时间，时间到达将跳过这个页面，单位为s,會自動加上0.5秒與延遲抵消.
        '''
        self.__type = type
        self.__showncode = showncode
        self.__text = text
        self.__remain = remain+0.5

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

    def __repr__(self) -> str:
        return str({"type": self.getType(),
                    "showncode": self.getShowncode(),
                    "text": self.getText(),
                    "remain": self.getRemain(),
                    "options": self.getOptions(),
                    "answer": self.getAnswer()
                    })

    def getOptions(self) -> list:
        return (self.__options)

    def getAnswer(self) -> str:
        return (self.__answer)


class MMC(Question):
    def __init__(self, type: str, showncode: str, text: str, remain: int, options: list, answers: list):
        super().__init__(type, showncode, text, remain)
        self.__options = options
        self.__answers = answers

    def __repr__(self) -> str:
        return str({"type": self.getType(),
                    "showncode": self.getShowncode(),
                    "text": self.getText(),
                    "remain": self.getRemain(),
                    "options": self.getOptions(),
                    "answers": self.getAnswers()
                    })

    def getOptions(self) -> list:
        return (self.__options)

    def getAnswers(self) -> list:
        return (self.__answers)


class YN(Question):
    def __init__(self, type: str, showncode: str, text: str, remain: int, answer: str):
        super().__init__(type, showncode, text, remain)
        self.__answer = answer

    def __repr__(self) -> str:
        return str({"type": self.getType(),
                    "showncode": self.getShowncode(),
                    "text": self.getText(),
                    "remain": self.getRemain(),
                    "answer": self.getAnswer()
                    })

    def getAnswer(self) -> str:
        return (self.__answer)


class STAT(Question):
    def __init__(self, type: str, showncode: str, text: str, remain: int, state: str):
        super().__init__(type, showncode, text, remain)
        self.__state = state

    def __repr__(self) -> str:
        return str({"type": self.getType(),
                    "showncode": self.getShowncode(),
                    "text": self.getText(),
                    "remain": self.getRemain(),
                    "state": self.getState()
                    })

    def getState(self) -> str:
        return (self.__state)


class Room:
    def __init__(self, room_id: str, master_ip: str = "0.0.0.0"):
        """
        创建房间简易例子（忽略房间创建者的ip）:\n
        Room("000000")
        """
        self.__room_id = room_id
        self.__player_list: list[Player] = []
        self.__question_list: list[Question] = []
        self.__master_ip = master_ip
        self.__status = -1
        self.__timer = 0

    def __repr__(self) -> str:
        return str({"room_id": self.__room_id,
                    "player_list": self.__player_list,
                    "question_list": self.__question_list,
                    "master_ip": self.__master_ip,
                    "status": self.__status,
                    "timer": self.__timer, })

    def __dict__(self) -> dict:
        return {"room_id": self.__room_id,
                "player_list": self.__player_list,
                "question_list": self.__question_list,
                "master_ip": self.__master_ip,
                "status": self.__status,
                "timer": self.__timer, }

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

    def getPlayerByName(self, player_name: str) -> Player:
        for inlist_player in self.__player_list:
            if (inlist_player.getName() == player_name):
                return (inlist_player)

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

    def isAllPlayersReady(self) -> bool:
        for player in self.getPlayers():
            if not player.hasReady():
                return False
        return True

    def getPlayersInReady(self) -> int:
        count = 0
        for player in self.getPlayers():
            if player.hasReady():
                count += 1
        return count

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
                    self.__addQuesion(YN(question["type"], question["showncode"], question["text"],
                                         question["remain"], question["answer"]))
                elif (question["type"] == "STAT"):
                    self.__addQuesion(STAT(question["type"], question["showncode"], question["text"],
                                           question["remain"], question["state"]))
        except Exception as e:
            print(e)

    def getCurrentQuestion(self) -> Question | SMC | MMC | YN | STAT:
        if (self.getStatus() > -1 and self.getStatus() < len(self.getQuestions())):
            return (self.__question_list[self.getStatus()])

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
