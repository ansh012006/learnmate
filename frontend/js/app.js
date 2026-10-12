/**
 * LearnMate AI — App Initialization & Navigation
 */
const App = {
    currentPage: 'dashboard',
    chatSessionId: 'session-' + Date.now(),
    currentQuiz: null,
    charts: {},

    init() {
        this.bindNavigation();
        this.bindSidebar();
        this.loadDashboard();
    },

    bindNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                const page = e.currentTarget.dataset.page;
                this.navigateTo(page);
            });
        });
    },

    bindSidebar() {
        const toggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');

        if (toggle) {
            toggle.addEventListener('click', () => {
                sidebar.classList.toggle('open');
                overlay.classList.toggle('visible');
            });
        }

        if (overlay) {
            overlay.addEventListener('click', () => {
                sidebar.classList.remove('open');
                overlay.classList.remove('visible');
            });
        }
    },

    navigateTo(page) {
        this.currentPage = page;

        // Update nav active state
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.page === page);
        });

        // Show/hide page sections
        document.querySelectorAll('.page-section').forEach(section => {
            section.classList.toggle('active', section.id === `page-${page}`);
        });

        // Close mobile sidebar
        document.getElementById('sidebar').classList.remove('open');
        document.getElementById('sidebarOverlay').classList.remove('visible');

        // Load page data
        switch (page) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'chat':
                Chat.loadHistory();
                break;
            case 'documents':
                Documents.load();
                break;
            case 'pyq':
                PYQ.load();
                break;
            case 'quiz':
                Quiz.reset();
                break;
            case 'planner':
                Planner.load();
                break;
            case 'analytics':
                Analytics.load();
                break;
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    async loadDashboard() {
        try {
            const analytics = await Api.getAnalytics();
            const docs = analytics.documents || {};
            const pyq = analytics.pyq || {};
            const quizzes = analytics.quizzes || {};
            const tasks = analytics.tasks || {};
            const learning = analytics.learning || {};

            animateValue('stat-docs', docs.total || 0);
            animateValue('stat-questions', pyq.total_questions || 0);
            animateValue('stat-quizzes', quizzes.attempts || 0);
            animateValue('stat-tasks', tasks.completed || 0);

            // Activity feed
            const activityEl = document.getElementById('dashboard-activity');
            const activities = analytics.recent_activity || [];

            if (activities.length === 0) {
                activityEl.innerHTML = '<div class="empty-state"><p>No activity yet. Start by uploading documents or asking questions!</p></div>';
            } else {
                activityEl.innerHTML = activities.map(a => `
                    <div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);">
                        <div style="width:8px;height:8px;border-radius:50%;background:var(--primary);flex-shrink:0;"></div>
                        <div>
                            <div style="font-size:13px;color:var(--text);">${escapeHtml(a.content)}</div>
                            <div style="font-size:11px;color:var(--text-muted);">${formatDate(a.created_at)}</div>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Dashboard load error:', error);
        }
    },
};

// Utility: Animate number counting
function animateValue(elementId, endValue) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const duration = 600;
    const start = parseInt(el.textContent) || 0;
    const range = endValue - start;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(start + range * eased);
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// Utility: Format date
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility: Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Navigation helper exposed globally
function navigateTo(page) {
    App.navigateTo(page);
}

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = '0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Loading overlay
function showLoading(text = 'Processing...') {
    const overlay = document.getElementById('loadingOverlay');
    document.getElementById('loadingText').textContent = text;
    overlay.classList.add('visible');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('visible');
}

// Modal helpers
function openModal(id) {
    document.getElementById(id).classList.add('visible');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('visible');
}

// Initialize app on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();

    // Initialize feature modules
    initDocuments();
    initPYQ();

    // Auto-resize textarea
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    }
});
