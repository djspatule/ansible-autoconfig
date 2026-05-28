// All object programming based on
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Working_with_Objects

/*---------------------------------

    Variables declaration

-----------------------------------*/

var turnLength = 30;

function playBeep() {
  try {
    var AudioContextCtor = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextCtor) {
      return;
    }
    var context = new AudioContextCtor();
    var oscillator = context.createOscillator();
    var gainNode = context.createGain();
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(880, context.currentTime);
    gainNode.gain.setValueAtTime(0.05, context.currentTime);
    oscillator.connect(gainNode);
    gainNode.connect(context.destination);
    oscillator.start();
    oscillator.stop(context.currentTime + 0.12);
    oscillator.onended = function () {
      context.close();
    };
  } catch (error) {
    // Ignore browsers that block or lack Web Audio support.
  }
}

var numberOfPlayers = 2;
var isGameStarted = false;
var isMute = true;
var isDark = false;
var isSettingsCollapsed = true;
var isdropdownCollapsed = true;

var newPlayerNode = document.getElementById('newPlayerNode');
var dropDownForm = document.getElementById('dropDownForm');
var dropDownFormGroup = document.getElementById('dropDownFormGroup');

const players = [];

var r = 0;
var g = 0;
var b = 0;

var gameHr = 0;
var gameSec = 0;
var gameMin = 0;
var isTimeStopped = true;
var gameStart = Date.now();
var turnStart = Date.now();
var isNewTurn = true;
var isGamePaused = false;

var totalPlayTimeDisplayDiv = document.getElementById('totalPlayTimeDisplayDiv');

var darkButton = document.getElementById('darkButton');
darkButton.addEventListener('click', dark);

var muteButton = document.getElementById('muteButton');
muteButton.addEventListener('click', mute);

var settingsButton = document.getElementById('settingsButton');
settingsButton.addEventListener('click', collapse);

var pauseButton = document.getElementById('pauseButton');
pauseButton.addEventListener('click', pause);

document.querySelector('#setNumberOfPlayersButton').onclick = setNumberOfPlayers;
document.querySelector('#setTurnLengthButton').onclick = setTurnLength;
document.querySelector('#totalPlayTimeButton').onclick = resetTotalPlayTimer;
document.querySelector('#playerSettingsButton').onclick = showDropDown;
document.querySelector('#playersSettingsSubmissionButton').onclick = registerPlayersSettings;

document.addEventListener('DOMContentLoaded', setNumberOfPlayers);

function resetTimers() {
  for (const player of players) {
    clearTimeout(player.timeout);
    player.sec = turnLength;
    turnStart = Date.now();
    document.getElementById('playerTimerDiv' + player.playerNumber).innerHTML = turnLength;
    document.getElementById('playerTimerDiv' + player.playerNumber).classList.remove('text-danger');
    var playerButton = document.getElementById('player' + player.playerNumber + 'Button');
    playerButton.querySelector('.progressButton__progress').style.height = '0%';
    isNewTurn = true;
  }
}

function collapseSettings() {
  dropDownForm.classList.remove('show');
  settingsDiv.classList.remove('show');
  isSettingsCollapsed = true;
  settingsButton.classList.remove('btn-secondary');
  settingsButton.classList.add('btn-outline-secondary');
  isdropdownCollapsed = true;
  dropDownForm.classList.remove('show');
}

function addZero(i) {
  if (i < 10) {
    i = '0' + i;
  }
  return i;
}

function randomRGB() {
  r = Math.floor(Math.random() * 100 + 100);
  g = Math.floor(Math.random() * 100 + 100);
  b = Math.floor(Math.random() * 100 + 100);
  return '#' + parseInt(r).toString(16) + parseInt(g).toString(16) + parseInt(b).toString(16);
}

