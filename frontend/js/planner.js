/**
 * LearnMate AI — Study Planner Module
 */
const Planner = {
    editingId: null,

    async load(status = 'all') {
        try {
            showLoading('Loading tasks...');
            const [tasks, summary] = await Promise.all([
                Api.listTasks(status === 'all' ? null : status),
                Api.plannerSummary(),
            ]);

            this.renderTasks(tasks);
            this.renderSummary(summary);
        } catch (error) {
            showToast('Failed to load tasks: ' + error.message, 'error');
        } finally {
            hideLoading();
        }
    },

    renderTasks(tasks) {
        const container = document.getElementById('taskList');

        if (!tasks || tasks.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No tasks found. Create your first study task!</p></div>';
            return;
        }

        // Sort: high priority first, then pending, then by deadline
        const sorted = [...tasks].sort((a, b) => {
            const priorityOrder = { high: 0, medium: 1, low: 2 };
            const statusOrder = { pending: 0, in_progress: 1, completed: 2 };

            if (a.status !== b.status) return statusOrder[a.status] - statusOrder[b.status];
            return priorityOrder[a.priority] - priorityOrder[b.priority];
        });

        container.innerHTML = sorted.map(task => {
            const isCompleted = task.status === 'completed';
            const isOverdue = task.deadline && !isCompleted && new Date(task.deadline) < new Date();

            return `
                <div class="task-item ${isCompleted ? 'completed' : ''}" id="task-${task.id}">
                    <button class="task-checkbox ${isCompleted ? 'checked' : ''}" onclick="Planner.toggleStatus(${task.id}, '${task.status}')" title="${isCompleted ? 'Mark as incomplete' : 'Mark as complete'}">
                        ${isCompleted ? '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>' : ''}
                    </button>
                    <div class="task-info">
                        <div class="task-title">${escapeHtml(task.title)}</div>
                        <div class="task-meta">${escapeHtml(task.subject)}${task.topic ? ' · ' + escapeHtml(task.topic) : ''}${task.estimated_hours ? ' · ' + task.estimated_hours + 'h' : ''}${isOverdue ? ' · <span style="color:var(--danger);">Overdue</span>' : ''}</div>
                    </div>
                    <span class="priority-badge priority-${task.priority}">${task.priority}</span>
                    <button class="btn btn-outline btn-sm" onclick="Planner.edit(${task.id})" title="Edit">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    </button>
                    <button class="btn btn-outline btn-sm" onclick="Planner.remove(${task.id})" title="Delete" style="color:var(--danger);">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
            `;
        }).join('');
    },

    renderSummary(summary) {
        const el = document.getElementById('plannerSummary');
        if (!summary || summary.total === 0) {
            el.innerHTML = '<div class="empty-state"><p>No tasks yet. Add your first study task!</p></div>';
            return;
        }

        el.innerHTML = `
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;">
                <div class="text-center" style="padding:12px;background:var(--page-bg);border-radius:8px;">
                    <div style="font-size:20px;font-weight:700;color:var(--text);">${summary.pending}</div>
                    <div style="font-size:11px;color:var(--text-muted);">Pending</div>
                </div>
                <div class="text-center" style="padding:12px;background:var(--lavender);border-radius:8px;">
                    <div style="font-size:20px;font-weight:700;color:var(--primary);">${summary.in_progress}</div>
                    <div style="font-size:11px;color:var(--text-muted);">In Progress</div>
                </div>
                <div class="text-center" style="padding:12px;background:#dcfce7;border-radius:8px;">
                    <div style="font-size:20px;font-weight:700;color:#16a34a;">${summary.completed}</div>
                    <div style="font-size:11px;color:var(--text-muted);">Completed</div>
                </div>
            </div>
            <div style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                    <span>Completion Rate</span><strong>${summary.completion_rate}%</strong>
                </div>
                <div style="height:8px;background:var(--page-bg);border-radius:4px;overflow:hidden;">
                    <div style="height:100%;width:${summary.completion_rate}%;background:linear-gradient(90deg,var(--hero-start),var(--hero-end));border-radius:4px;transition:width 0.6s ease;"></div>
                </div>
            </div>
            ${summary.upcoming && summary.upcoming.length > 0 ? `
                <div style="font-size:12px;color:var(--text-muted);margin-top:12px;">
                    <strong>Upcoming deadlines:</strong>
                    ${summary.upcoming.map(t => escapeHtml(t.title)).join(', ')}
                </div>
            ` : ''}
        `;
    },

    async add() {
        const title = document.getElementById('taskTitle').value.trim();
        const subject = document.getElementById('taskSubject').value.trim();
        const topic = document.getElementById('taskTopic').value.trim();
        const priority = document.getElementById('taskPriority').value;
        const deadline = document.getElementById('taskDeadline').value;
        const estimated_hours = parseFloat(document.getElementById('taskHours').value) || 1;

        if (!title || !subject) {
            showToast('Title and Subject are required', 'warning');
            return;
        }

        try {
            showLoading('Adding task...');
            await Api.createTask({ title, subject, topic, priority, deadline: deadline || null, estimated_hours });

            // Clear form
            document.getElementById('taskTitle').value = '';
            document.getElementById('taskSubject').value = '';
            document.getElementById('taskTopic').value = '';
            document.getElementById('taskDeadline').value = '';

            showToast('Task added!', 'success');
            this.load();
        } catch (error) {
            showToast('Failed to add task: ' + error.message, 'error');
        } finally {
            hideLoading();
        }
    },

    async toggleStatus(taskId, currentStatus) {
        const newStatus = currentStatus === 'completed' ? 'pending' : 'completed';
        try {
            await Api.updateTask(taskId, { status: newStatus });
            this.load();
        } catch (error) {
            showToast('Failed to update task', 'error');
        }
    },

    edit(taskId) {
        this.editingId = taskId;
        document.getElementById('editTaskId').value = taskId;
        document.getElementById('taskModalTitle').textContent = 'Edit Task';
        openModal('taskModal');
    },

    async saveEdit() {
        const taskId = parseInt(document.getElementById('editTaskId').value);
        const title = document.getElementById('editTaskTitle').value.trim();
        const status = document.getElementById('editTaskStatus').value;

        try {
            await Api.updateTask(taskId, { title: title || undefined, status });
            closeModal('taskModal');
            this.load();
            showToast('Task updated', 'success');
        } catch (error) {
            showToast('Update failed: ' + error.message, 'error');
        }
    },

    async remove(taskId) {
        if (!confirm('Delete this task?')) return;
        try {
            await Api.deleteTask(taskId);
            showToast('Task deleted', 'success');
            this.load();
        } catch (error) {
            showToast('Delete failed: ' + error.message, 'error');
        }
    },
};

function addTask() {
    Planner.add();
}

function saveTaskEdit() {
    Planner.saveEdit();
}
