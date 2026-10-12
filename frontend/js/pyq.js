/**
 * LearnMate AI — PYQ Analyzer Module
 */
const PYQ = {
    async load() {
        try {
            const result = await Api.listPyqAnalyses();
            this.renderResults(result.analyses);
        } catch (error) {
            console.error('PYQ load error:', error);
        }
    },

    async upload(file) {
        if (!file || file.type !== 'application/pdf') {
            showToast('Please upload a PDF file', 'error');
            return;
        }

        try {
            showLoading('Analyzing question paper...');
            const result = await Api.uploadPyq(file);
            hideLoading();

            if (result.status === 'error') {
                showToast('Analysis failed: ' + (result.error_message || 'Unknown error'), 'error');
                return;
            }

            showToast(`Analyzed ${result.question_count} questions!`, 'success');
            this.renderResult(result);
        } catch (error) {
            hideLoading();
            showToast('Upload failed: ' + error.message, 'error');
        }
    },

    renderResults(analyses) {
        if (!analyses || analyses.length === 0) return;

        const latest = analyses[0];
        if (latest.status !== 'completed') return;
        this.renderResult(latest);
    },

    renderResult(result) {
        // Hide empty state
        const resultsEl = document.getElementById('pyqResults');
        resultsEl.querySelector('.empty-state')?.remove();

        // Question count
        resultsEl.innerHTML = `
            <div class="card-header">
                <div>
                    <div class="card-title">${escapeHtml(result.filename)}</div>
                    <div class="card-subtitle">${result.question_count} questions analyzed</div>
                </div>
                <span class="doc-status ${result.status === 'completed' ? 'ready' : 'processing'}">${result.status}</span>
            </div>
            <div style="font-size:13px;color:var(--text-muted);">
                Click on topics to see related questions.
            </div>
        `;

        // Topics
        const topicsCard = document.getElementById('pyqTopicsCard');
        const topicsEl = document.getElementById('pyqTopics');
        if (result.topics && result.topics.length > 0) {
            topicsCard.style.display = 'block';
            const maxCount = Math.max(...result.topics.map(t => t.count || 1));

            topicsEl.innerHTML = result.topics.slice(0, 10).map(topic => {
                const pct = Math.round((topic.count / maxCount) * 100);
                const questions = (topic.questions || []).slice(0, 2);
                return `
                    <div class="topic-bar">
                        <div class="topic-name">${escapeHtml(topic.name)}</div>
                        <div class="topic-bar-track">
                            <div class="topic-bar-fill" style="width:${pct}%"></div>
                        </div>
                        <div class="topic-count">${topic.count}</div>
                    </div>
                    ${questions.length > 0 ? `
                        <div style="padding:4px 0 4px 172px;font-size:11px;color:var(--text-muted);">
                            e.g., ${questions.map(q => escapeHtml(q.substring(0, 80))).join(' | ')}
                        </div>
                    ` : ''}
                `;
            }).join('');
        } else {
            topicsCard.style.display = 'none';
        }

        // Patterns
        const patternsCard = document.getElementById('pyqPatternsCard');
        const patternsEl = document.getElementById('pyqPatterns');
        if (result.patterns && Object.keys(result.patterns).length > 0) {
            patternsCard.style.display = 'block';
            patternsEl.innerHTML = Object.entries(result.patterns).map(([key, value]) => {
                const icons = {
                    define: '📖', explain: '📝', compare: '⚖️', differentiate: '🔍',
                    short_answer: '📋', long_answer: '📄', numerical: '🔢', diagram: '✏️'
                };
                return `
                    <div class="pattern-card">
                        <div class="pattern-value">${value}</div>
                        <div class="pattern-label">${icons[key] || ''} ${key.replace('_', ' ')}</div>
                    </div>
                `;
            }).join('');
        } else {
            patternsCard.style.display = 'none';
        }
    },
};

function initPYQ() {
    const uploadArea = document.getElementById('pyqUploadArea');
    const fileInput = document.getElementById('pyqFileInput');

    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) PYQ.upload(file);
        });
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) PYQ.upload(file);
            fileInput.value = '';
        });
    }
}
