const STORAGE_KEY = 'mindspark-ai-progress-v1';
const ROUNDS_PER_CHALLENGE = 5;
const GAME_DETAILS = {
  memory: {
    title: 'Memory Matrix',
    category: 'MEMORY',
    instruction: 'Watch the tiles light up, then repeat the full sequence in the same order.',
    performanceGroup: 'memory'
  },
  number: {
    title: 'Number Detective',
    category: 'LOGIC',
    instruction: 'Find the number that continues the sequence. Choose the best answer.',
    performanceGroup: 'logic'
  },
  color: {
    title: 'Color Confusion',
    category: 'FOCUS',
    instruction: 'Ignore what the word says. Select the color of the letters instead.',
    performanceGroup: 'focus'
  },
  reflex: {
    title: 'Reflex Challenge',
    category: 'SPEED',
    instruction: 'Wait for the green target to appear, then tap it as quickly as you can.',
    performanceGroup: 'speed'
  },
  pattern: {
    title: 'Pattern Master',
    category: 'LOGIC',
    instruction: 'Study the pattern and choose the item that should come next.',
    performanceGroup: 'logic'
  }
};

const NUMBER_QUESTIONS = {
  easy: [
    { prompt: '2, 4, 6, 8, ?', answer: '10', choices: ['9', '10', '12', '16'], explanation: 'The sequence adds 2 each time.' },
    { prompt: '5, 10, 15, 20, ?', answer: '25', choices: ['22', '24', '25', '30'], explanation: 'Each number increases by 5.' },
    { prompt: '1, 3, 5, 7, ?', answer: '9', choices: ['8', '9', '10', '11'], explanation: 'These are consecutive odd numbers.' },
    { prompt: '10, 9, 8, 7, ?', answer: '6', choices: ['4', '5', '6', '8'], explanation: 'The sequence counts down by 1.' },
    { prompt: '3, 6, 9, 12, ?', answer: '15', choices: ['14', '15', '16', '18'], explanation: 'Each number increases by 3.' }
  ],
  medium: [
    { prompt: '2, 4, 8, 16, ?', answer: '32', choices: ['24', '30', '32', '36'], explanation: 'Each number is doubled.' },
    { prompt: '1, 4, 9, 16, ?', answer: '25', choices: ['20', '24', '25', '36'], explanation: 'These are square numbers: 1², 2², 3², 4², then 5².' },
    { prompt: '3, 6, 11, 18, ?', answer: '27', choices: ['25', '26', '27', '29'], explanation: 'The gaps are +3, +5, +7, then +9.' },
    { prompt: '2, 3, 5, 8, 13, ?', answer: '21', choices: ['18', '20', '21', '22'], explanation: 'Each number is the sum of the two before it.' },
    { prompt: '81, 27, 9, 3, ?', answer: '1', choices: ['0', '1', '2', '1.5'], explanation: 'Each number is divided by 3.' }
  ],
  hard: [
    { prompt: '1, 2, 6, 24, 120, ?', answer: '720', choices: ['600', '620', '720', '840'], explanation: 'Multiply by 2, 3, 4, 5, then 6.' },
    { prompt: '4, 7, 13, 25, 49, ?', answer: '97', choices: ['89', '95', '97', '99'], explanation: 'Each step doubles the previous gap: +3, +6, +12, +24, then +48.' },
    { prompt: '2, 5, 11, 23, 47, ?', answer: '95', choices: ['89', '93', '95', '97'], explanation: 'Double each number and add 1.' },
    { prompt: '1, 8, 27, 64, ?', answer: '125', choices: ['100', '121', '125', '128'], explanation: 'These are cubes: 1³, 2³, 3³, 4³, then 5³.' },
    { prompt: '10, 13, 19, 28, 40, ?', answer: '55', choices: ['52', '53', '55', '57'], explanation: 'The gaps increase by 3: +3, +6, +9, +12, then +15.' }
  ]
};

