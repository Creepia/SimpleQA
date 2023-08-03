



function toLobby(){
    window.location.href = 'lobby.html';
}

function toNextQuestion(){
    var urlParams = new URLSearchParams(window.location.search);
    var r=urlParams.get('room_id');
    window.location.href = 'QuestionShow.html?room_id='+r;
}






// 回答问题
function answerQuestion() {
    clearInterval(timerInterval);
    socket.emit('answer_question', {
        room_id: '{{ room_id }}',
        question_number: '{{ question_number }}'
    });
}



