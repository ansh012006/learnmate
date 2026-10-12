/**
 * LearnMate AI — Documents Module
 */
const Documents = {
    async load() {
        try {
            showLoading('Loading documents...');
            const result = await Api.listDocuments();
            this.render(result.documents, result.total);
        } catch (error) {
            showToast('Failed to load documents: ' + error.message, 'error');
        } finally {
            hideLoading();
        }
    },

    render(documents, total) {
        const listEl = document.getElementById('docList');
        const countEl = document.getElementById('docCount');

        countEl.textContent = `${total} file${total !== 1 ? 's' : ''}`;

        if (!documents || documents.length === 0) {
            listEl.innerHTML = '<div class="empty-state"><p>No documents uploaded yet. Upload your study materials to get started.</p></div>';
            return;
        }

        listEl.innerHTML = documents.map(doc => {
            const ext = doc.file_type.toLowerCase();
            const iconClass = ext === 'pdf' ? 'pdf' : ext === 'docx' || ext === 'doc' ? 'docx' : 'txt';
            const statusClass = doc.status === 'ready' ? 'ready' : doc.status === 'error' ? 'error' : 'processing';

            return `
                <div class="doc-item">
                    <div class="doc-icon ${iconClass}">${ext}</div>
                    <div class="doc-info">
                        <div class="doc-name">${escapeHtml(doc.filename)}</div>
                        <div class="doc-meta">${formatFileSize(doc.file_size)} · ${doc.chunk_count || 0} chunks</div>
                    </div>
                    <span class="doc-status ${statusClass}">${doc.status}</span>
                    <button class="btn btn-outline btn-sm" onclick="Documents.remove(${doc.id}, '${escapeHtml(doc.filename)}')" title="Delete">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
            `;
        }).join('');
    },

    async upload(file) {
        if (!file) return;

        const validTypes = ['.pdf', '.txt', '.docx', '.doc'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!validTypes.includes(ext)) {
            showToast('Invalid file type. Use PDF, TXT, or DOCX.', 'error');
            return;
        }

        try {
            showLoading('Uploading and processing document...');
            const result = await Api.uploadDocument(file);
            showToast(`Document "${result.filename}" uploaded successfully!`, 'success');

            // Update status periodically
            this.pollStatus(result.id);
        } catch (error) {
            hideLoading();
            showToast('Upload failed: ' + error.message, 'error');
        }
    },

    async pollStatus(docId) {
        const check = async () => {
            try {
                const result = await Api.listDocuments();
                const doc = result.documents.find(d => d.id === docId);
                if (doc) {
                    this.render(result.documents, result.total);
                    if (doc.status === 'ready') {
                        hideLoading();
                        showToast('Document processed successfully!', 'success');
                    } else if (doc.status === 'error') {
                        hideLoading();
                        showToast('Processing failed: ' + (doc.error_message || 'Unknown error'), 'error');
                    } else {
                        setTimeout(check, 2000);
                    }
                }
            } catch {
                setTimeout(check, 3000);
            }
        };
        setTimeout(check, 2000);
    },

    async remove(docId, filename) {
        if (!confirm(`Delete "${filename}" and its embeddings?`)) return;

        try {
            await Api.deleteDocument(docId);
            showToast('Document deleted', 'success');
            this.load();
        } catch (error) {
            showToast('Delete failed: ' + error.message, 'error');
        }
    },
};

function initDocuments() {
    const uploadArea = document.getElementById('docUploadArea');
    const fileInput = document.getElementById('docFileInput');

    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) Documents.upload(file);
        });

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) Documents.upload(file);
            fileInput.value = '';
        });
    }
}
