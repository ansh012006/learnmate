/**
 * LearnMate AI — Analytics Module
 */
const Analytics = {
    async load() {
        try {
            showLoading('Loading analytics...');
            const data = await Api.getAnalytics();
            this.renderStats(data);
            this.renderCharts(data);
        } catch (error) {
            showToast('Failed to load analytics: ' + error.message, 'error');
        } finally {
            hideLoading();
        }
    },

    renderStats(data) {
        document.getElementById('ana-docs').textContent = data.documents?.total || 0;
        document.getElementById('ana-avg-score').textContent = (data.quizzes?.avg_score || 0) + '%';
        document.getElementById('ana-completion').textContent = (data.tasks?.completion_rate || 0) + '%';
        document.getElementById('ana-chats').textContent = data.learning?.weekly_chats || 0;
    },

    renderCharts(data) {
        // Destroy existing charts
        Object.values(App.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') chart.destroy();
        });
        App.charts = {};

        const chartDefaults = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { font: { size: 11, family: 'Inter' }, color: '#85869b' } } },
            scales: {
                x: { ticks: { color: '#85869b', font: { size: 11 } }, grid: { color: '#f0f0f5' } },
                y: { ticks: { color: '#85869b', font: { size: 11 } }, grid: { color: '#f0f0f5' } },
            },
        };

        // Quiz Performance Chart
        const quizCtx = document.getElementById('quizChart');
        if (quizCtx) {
            const scoreHistory = data.quizzes?.score_history || [];
            App.charts.quiz = new Chart(quizCtx, {
                type: 'bar',
                data: {
                    labels: scoreHistory.map((_, i) => `Quiz ${i + 1}`),
                    datasets: [{
                        label: 'Score (%)',
                        data: scoreHistory.map(s => Math.round(s.score)),
                        backgroundColor: scoreHistory.map(s => s.score >= 70 ? '#6254e8' : s.score >= 40 ? '#8475f5' : '#ef4444'),
                        borderRadius: 6,
                        barPercentage: 0.6,
                    }],
                },
                options: {
                    ...chartDefaults,
                    scales: {
                        ...chartDefaults.scales,
                        y: { ...chartDefaults.scales.y, min: 0, max: 100 },
                    },
                    plugins: {
                        ...chartDefaults.plugins,
                        legend: { display: false },
                    },
                },
            });
        }

        // Task Chart
        const taskCtx = document.getElementById('taskChart');
        if (taskCtx) {
            const tasks = data.tasks || {};
            App.charts.task = new Chart(taskCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Completed', 'Pending', 'In Progress'],
                    datasets: [{
                        data: [
                            tasks.completed || 0,
                            tasks.total - (tasks.completed || 0) - (data.tasks?.in_progress || 0) || 0,
                            data.tasks?.in_progress || 0,
                        ],
                        backgroundColor: ['#6254e8', '#e9eaf2', '#8475f5'],
                        borderWidth: 0,
                        spacing: 4,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { font: { size: 12, family: 'Inter' }, color: '#85869b', padding: 16 },
                        },
                    },
                },
            });
        }
    },
};