class Player {
  constructor(_playerNumber, _sec) {
    this.playerNumber = _playerNumber;
    this.playerName = 'Player ' + (this.playerNumber + 1);
    this.rgb = randomRGB();
    this.timeout = 0;
    this.sec = _sec;
    this.playerHr = 0;
    this.playerMin = 0;
    this.playerSec = 0;
    this.totalPlayerSec = 0;
    this.delta = 0;
    this.playerNameFormGroup = document.createElement('div');
    this.div = document.createElement('div');
  }

  get newButton() {
    return `<br>
    <button type="button" class="progressButton" style="background-color:${this.rgb}" id="player${this.playerNumber}Button">
      <div class="progressButton__progress">
        <span class="progressButton__text">
          <div class="big" id="playerNameDiv${this.playerNumber}">${this.playerName}</div>
          Total time played:
          <div id="totalPlayerTimeDiv${this.playerNumber}">
            00:00:00
          </div>
          <br>
          Time left:
          <div id="playerTimerDiv${this.playerNumber}" class="big">
            30
          </div>
        </span>
      </div>
    </button>`;
  }
}

function setNumberOfPlayers() {
  if (players.length !== 0) {
    numberOfPlayers = parseInt(window.prompt('Enter the number of players: '), 10);
    collapseSettings();
  }

  if (numberOfPlayers < players.length) {
    var playersToRemove = players.length - numberOfPlayers;
    for (var i = 0; i < playersToRemove; i++) {
      newPlayerNode.removeChild(players[players.length - 1].div);
      dropDownFormGroup.removeChild(players[players.length - 1].playerNameFormGroup);
      players.pop();
    }
  }

  for (let i = players.length; i < numberOfPlayers; i++) {
    players[i] = new Player(i, turnLength);
    players[i].div.id = players[i].playerNumber;
    players[i].div.innerHTML = players[i].newButton;
    newPlayerNode.appendChild(players[i].div);
    players[i].totalPlayerTimeDiv = document.getElementById('totalPlayerTimeDiv' + i);
    players[i].playerNameFormGroup.innerHTML = `
      <div class="dropdown-divider"></div>
      <div class="less-big">${players[i].playerName}</div>
      <div class="form-group" id="playerNameFormGroup${players[i].playerNumber}">
        <label for="dropDownFormNameInput${players[i].playerNumber}">Name</label>
        <input type="text" class="form-control" maxlength="12" id="dropDownFormNameInput${players[i].playerNumber}" value="${players[i].playerName}">
        <label for="dropDownFormColorInput${players[i].playerNumber}">Color</label>
        <input type="color" value="${players[i].rgb}" class="form-control" id="dropDownFormColorInput${players[i].playerNumber}">
      </div><br>`;
    dropDownFormGroup.appendChild(players[i].playerNameFormGroup);
    document.querySelector('#player' + i + 'Button').onclick = function () { playerTimer(i); };
  }
}

function registerPlayersSettings() {
  for (const player of players) {
    player.playerName = document.getElementById('dropDownFormNameInput' + player.playerNumber).value;
    player.rgb = document.getElementById('dropDownFormColorInput' + player.playerNumber).value;
    document.getElementById('playerNameDiv' + player.playerNumber).innerHTML = player.playerName;
    document.getElementById('player' + player.playerNumber + 'Button').style.backgroundColor = player.rgb;
    collapseSettings();
  }
}

function toggle(button) {
  if (button.classList.contains('btn-secondary')) {
    button.classList.remove('btn-secondary');
    button.classList.add('btn-outline-secondary');
  } else {
    button.classList.remove('btn-outline-secondary');
    button.classList.add('btn-secondary');
  }
}

function mute() {
  if (isMute === false) {
    isMute = true;
    toggle(muteButton);
  } else {
    isMute = false;
    playBeep();
    toggle(muteButton);
  }
}

function dark() {
  if (isDark === false) {
    isDark = true;
    toggle(darkButton);
    document.body.style.backgroundColor = 'black';
  } else {
    isDark = false;
    toggle(darkButton);
    document.body.style.backgroundColor = 'white';
  }
}