const PATTERN_QUESTIONS = {
  easy: [
    { items: ['●', '▲', '●', '▲', '●'], answer: '▲', choices: ['●', '▲', '■', '◆'], explanation: 'The circle and triangle alternate.' },
    { items: ['1', '2', '3', '4'], answer: '5', choices: ['4', '5', '6', '7'], explanation: 'The numbers count up by 1.' },
    { items: ['★', '★', '☆', '★', '★'], answer: '☆', choices: ['★', '☆', '●', '▲'], explanation: 'Two filled stars are followed by one outline star.' },
    { items: ['A', 'B', 'C', 'D'], answer: 'E', choices: ['D', 'E', 'F', 'G'], explanation: 'The letters move forward through the alphabet.' },
    { items: ['🔵', '🔴', '🔵', '🔴'], answer: '🔵', choices: ['🔵', '🔴', '🟢', '🟡'], explanation: 'The blue and red circles alternate.' }
  ],
  medium: [
    { items: ['▲', '▲', '●', '▲', '▲', '●'], answer: '▲', choices: ['▲', '●', '■', '◆'], explanation: 'The repeating group is triangle, triangle, circle.' },
    { items: ['2', '4', '8', '16'], answer: '32', choices: ['24', '30', '32', '34'], explanation: 'Each number doubles.' },
    { items: ['◇', '◆', '◇', '◆', '◇'], answer: '◆', choices: ['◇', '◆', '○', '●'], explanation: 'Outline and filled diamonds alternate.' },
    { items: ['1', '1', '2', '3', '5'], answer: '8', choices: ['7', '8', '9', '10'], explanation: 'Each number is the sum of the previous two.' },
    { items: ['A', 'C', 'E', 'G'], answer: 'I', choices: ['H', 'I', 'J', 'K'], explanation: 'The sequence skips one letter each time.' }
  ],
  hard: [
    { items: ['1', '4', '9', '16', '25'], answer: '36', choices: ['30', '35', '36', '49'], explanation: 'These are consecutive square numbers; the next is 6².' },
    { items: ['▲', '●', '●', '▲', '●', '●'], answer: '▲', choices: ['▲', '●', '■', '◆'], explanation: 'The repeating group is one triangle followed by two circles.' },
    { items: ['2', '6', '12', '20', '30'], answer: '42', choices: ['40', '41', '42', '44'], explanation: 'The gaps are +4, +6, +8, +10, then +12.' },
    { items: ['A', 'D', 'G', 'J'], answer: 'M', choices: ['L', 'M', 'N', 'O'], explanation: 'Move forward three letters each time.' },
    { items: ['1', '2', '6', '24', '120'], answer: '720', choices: ['600', '620', '720', '840'], explanation: 'Multiply by 2, 3, 4, 5, then 6.' }
  ]
};

const COLOR_OPTIONS = [
  { name: 'Purple', value: '#b995ff' },
  { name: 'Green', value: '#65e6ba' },
  { name: 'Pink', value: '#f48acb' },
  { name: 'Yellow', value: '#ffd279' },
  { name: 'Blue', value: '#7fa7ff' },
  { name: 'Orange', value: '#ff9c6e' }
];
const COLOR_WORDS = ['PURPLE', 'GREEN', 'PINK', 'YELLOW', 'BLUE', 'ORANGE'];
const DIFFICULTY_SETTINGS = {
  easy: { seconds: 90, points: 100 },
  medium: { seconds: 75, points: 150 },
  hard: { seconds: 60, points: 200 }
};

const defaultProgress = () => ({
  totalPoints: 0,
  bestScore: 0,
  completedChallenges: 0,
  radar: { memory: 0, logic: 0, focus: 0, speed: 0 },
  radarCounts: { memory: 0, logic: 0, focus: 0, speed: 0 }
});

function readProgress() {
  const fallback = defaultProgress();
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return fallback;
    const parsed = JSON.parse(saved);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return fallback;
    const validNumber = value => Number.isFinite(value) && value >= 0;
    const progress = {
      totalPoints: validNumber(parsed.totalPoints) ? Math.floor(parsed.totalPoints) : 0,
      bestScore: validNumber(parsed.bestScore) ? Math.floor(parsed.bestScore) : 0,
      completedChallenges: validNumber(parsed.completedChallenges) ? Math.floor(parsed.completedChallenges) : 0,
      radar: { ...fallback.radar },
      radarCounts: { ...fallback.radarCounts }
    };
    for (const group of Object.keys(fallback.radar)) {
      if (parsed.radar && Number.isFinite(parsed.radar[group])) {
        progress.radar[group] = Math.max(0, Math.min(100, Math.round(parsed.radar[group])));
      }
      if (parsed.radarCounts && validNumber(parsed.radarCounts[group])) {
        progress.radarCounts[group] = Math.floor(parsed.radarCounts[group]);
      }
    }
    return progress;
  } catch (error) {
    console.warn('MindSpark could not read saved progress. Starting with a fresh score.', error);
    showStorageNotice();
    return fallback;
  }
}

