var formData = new FormData();
var room_id = -1;

if(room_id==-1){
    room_id = Math.floor(Math.random() * 1000000) + 1;
}

function checkFile() {
    var fileInput = document.getElementById('file-input');
    var errorMessage = document.getElementById('error-message');
    var nextButton = document.getElementById('next-button');

    var file = fileInput.files[0];
    if (file && file.name.endsWith('.json')) {
        formData.append('file', file);
        alert(room_id);
        formData.append('room_id',room_id);
        nextButton.classList.remove('disabled');
        nextButton.disabled = false;
        errorMessage.textContent = '';
        
    } else {
        // 文件格式错误，显示错误信息
        nextButton.classList.add('disabled');
        nextButton.disabled = true;
        errorMessage.textContent = 'Invalid file format. Please upload a .json file.';
    }
}

function toPrestart(){
    var xhr = new XMLHttpRequest();
    var errorMessage = document.getElementById('error-message');
    var nextButton = document.getElementById('next-button');
    xhr.open('POST', '/process_json');
    alert("xhr opened.");
    // 将文件数据作为请求体发送给后端
    xhr.send(formData);
    xhr.onload = function() {
        // alert(xhr.status);
        if (xhr.status === 200) {
            // 读取成功
            var response = JSON.parse(xhr.responseText);
            if (response.success) {
                // 文件格式正确，跳转到该房间号的页面
                window.location.href = 'Prestart.html?room_id=' + room_id;
            } else {
                // 文件格式错误，显示错误信息
                nextButton.classList.add('disabled');
                nextButton.disabled = true;
                errorMessage.textContent = response.error;
            }
        } else {
            // 请求错误
            errorMessage.textContent = 'An error occurred while processing the file.';
        }
    };
    
}

function toQuestionShow(){
    var urlParams = new URLSearchParams(window.location.search);
    var r=urlParams.get('room_id');
    window.location.href = 'QuestionShow.html?room_id='+r;
}

function toLobby(){
    window.location.href = 'lobby.html';
}

function toNextQuestion(){
    var urlParams = new URLSearchParams(window.location.search);
    var r=urlParams.get('room_id');
    window.location.href = 'QuestionShow.html?room_id='+r;
}

var players = [
    { name: 'Alex', ip: '123.4.56.78' },
    { name: 'Bob', ip: '100.2.88.9' },
    { name: 'Carol', ip: '102.0.231.114' }
];

function displayRoomId(){
    // 在 Prestart.html 页面中获取 URL 参数中的房间号
    // alert("displayRoomId");
    var urlParams = new URLSearchParams(window.location.search);
    var roomIdTitle = document.getElementById('room-id');
    roomIdTitle.textContent = urlParams.get('room_id');
}

function displayPlayers() {
    var playerTable = document.getElementById('player-table');
    playerTable.innerHTML = '';

    for (var i = 0; i < players.length; i++) {
        var player = players[i];
        var row = document.createElement('tr');
        var nameCell = document.createElement('td');
        var ipCell = document.createElement('td');

        nameCell.textContent = player.name;
        ipCell.textContent = player.ip;

        row.appendChild(nameCell);
        row.appendChild(ipCell);

        // 添加鼠标悬停和点击事件监听器
        row.addEventListener('mouseover', function () {
            this.style.color = 'red';
            this.style.textDecoration = 'line-through';
        });

        row.addEventListener('mouseout', function () {
            this.style.color = '';
            this.style.textDecoration = '';
        });

        row.addEventListener('click', function () {
            var index = Array.from(playerTable.children).indexOf(this);
            players.splice(index, 1);
            displayPlayers();
        });

        playerTable.appendChild(row);
    }
}

// 开始计时器
function startTimer() {
    // document.getElementById('answer-button').disabled = false;
    socket.emit('start_timer', { room_id: '{{ room_id }}' });
    var timeRemaining = 15;
    // alert("in startTimer()");
    document.getElementById('timer').textContent = timeRemaining;
    timerInterval = setInterval(function() {
        timeRemaining -= 1;
        if (timeRemaining >= 0) {
            document.getElementById('timer').textContent = timeRemaining;
        } else {
            clearInterval(timerInterval);
            document.getElementById('timer').textContent = 'Time is up!';
            var urlParams = new URLSearchParams(window.location.search);
            var r=urlParams.get('room_id');
            window.location.href = 'Rank.html?room_id='+r;
            // document.getElementById('answer-button').disabled = true;
        }
    }, 1000);
}

// 回答问题
function answerQuestion() {
    clearInterval(timerInterval);
    socket.emit('answer_question', {
        room_id: '{{ room_id }}',
        question_number: '{{ question_number }}'
    });
}