function pause() {
  if (isGamePaused === false) {
    isGamePaused = true;
    toggle(pauseButton);
  } else {
    isGamePaused = false;
    toggle(pauseButton);
  }
}

function collapse() {
  var settingsDiv = document.getElementById('settingsDiv');
  if (isSettingsCollapsed === true) {
    isSettingsCollapsed = false;
    settingsDiv.classList.add('show');
    toggle(settingsButton);
  } else {
    isSettingsCollapsed = true;
    settingsDiv.classList.remove('show');
    toggle(settingsButton);
  }
}

function showDropDown() {
  if (isdropdownCollapsed === true) {
    isdropdownCollapsed = false;
    dropDownForm.classList.add('show');
  } else {
    isdropdownCollapsed = true;
    dropDownForm.classList.remove('show');
  }
}

function playerTimer(id) {
  if (isGameStarted === false || isGamePaused === true) {
    isGameStarted = true;
    isGamePaused = false;
    gameDuration();
  }

  resetTimers();
  playerTurnDuration(id);
}

function playerTurnDuration(id) {
  var delta = (Date.now() - turnStart) / 1000;
  players[id].sec = turnLength - Math.floor(delta);
  playerDuration(id);

  var playerButton = document.getElementById('player' + id + 'Button');
  var progress = (1 - (players[id].sec / turnLength)) * 100;
  playerButton.querySelector('.progressButton__progress').style.height = `${progress}%`;

  var playerTimerDiv = document.getElementById('playerTimerDiv' + id);

  if (isMute === false && (players[id].sec === 10 || players[id].sec <= 3)) {
    playBeep();
    playerTimerDiv.classList.add('text-danger');
  }

  playerTimerDiv.innerHTML = players[id].sec;
  players[id].timeout = setTimeout(playerTurnDuration, 300, id);

  if (players[id].sec <= 0) {
    clearTimeout(players[id].timeout);
    players[id].sec = turnLength;
  }
}

function setTurnLength() {
  turnLength = parseInt(window.prompt('Enter the turn duration in seconds: '), 10);
  collapseSettings();

  for (const player of players) {
    clearTimeout(player.timeout);
    document.getElementById('playerTimerDiv' + player.playerNumber).innerHTML = turnLength;
  }
}

function playerDuration(id) {
  if (isNewTurn === true) {
    isNewTurn = false;
    players[id].totalPlayerSec = parseInt(players[id].delta, 10);
  }

  players[id].delta = ((Date.now() - turnStart) / 1000) + players[id].totalPlayerSec;
  players[id].playerSec = addZero(Math.floor(players[id].delta % 60));
  players[id].playerMin = addZero(Math.floor((players[id].delta / 60) % 3600));
  players[id].playerHr = addZero(Math.floor(players[id].delta / 3600));
  players[id].totalPlayerTimeDiv.innerHTML = players[id].playerHr + ':' + players[id].playerMin + ':' + players[id].playerSec;
}

function gameDuration() {
  if (isTimeStopped === true || isGamePaused === true) {
    isTimeStopped = false;
    isGamePaused = false;
    gameStart = Date.now();
    timerCycle();
  }
}

function timerCycle() {
  if (isTimeStopped === false && isGamePaused === false) {
    var delta = (Date.now() - gameStart) / 1000;
    gameSec = addZero(Math.floor(delta % 60));
    gameMin = addZero(Math.floor((delta / 60) % 3600));
    gameHr = addZero(Math.floor(delta / 3600));
    totalPlayTimeDisplayDiv.innerHTML = gameHr + ':' + gameMin + ':' + gameSec;
    setTimeout(timerCycle, 300);
  }
}

function resetTotalPlayTimer() {
  if (isTimeStopped === false) {
    isTimeStopped = true;
    isGameStarted = false;
    totalPlayTimeDisplayDiv.innerHTML = '00:00:00';

    for (const player of players) {
      player.totalPlayerSec = 0;
      player.delta = 0;
      player.totalPlayerTimeDiv.innerHTML = '00:00:00';
    }

    resetTimers();
  }
}