function showStorageNotice() {
  const notice = document.getElementById('storageNotice');
  notice.textContent = 'Progress could not be saved in this browser. You can still play, but scores may not persist.';
  notice.hidden = false;
}

const progress = readProgress();
let activeGame = null;
let isDailyChallenge = false;
let lastCompletedGame = 'memory';
let lastCompletedWasDaily = false;
let difficulty = 'medium';
let score = 0;
let roundIndex = 0;
let correctRounds = 0;
let answeredRounds = 0;
let remainingTime = 0;
let timerInterval = null;
let timeoutIds = new Set();
let locked = false;
let memorySequence = [];
let memoryInput = [];
let memoryReady = false;
let reflexReady = false;
let reflexTrialStartedAt = 0;
let reflexResponseTotal = 0;
let reflexResponseCount = 0;
let roundStartedAt = 0;

const dashboard = document.getElementById('dashboard');
const gameScreen = document.getElementById('gameScreen');
const completionScreen = document.getElementById('completionScreen');
const gameContent = document.getElementById('gameContent');
const difficultySelect = document.getElementById('difficultySelect');

function saveProgress() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  } catch (error) {
    console.warn('MindSpark could not save progress in this browser.', error);
    showStorageNotice();
  }
}

function renderDashboard() {
  document.getElementById('totalPoints').textContent = progress.totalPoints.toLocaleString();
  document.getElementById('bestScore').textContent = progress.bestScore.toLocaleString();
  document.getElementById('completedChallenges').textContent = progress.completedChallenges.toLocaleString();
  renderRadar();
}

function renderRadar() {
  const groups = [
    ['memory', 'Memory'],
    ['logic', 'Logic'],
    ['focus', 'Focus'],
    ['speed', 'Speed']
  ];
  const radarScores = document.getElementById('radarScores');
  radarScores.innerHTML = groups.map(([key, label]) => `
    <div class="radar-score-row">
      <span>${label}</span>
      <div class="mini-track" aria-hidden="true"><span style="width: ${progress.radar[key]}%"></span></div>
      <strong>${progress.radar[key]}</strong>
    </div>
  `).join('');
  const center = 110;
  const radius = 90;
  const values = [progress.radar.memory, progress.radar.logic, progress.radar.focus, progress.radar.speed];
  const points = values.map((value, index) => {
    const angle = (-Math.PI / 2) + (index * Math.PI / 2);
    const distance = radius * value / 100;
    return `${center + Math.cos(angle) * distance},${center + Math.sin(angle) * distance}`;
  });
  document.getElementById('radarPolygon').setAttribute('points', points.join(' '));
}

function animateScreen(element) {
  element.classList.remove('screen-enter');
  window.requestAnimationFrame(() => element.classList.add('screen-enter'));
}

function animateDashboard() {
  dashboard.classList.remove('dashboard-enter');
  window.requestAnimationFrame(() => dashboard.classList.add('dashboard-enter'));
}

function initializeScrollAnimations() {
  const revealTargets = document.querySelectorAll(
    '.hero-copy, .hero-art, .stat-card, .section-heading, .game-card, .radar-section'
  );
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion || !('IntersectionObserver' in window)) {
    revealTargets.forEach(target => target.classList.add('is-visible'));
    return;
  }

  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    }
  }, { threshold: 0.12, rootMargin: '0px 0px -24px 0px' });

  revealTargets.forEach(target => {
    target.classList.add('scroll-reveal');
    observer.observe(target);
  });
}

function scheduleTimeout(callback, delay) {
  const timeoutId = window.setTimeout(() => {
    timeoutIds.delete(timeoutId);
    callback();
  }, delay);
  timeoutIds.add(timeoutId);
  return timeoutId;
}

