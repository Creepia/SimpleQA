function toLobby() {
    window.location.href = 'lobby.html';
}



// 回答问题
function answerQuestion() {
    clearInterval(timerInterval);
    socket.emit('answer_question', {
        room_id: '{{ room_id }}',
        question_number: '{{ question_number }}'
    });
}



