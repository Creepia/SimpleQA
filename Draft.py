# QuestionShow 页面
@app.route('/question/<string:room_id>/<int:question_number>')
def question_show(room_id, question_number):
    # 在此处根据 room_id 和 question_number 获取相应的题目信息
    # 可以从服务器端维护的题目列表中获取对应题目信息
    question_info = {
        "type": "SMC",
        "question": "What is the capital of France?",
        "options": ["Paris", "London", "Rome", "Madrid"],
        "answer": "A"
    }
    return render_template('QuestionShow.html', room_id=room_id, question_number=question_number, **question_info)

# SimpleRank 页面
@app.route('/rank/<string:room_id>/<int:question_number>')
def simple_rank(room_id, question_number):
    # 在此处根据 room_id 和 question_number 获取玩家得分等信息
    # 可以从服务器端维护的玩家得分列表中获取相应信息
    player1_score = 0
    player2_score = 0
    player3_score = 0
    # 可以添加更多玩家得分信息

    return render_template('SimpleRank.html', room_id=room_id, question_number=question_number, 
                           player1_score=player1_score, player2_score=player2_score, player3_score=player3_score)