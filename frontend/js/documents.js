
const DOCUMENT_API_URL = "http://127.0.0.1:8000/api/documents";

document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("document-file-input");
    const uploadTrigger = document.getElementById("upload-trigger");
    const browseButton = document.getElementById("browse-files-btn");
    const uploadArea = document.getElementById("upload-area");
    const uploadStatus = document.getElementById("upload-status");
    const documentsList = document.getElementById("documents-list");
    const refreshButton = document.getElementById("refresh-documents-btn");

    if (!fileInput || !documentsList) {
        return;
    }

    // Open the file picker.
    function openFilePicker() {
        fileInput.click();
    }

    uploadTrigger?.addEventListener("click", openFilePicker);
    browseButton?.addEventListener("click", openFilePicker);

    // Display upload status.
    function showStatus(message, type = "info") {
        uploadStatus.textContent = message;
        uploadStatus.className = `upload-status ${type}`;
    }

    // Format file size.
    function formatFileSize(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) {
            return `${(bytes / 1024).toFixed(1)} KB`;
        }
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }

    // Load all uploaded documents.
    async function loadDocuments() {
        documentsList.replaceChildren();

        const loading = document.createElement("div");
        loading.className = "documents-empty";
        loading.textContent = "Loading documents...";
        documentsList.appendChild(loading);

        try {
            const response = await fetch(`${DOCUMENT_API_URL}/`);

            if (!response.ok) {
                throw new Error("Unable to load documents.");
            }

            const documents = await response.json();

            documentsList.replaceChildren();

            if (documents.length === 0) {
                const empty = document.createElement("div");
                empty.className = "documents-empty";
                empty.textContent = "No documents uploaded yet. Upload your first study material!";
                documentsList.appendChild(empty);
                return;
            }

            documents.forEach((document) => {
                createDocumentCard(document);
            });

        } catch (error) {
            console.error("Document loading error:", error);

            documentsList.replaceChildren();

            const errorMessage = document.createElement("div");
            errorMessage.className = "documents-empty";
            errorMessage.textContent =
                "Could not load documents. Check your backend connection.";

            documentsList.appendChild(errorMessage);
        }
    }

    // Create a card for each document.
    function createDocumentCard(documentData) {
        const card = document.createElement("div");
        card.className = "document-card";

        const icon = document.createElement("div");
        icon.className = "document-card-icon";
        icon.textContent = "📄";

        const name = document.createElement("h4");
        name.textContent = documentData.original_filename;

        const type = document.createElement("p");
        type.textContent = `Type: ${documentData.file_type}`;

        const size = document.createElement("p");
        size.textContent = `Size: ${formatFileSize(documentData.file_size)}`;

        const segments = document.createElement("p");
        segments.textContent = `Segments: ${documentData.segment_count}`;

        const status = document.createElement("p");
        status.textContent = `Status: ${documentData.extraction_status}`;

        const uploaded = document.createElement("p");
        uploaded.textContent = `Uploaded: ${documentData.uploaded_at}`;

        const actions = document.createElement("div");
        actions.className = "document-card-actions";

        const deleteButton = document.createElement("button");
        deleteButton.className = "delete-document-btn";
        deleteButton.type = "button";
        deleteButton.textContent = "Delete";

        deleteButton.addEventListener("click", () => {
            deleteDocument(documentData.document_id, deleteButton);
        });

        actions.appendChild(deleteButton);

        card.append(
            icon,
            name,
            type,
            size,
            segments,
            status,
            uploaded,
            actions
        );

        documentsList.appendChild(card);
    }

    // Upload a document.
    async function uploadDocument(file) {
        if (!file) return;

        const allowedExtensions = [".pdf", ".docx", ".pptx", ".txt"];
        const extension = file.name
            .substring(file.name.lastIndexOf("."))
            .toLowerCase();

        if (!allowedExtensions.includes(extension)) {
            showStatus(
                "Unsupported file type. Please select PDF, DOCX, PPTX or TXT.",
                "error"
            );
            fileInput.value = "";
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            showStatus("File size must not exceed 10 MB.", "error");
            fileInput.value = "";
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        uploadTrigger.disabled = true;
        browseButton.disabled = true;

        showStatus(`Uploading and processing ${file.name}...`, "info");

        try {
            const response = await fetch(`${DOCUMENT_API_URL}/upload`, {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    typeof data.detail === "string"
                        ? data.detail
                        : "Document upload failed."
                );
            }

            showStatus(
                `${data.message} (${data.segment_count} segments created.)`,
                "success"
            );

            fileInput.value = "";

            await loadDocuments();

        } catch (error) {
            console.error("Upload error:", error);
            showStatus(error.message, "error");

        } finally {
            uploadTrigger.disabled = false;
            browseButton.disabled = false;
        }
    }

    // Delete a document.
    async function deleteDocument(documentId, button) {
        const confirmed = window.confirm(
            "Are you sure you want to delete this document? This will also remove its indexed vectors."
        );

        if (!confirmed) return;

        button.disabled = true;
        button.textContent = "Deleting...";

        try {
            const response = await fetch(
                `${DOCUMENT_API_URL}/${encodeURIComponent(documentId)}`,
                { method: "DELETE" }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Unable to delete document.");
            }

            showStatus("Document deleted successfully.", "success");

            await loadDocuments();

        } catch (error) {
            console.error("Delete error:", error);
            showStatus(error.message, "error");

            button.disabled = false;
            button.textContent = "Delete";
        }
    }

    // Handle file selection.
    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];

        if (file) {
            uploadDocument(file);
        }
    });

    // Drag and drop functionality.
    uploadArea?.addEventListener("dragover", (event) => {
        event.preventDefault();
        uploadArea.classList.add("drag-over");
    });

    uploadArea?.addEventListener("dragleave", (event) => {
        event.preventDefault();
        uploadArea.classList.remove("drag-over");
    });

    uploadArea?.addEventListener("drop", (event) => {
        event.preventDefault();
        uploadArea.classList.remove("drag-over");

        const file = event.dataTransfer.files[0];

        if (file) {
            uploadDocument(file);
        }
    });

    // Refresh document list.
    refreshButton?.addEventListener("click", loadDocuments);

    // Initial document list.
    loadDocuments();
});