function clearTimers() {
  if (timerInterval !== null) {
    window.clearInterval(timerInterval);
    timerInterval = null;
  }
  for (const timeoutId of timeoutIds) window.clearTimeout(timeoutId);
  timeoutIds.clear();
}

function startGame(gameKey, daily = false) {
  if (!GAME_DETAILS[gameKey]) return;
  clearTimers();
  activeGame = gameKey;
  isDailyChallenge = daily;
  difficulty = difficultySelect.value;
  score = 0;
  roundIndex = 0;
  correctRounds = 0;
  answeredRounds = 0;
  remainingTime = DIFFICULTY_SETTINGS[difficulty].seconds;
  locked = false;
  memorySequence = [];
  memoryInput = [];
  memoryReady = false;
  reflexReady = false;
  reflexResponseTotal = 0;
  reflexResponseCount = 0;
  dashboard.hidden = true;
  completionScreen.hidden = true;
  gameScreen.hidden = false;
  animateScreen(gameScreen);
  document.getElementById('gameCategory').textContent = `${GAME_DETAILS[gameKey].category} TRAINING · ${difficulty.toUpperCase()}`;
  document.getElementById('gameTitle').textContent = GAME_DETAILS[gameKey].title;
  document.getElementById('gameInstruction').textContent = GAME_DETAILS[gameKey].instruction;
  document.getElementById('challengeLabel').textContent = daily ? '✦ DAILY CHALLENGE' : `${difficulty.toUpperCase()} CHALLENGE`;
  updateGameStats();
  timerInterval = window.setInterval(updateTimer, 1000);
  renderRound();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateTimer() {
  if (!activeGame) return;
  remainingTime = Math.max(0, remainingTime - 1);
  document.getElementById('timeLeft').textContent = remainingTime;
  if (remainingTime === 0) finishChallenge(true);
}

function updateGameStats() {
  document.getElementById('timeLeft').textContent = remainingTime;
  document.getElementById('sessionScore').textContent = score.toLocaleString();
  document.getElementById('sessionAccuracy').textContent = answeredRounds ? `${Math.round(correctRounds / answeredRounds * 100)}%` : '—';
  document.getElementById('roundCount').textContent = `${Math.min(roundIndex + 1, ROUNDS_PER_CHALLENGE)} / ${ROUNDS_PER_CHALLENGE}`;
  document.getElementById('roundLabel').textContent = `CHALLENGE ${Math.min(roundIndex + 1, ROUNDS_PER_CHALLENGE)} OF ${ROUNDS_PER_CHALLENGE}`;
  const percentage = Math.round(roundIndex / ROUNDS_PER_CHALLENGE * 100);
  document.getElementById('progressPercent').textContent = `${percentage}%`;
  document.getElementById('progressFill').style.width = `${percentage}%`;
}

function renderRound() {
  if (!activeGame || remainingTime <= 0) return;
  locked = false;
  memoryInput = [];
  updateGameStats();
  if (activeGame === 'memory') renderMemoryRound();
  if (activeGame === 'number') renderChoiceRound(NUMBER_QUESTIONS[difficulty][roundIndex]);
  if (activeGame === 'pattern') renderPatternRound(PATTERN_QUESTIONS[difficulty][roundIndex]);
  if (activeGame === 'color') renderColorRound();
  if (activeGame === 'reflex') startReflexTrial();
}

function renderChoiceRound(question) {
  roundStartedAt = performance.now();
  gameContent.innerHTML = `
    <p class="prompt-label">FIND THE NEXT NUMBER</p>
    <p class="number-prompt">${question.prompt}</p>
    <div class="answer-grid">
      ${question.choices.map(choice => `<button class="answer-button" type="button" data-action="answer" data-answer="${choice}">${choice}</button>`).join('')}
    </div>
    <p class="feedback" aria-live="polite"></p>
  `;
}

function renderPatternRound(question) {
  roundStartedAt = performance.now();
  gameContent.innerHTML = `
    <p class="prompt-label">WHAT COMES NEXT?</p>
    <div class="sequence" aria-label="Pattern: ${question.items.join(', ')}">
      ${question.items.map(item => `<span class="sequence-item">${item}</span>`).join('')}
      <span class="sequence-item" aria-label="missing item">?</span>
    </div>
    <div class="answer-grid">
      ${question.choices.map(choice => `<button class="answer-button" type="button" data-action="answer" data-answer="${choice}">${choice}</button>`).join('')}
    </div>
    <p class="feedback" aria-live="polite"></p>
  `;
}

function renderColorRound() {
  roundStartedAt = performance.now();
  const word = COLOR_WORDS[Math.floor(Math.random() * COLOR_WORDS.length)];
  const ink = COLOR_OPTIONS[Math.floor(Math.random() * COLOR_OPTIONS.length)];
  gameContent.innerHTML = `
    <p class="prompt-label">WHICH COLOR IS THE INK?</p>
    <p class="color-word" style="color: ${ink.value}">${word}</p>
    <div class="color-choices">
      ${COLOR_OPTIONS.map(color => `<button class="color-choice" type="button" data-action="answer" data-answer="${color.value}">${color.name}</button>`).join('')}
    </div>
    <p class="feedback" aria-live="polite"></p>
  `;
  gameContent.dataset.correctAnswer = ink.value;
}

function renderMemoryRound() {
  memorySequence.push(Math.floor(Math.random() * 9));
  memoryInput = [];
  memoryReady = false;
  roundStartedAt = performance.now();
  gameContent.innerHTML = `
    <p class="prompt-label" id="memoryPrompt">WATCH THE LIGHTS</p>
    <div class="memory-grid" aria-label="Memory Matrix with nine tiles">
      ${Array.from({ length: 9 }, (_, index) => `<button class="memory-tile" type="button" data-action="memory-tile" data-tile="${index}" aria-label="Tile ${index + 1}" disabled></button>`).join('')}
    </div>
    <p class="feedback" aria-live="polite">Sequence length: ${memorySequence.length}</p>
  `;
  flashMemorySequence(0);
}

function flashMemorySequence(position) {
  if (!activeGame || activeGame !== 'memory') return;
  if (position >= memorySequence.length) {
    memoryReady = true;
    for (const tile of gameContent.querySelectorAll('.memory-tile')) tile.disabled = false;
    document.getElementById('memoryPrompt').textContent = 'YOUR TURN — REPEAT THE SEQUENCE';
    return;
  }
  const tileIndex = memorySequence[position];
  const tile = gameContent.querySelector(`[data-tile="${tileIndex}"]`);
  if (tile) tile.classList.add('is-lit');
  scheduleTimeout(() => {
    const currentTile = gameContent.querySelector(`[data-tile="${tileIndex}"]`);
    if (currentTile) currentTile.classList.remove('is-lit');
    scheduleTimeout(() => flashMemorySequence(position + 1), 180);
  }, 430);
}

function renderReflexWaiting() {
  reflexReady = false;
  gameContent.innerHTML = `
    <p class="prompt-label">TRIAL ${roundIndex + 1} OF ${ROUNDS_PER_CHALLENGE}</p>
    <p class="reflex-message">Keep your eyes on the box. Don't click until it turns green.</p>
    <div class="reflex-wait">Wait for the green target…</div>
    <p class="reflex-feedback" aria-live="polite"></p>
  `;
}

function startReflexTrial() {
  renderReflexWaiting();
  const delay = 1000 + Math.floor(Math.random() * 2501);
  scheduleTimeout(() => {
    if (!activeGame || activeGame !== 'reflex' || remainingTime <= 0 || locked) return;
    reflexReady = true;
    reflexTrialStartedAt = performance.now();
    gameContent.innerHTML = `
      <p class="prompt-label">TRIAL ${roundIndex + 1} OF ${ROUNDS_PER_CHALLENGE}</p>
      <p class="reflex-message">Now! Tap the target as quickly as you can.</p>
      <button class="reflex-target" type="button" data-action="reflex-target">TAP NOW!</button>
      <p class="reflex-feedback" aria-live="polite"></p>
    `;
  }, delay);
}

function handleAnswer(button) {
  if (locked || !activeGame || activeGame === 'memory' || activeGame === 'reflex') return;
  const selectedAnswer = button.dataset.answer;
  const correctAnswer = activeGame === 'color'
    ? gameContent.dataset.correctAnswer
    : activeGame === 'number'
      ? NUMBER_QUESTIONS[difficulty][roundIndex].answer
      : PATTERN_QUESTIONS[difficulty][roundIndex].answer;
  const question = activeGame === 'number'
    ? NUMBER_QUESTIONS[difficulty][roundIndex]
    : activeGame === 'pattern'
      ? PATTERN_QUESTIONS[difficulty][roundIndex]
      : null;
  const explanation = activeGame === 'color'
    ? `The ink was ${COLOR_OPTIONS.find(color => color.value === correctAnswer).name.toLowerCase()}. The word itself was a distraction.`
    : question.explanation;
  const isCorrect = selectedAnswer === correctAnswer;
  for (const option of gameContent.querySelectorAll('[data-action="answer"]')) {
    option.disabled = true;
    if (option.dataset.answer === correctAnswer) option.classList.add('is-correct');
    if (option === button && !isCorrect) option.classList.add('is-wrong');
  }
  recordRound(isCorrect, explanation, performance.now() - roundStartedAt);
}

function recordRound(isCorrect, explanation, elapsedMilliseconds = 0) {
  if (locked || !activeGame) return;
  locked = true;
  answeredRounds += 1;
  if (isCorrect) {
    correctRounds += 1;
    const basePoints = DIFFICULTY_SETTINGS[difficulty].points;
    const speedBonus = Math.max(0, Math.floor((10000 - elapsedMilliseconds) / 1000) * 5);
    score += basePoints + speedBonus;
  }
  updateGameStats();
  const feedback = gameContent.querySelector('.feedback');
  if (feedback) {
    feedback.textContent = `${isCorrect ? 'Correct!' : 'Not quite.'} ${explanation}`;
    feedback.classList.add(isCorrect ? 'correct' : 'incorrect');
    const nextButton = document.createElement('button');
    nextButton.className = 'button button-primary next-button';
    nextButton.type = 'button';
    nextButton.dataset.action = 'next';
    nextButton.textContent = roundIndex === ROUNDS_PER_CHALLENGE - 1 ? 'Finish challenge' : 'Next round';
    feedback.insertAdjacentElement('afterend', nextButton);
  }
}

function handleMemoryTile(tile) {
  if (!memoryReady || locked || !activeGame || activeGame !== 'memory') return;
  const selectedTile = Number(tile.dataset.tile);
  tile.classList.add('is-lit');
  scheduleTimeout(() => tile.classList.remove('is-lit'), 180);
  const expectedTile = memorySequence[memoryInput.length];
  memoryInput.push(selectedTile);
  if (selectedTile !== expectedTile) {
    memoryReady = false;
    for (const item of gameContent.querySelectorAll('.memory-tile')) item.disabled = true;
    recordRound(false, `The sequence was ${memorySequence.map(index => index + 1).join(', ')}. Watch carefully and try again.`);
    return;
  }
  if (memoryInput.length === memorySequence.length) {
    memoryReady = false;
    for (const item of gameContent.querySelectorAll('.memory-tile')) item.disabled = true;
    recordRound(true, `You repeated all ${memorySequence.length} tiles in order.`, performance.now() - roundStartedAt);
  }
}

function handleReflexTarget() {
  if (!reflexReady || locked || !activeGame || activeGame !== 'reflex') return;
  reflexReady = false;
  locked = true;
  const reactionMilliseconds = Math.round(performance.now() - reflexTrialStartedAt);
  reflexResponseTotal += reactionMilliseconds;
  reflexResponseCount += 1;
  answeredRounds += 1;
  correctRounds += 1;
  const speedPoints = Math.max(20, Math.round(300 - reactionMilliseconds / 10));
  score += speedPoints;
  updateGameStats();
  const nextTrial = roundIndex + 1;
  gameContent.innerHTML = `
    <p class="prompt-label">TRIAL ${nextTrial} OF ${ROUNDS_PER_CHALLENGE}</p>
    <div class="completion-burst" aria-hidden="true">ϟ</div>
    <p class="reflex-feedback correct">Your reaction time: <strong>${reactionMilliseconds} ms</strong> · +${speedPoints} points</p>
    ${nextTrial < ROUNDS_PER_CHALLENGE ? '<p class="reflex-feedback">Get ready for the next signal…</p>' : ''}
  `;
  roundIndex += 1;
  updateGameStats();
  if (roundIndex >= ROUNDS_PER_CHALLENGE) {
    scheduleTimeout(() => finishChallenge(false), 700);
  } else {
    scheduleTimeout(() => {
      if (!activeGame || remainingTime <= 0) return;
      locked = false;
      startReflexTrial();
    }, 750);
  }
}

function goToNextRound() {
  if (!locked || !activeGame) return;
  if (roundIndex >= ROUNDS_PER_CHALLENGE - 1) {
    roundIndex += 1;
    finishChallenge(false);
    return;
  }
  roundIndex += 1;
  renderRound();
}

function finishChallenge(timeExpired) {
  if (!activeGame) return;
  clearTimers();
  reflexReady = false;
  memoryReady = false;
  const gameKey = activeGame;
  lastCompletedGame = gameKey;
  lastCompletedWasDaily = isDailyChallenge;
  activeGame = null;
  const accuracy = answeredRounds ? Math.round(correctRounds / answeredRounds * 100) : 0;
  progress.totalPoints += score;
  progress.bestScore = Math.max(progress.bestScore, score);
  progress.completedChallenges += 1;
  const group = GAME_DETAILS[gameKey].performanceGroup;
  const performanceScore = gameKey === 'reflex' && reflexResponseCount
    ? Math.max(0, Math.min(100, Math.round(100 - (reflexResponseTotal / reflexResponseCount) / 30)))
    : accuracy;
  const previousCount = progress.radarCounts[group];
  progress.radar[group] = Math.round((progress.radar[group] * previousCount + performanceScore) / (previousCount + 1));
  progress.radarCounts[group] = previousCount + 1;
  saveProgress();
  renderDashboard();
  gameScreen.hidden = true;
  completionScreen.hidden = false;
  animateScreen(completionScreen);
  document.getElementById('completionTitle').textContent = timeExpired ? 'Time is up!' : 'Nice work!';
  document.getElementById('completionMessage').textContent = timeExpired
    ? `You earned ${score.toLocaleString()} points before the timer ran out. Every round is practice.`
    : `${GAME_DETAILS[gameKey].title} complete${isDailyChallenge ? ' — daily challenge complete' : ''}. Keep that momentum going!`;
  document.getElementById('finalScore').textContent = score.toLocaleString();
  document.getElementById('finalAccuracy').textContent = `${accuracy}%`;
  document.getElementById('finalBestScore').textContent = progress.bestScore.toLocaleString();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function home() {
  clearTimers();
  activeGame = null;
  reflexReady = false;
  memoryReady = false;
  gameScreen.hidden = true;
  completionScreen.hidden = true;
  dashboard.hidden = false;
  renderDashboard();
  animateDashboard();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function dailyGameForToday() {
  const now = new Date();
  const dateKey = `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;
  const dateSeed = dateKey.split('').reduce((sum, character) => sum + character.charCodeAt(0), 0);
  return Object.keys(GAME_DETAILS)[dateSeed % Object.keys(GAME_DETAILS).length];
}

document.addEventListener('click', event => {
  const button = event.target.closest('[data-action]');
  if (!button || button.disabled) return;
  const action = button.dataset.action;
  if (action === 'home') home();
  if (action === 'start') startGame(button.dataset.game);
  if (action === 'daily') startGame(dailyGameForToday(), true);
  if (action === 'restart' && !activeGame) startGame(lastCompletedGame, lastCompletedWasDaily);
  if (action === 'answer') handleAnswer(button);
  if (action === 'next') goToNextRound();
  if (action === 'memory-tile') handleMemoryTile(button);
  if (action === 'reflex-target') handleReflexTarget();
});

document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !dashboard.hidden) return;
  if (event.key === 'Escape' && !gameScreen.hidden) home();
});

difficultySelect.addEventListener('change', () => {
  difficulty = difficultySelect.value;
});

renderDashboard();
animateDashboard();
initializeScrollAnimations();