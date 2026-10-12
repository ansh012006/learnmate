/**
 * LearnMate AI — Quiz Module
 */
const Quiz = {
    currentQuizId: null,
    userAnswers: [],

    reset() {
        document.getElementById('quizSetup').classList.remove('hidden');
        document.getElementById('quizActive').classList.add('hidden');
        document.getElementById('quizResult').classList.add('hidden');
        this.currentQuizId = null;
        this.userAnswers = [];
    },

    async generate() {
        const topic = document.getElementById('quizTopic').value.trim();
        if (!topic) {
            showToast('Please enter a topic', 'warning');
            return;
        }

        const numQuestions = parseInt(document.getElementById('quizNumQuestions').value);
        const difficulty = document.getElementById('quizDifficulty').value;

        try {
            showLoading('Generating quiz questions...');
            const result = await Api.generateQuiz(topic, numQuestions, difficulty, []);

            this.currentQuizId = result.id;
            this.userAnswers = new Array(result.questions.length).fill(-1);

            this.renderQuestions(result.questions);
            document.getElementById('quizSetup').classList.add('hidden');
            document.getElementById('quizActive').classList.remove('hidden');
            document.getElementById('quizProgress').textContent =
                `${result.questions.length} questions · ${difficulty} · ${topic}`;

            showToast('Quiz generated!', 'success');
        } catch (error) {
            showToast('Failed to generate quiz: ' + error.message, 'error');
        } finally {
            hideLoading();
        }
    },

    renderQuestions(questions) {
        const container = document.getElementById('quizQuestions');
        container.innerHTML = questions.map((q, i) => `
            <div class="quiz-question" id="quiz-q-${i}">
                <div class="quiz-question-number">Question ${i + 1} of ${questions.length}</div>
                <div class="quiz-question-text">${escapeHtml(q.question)}</div>
                <div class="quiz-options">
                    ${q.options.map((opt, j) => `
                        <label class="quiz-option" onclick="Quiz.selectOption(${i}, ${j})">
                            <input type="radio" name="q-${i}" value="${j}" ${this.userAnswers[i] === j ? 'checked' : ''}>
                            <span>${escapeHtml(opt)}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
        `).join('');
    },

    selectOption(questionIndex, optionIndex) {
        this.userAnswers[questionIndex] = optionIndex;

        // Update visual state
        const qEl = document.getElementById(`quiz-q-${questionIndex}`);
        if (qEl) {
            qEl.querySelectorAll('.quiz-option').forEach((opt, i) => {
                opt.classList.toggle('selected', i === optionIndex);
            });
        }
    },

    async submit() {
        if (this.userAnswers.some(a => a === -1)) {
            showToast('Please answer all questions', 'warning');
            return;
        }

        try {
            showLoading('Submitting quiz...');
            const result = await Api.submitQuiz(this.currentQuizId, this.userAnswers);

            const percentage = Math.round(result.score);
            const circleClass = percentage >= 70 ? 'good' : percentage >= 40 ? 'average' : 'poor';

            document.getElementById('quizActive').classList.add('hidden');
            document.getElementById('quizResult').classList.remove('hidden');
            document.getElementById('quizResultCard').innerHTML = `
                <div class="quiz-score-circle ${circleClass}">${percentage}%</div>
                <h3 style="margin-bottom:8px;font-size:20px;">${percentage >= 70 ? 'Great Job!' : percentage >= 40 ? 'Good Effort!' : 'Keep Practicing!'}</h3>
                <p class="text-muted" style="margin-bottom:20px;">
                    You got <strong>${result.correct_answers}</strong> out of <strong>${result.total_questions}</strong> questions correct.
                </p>
                <div style="display:flex;gap:10px;justify-content:center;">
                    <button class="btn btn-primary" onclick="Quiz.reset()">New Quiz</button>
                    <button class="btn btn-outline" onclick="navigateTo('analytics')">View Analytics</button>
                </div>
            `;

            showToast(`Quiz completed! Score: ${percentage}%`, 'success');
        } catch (error) {
            showToast('Submission failed: ' + error.message, 'error');
        } finally {
            hideLoading();
        }
    },

    end() {
        if (confirm('End this quiz? Your progress will be lost.')) {
            this.reset();
        }
    },
};

function generateQuiz() {
    Quiz.generate();
}

function submitQuiz() {
    Quiz.submit();
}

function endQuiz() {
    Quiz.end();
}
