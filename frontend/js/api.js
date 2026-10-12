const API_BASE = window.__API_BASE__ || window.location.origin;

const Api = {
    async request(endpoint, options = {}) {
        const url = `${API_BASE}/api/v1${endpoint}`;
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 90000);
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
            signal: controller.signal,
        };

        if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            clearTimeout(timer);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            clearTimeout(timer);
            if (error.name === 'AbortError') throw new Error('Request timed out — server may be waking up, please retry.');
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    },

    get(endpoint) { return this.request(endpoint, { method: 'GET' }); },
    post(endpoint, body) { return this.request(endpoint, { method: 'POST', body }); },
    put(endpoint, body) { return this.request(endpoint, { method: 'PUT', body }); },
    delete(endpoint) { return this.request(endpoint, { method: 'DELETE' }); },

    async upload(endpoint, formData, onProgress) {
        const url = `${API_BASE}/api/v1${endpoint}`;
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', url);
            xhr.upload.onprogress = (e) => {
                if (onProgress && e.lengthComputable) onProgress((e.loaded / e.total) * 100);
            };
            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try { resolve(JSON.parse(xhr.responseText)); }
                    catch { resolve(xhr.responseText); }
                } else {
                    try { reject(new Error(JSON.parse(xhr.responseText).detail || `Upload failed (${xhr.status})`)); }
                    catch { reject(new Error(`Upload failed (${xhr.status})`)); }
                }
            };
            xhr.onerror = () => reject(new Error('Network error during upload'));
            xhr.send(formData);
        });
    },

    async health() { return this.get('/health'); },
    async chatAsk(message, sessionId, useDocuments) {
        return this.post('/chat/ask', { message, session_id: sessionId, use_documents: useDocuments });
    },
    async chatClear(sessionId) { return this.post('/chat/clear', { session_id: sessionId }); },
    async chatHistory(sessionId) { return this.get(`/chat/history/${encodeURIComponent(sessionId)}`); },
    async listDocuments() { return this.get('/documents/'); },
    async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);
        return this.upload('/documents/upload', formData);
    },
    async deleteDocument(docId) { return this.delete(`/documents/${docId}`); },
    async listPyqAnalyses() { return this.get('/pyq/'); },
    async uploadPyq(file) {
        const formData = new FormData();
        formData.append('file', file);
        return this.upload('/pyq/upload', formData);
    },
    async generateQuiz(topic, numQuestions, difficulty, sourceDocIds) {
        return this.post('/quiz/generate', { topic, num_questions: numQuestions, difficulty, source_document_ids: sourceDocIds });
    },
    async submitQuiz(quizId, answers) { return this.post('/quiz/submit', { quiz_id: quizId, answers }); },
    async quizHistory() { return this.get('/quiz/history'); },
    async listTasks(status) {
        const qs = status ? `?status=${status}` : '';
        return this.get(`/planner/tasks${qs}`);
    },
    async createTask(task) { return this.post('/planner/tasks', task); },
    async updateTask(taskId, task) { return this.put(`/planner/tasks/${taskId}`, task); },
    async deleteTask(taskId) { return this.delete(`/planner/tasks/${taskId}`); },
    async plannerSummary() { return this.get('/planner/summary'); },
    async getAnalytics() { return this.get('/analytics/dashboard'); },
};

window.Api = Api;
