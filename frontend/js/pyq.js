
const PYQ_API_URL = "http://127.0.0.1:8000/api/pyq";

document.addEventListener("DOMContentLoaded", () => {
    const uploadForm = document.getElementById("pyq-upload-form");
    const subjectInput = document.getElementById("pyq-subject");
    const yearInput = document.getElementById("pyq-year");
    const fileInput = document.getElementById("pyq-file");
    const browseButton = document.getElementById("pyq-browse-btn");
    const fileName = document.getElementById("pyq-file-name");
    const uploadButton = document.getElementById("pyq-upload-btn");
    const uploadStatus = document.getElementById("pyq-upload-status");

    const questionsList = document.getElementById("pyq-questions-list");
    const subjectFilter = document.getElementById("pyq-subject-filter");
    const yearFilter = document.getElementById("pyq-year-filter");

    const filterButton = document.getElementById("pyq-filter-btn");
    const clearFilterButton = document.getElementById("pyq-clear-filter-btn");
    const refreshButton = document.getElementById("pyq-refresh-btn");

    if (!uploadForm || !questionsList) {
        return;
    }

    // Display upload status.
    function showUploadStatus(message, type = "info") {
        uploadStatus.textContent = message;
        uploadStatus.className = `pyq-status ${type}`;
    }

    // Display an empty or error message.
    function showMessage(container, message) {
        container.replaceChildren();

        const element = document.createElement("div");
        element.className = "documents-empty";
        element.textContent = message;

        container.appendChild(element);
    }

    // Safely display analytics.
    function renderAnalyticsList(containerId, data) {
        const container = document.getElementById(containerId);
        container.replaceChildren();

        const entries = Object.entries(data || {});

        if (entries.length === 0) {
            const empty = document.createElement("p");
            empty.textContent = "No data available.";
            container.appendChild(empty);
            return;
        }

        entries.sort((a, b) => b[1] - a[1]);

        entries.forEach(([label, count]) => {
            const item = document.createElement("div");
            item.className = "pyq-analytics-item";

            const name = document.createElement("span");
            name.textContent = label;

            const value = document.createElement("strong");
            value.textContent = count;

            item.append(name, value);
            container.appendChild(item);
        });
    }

    // Load question analytics.
    async function loadAnalytics(subject = "") {
        try {
            const params = new URLSearchParams();

            if (subject.trim()) {
                params.set("subject", subject.trim());
            }

            const response = await fetch(
                `${PYQ_API_URL}/analytics?${params.toString()}`
            );

            if (!response.ok) {
                throw new Error("Unable to load analytics.");
            }

            const data = await response.json();

            document.getElementById("pyq-total-questions").textContent =
                data.total_questions;

            document.getElementById("pyq-total-topics").textContent =
                Object.keys(data.topic_wise || {}).length;

            document.getElementById("pyq-total-years").textContent =
                Object.keys(data.year_wise || {}).length;

            renderAnalyticsList("pyq-topic-analytics", data.topic_wise);
            renderAnalyticsList("pyq-year-analytics", data.year_wise);

        } catch (error) {
            console.error("Analytics error:", error);

            document.getElementById("pyq-total-questions").textContent = "—";
            document.getElementById("pyq-total-topics").textContent = "—";
            document.getElementById("pyq-total-years").textContent = "—";

            renderAnalyticsList("pyq-topic-analytics", {});
            renderAnalyticsList("pyq-year-analytics", {});
        }
    }

    // Create an individual question card.
    function createQuestionCard(question) {
        const card = document.createElement("div");
        card.className = "pyq-question-card";

        const top = document.createElement("div");
        top.className = "pyq-question-top";

        const metadata = document.createElement("div");
        metadata.className = "pyq-question-meta";

        const tags = [
            question.subject,
            `Year: ${question.exam_year}`,
            question.topic || "Uncategorized",
            question.marks != null ? `${question.marks} Marks` : null
        ].filter(Boolean);

        tags.forEach((tagText) => {
            const tag = document.createElement("span");
            tag.className = "pyq-tag";
            tag.textContent = tagText;
            metadata.appendChild(tag);
        });

        top.appendChild(metadata);

        const questionText = document.createElement("p");
        questionText.className = "pyq-question-text";
        questionText.textContent = question.question_text;

        const footer = document.createElement("div");
        footer.className = "pyq-question-footer";

        const source = document.createElement("p");
        source.textContent = `Source: ${question.source_filename}`;

        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "pyq-delete-btn";
        deleteButton.textContent = "Delete";

        deleteButton.addEventListener("click", () => {
            deleteQuestion(question.question_id, deleteButton);
        });

        footer.append(source, deleteButton);

        card.append(top, questionText, footer);

        return card;
    }

    // Load saved questions with optional filters.
    async function loadQuestions() {
        showMessage(questionsList, "Loading questions...");

        try {
            const params = new URLSearchParams();

            if (subjectFilter.value.trim()) {
                params.set("subject", subjectFilter.value.trim());
            }

            if (yearFilter.value.trim()) {
                params.set("exam_year", yearFilter.value.trim());
            }

            const response = await fetch(
                `${PYQ_API_URL}/questions?${params.toString()}`
            );

            if (!response.ok) {
                throw new Error("Unable to load questions.");
            }

            const questions = await response.json();

            questionsList.replaceChildren();

            if (questions.length === 0) {
                showMessage(
                    questionsList,
                    "No questions found. Upload a question paper or change your filters."
                );
                return;
            }

            questions.forEach((question) => {
                questionsList.appendChild(createQuestionCard(question));
            });

        } catch (error) {
            console.error("Question loading error:", error);

            showMessage(
                questionsList,
                "Could not load questions. Please check your backend connection."
            );
        }
    }

    // Refresh questions and analytics.
    async function refreshPYQData() {
        await Promise.all([
            loadQuestions(),
            loadAnalytics(subjectFilter.value)
        ]);
    }

    // Upload and process a PYQ PDF.
    async function uploadPYQ(event) {
        event.preventDefault();

        const subject = subjectInput.value.trim();
        const year = yearInput.value.trim();
        const file = fileInput.files[0];

        if (!subject || !year || !file) {
            showUploadStatus(
                "Please enter the subject, year and select a PDF.",
                "error"
            );
            return;
        }

        if (!Number.isInteger(Number(year)) ||
            Number(year) < 1900 ||
            Number(year) > 2100) {
            showUploadStatus("Please enter a valid examination year.", "error");
            return;
        }

        if (!file.name.toLowerCase().endsWith(".pdf")) {
            showUploadStatus("Only PDF files are supported.", "error");
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            showUploadStatus("File size must not exceed 10 MB.", "error");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        const params = new URLSearchParams({
            subject: subject,
            exam_year: year
        });

        uploadButton.disabled = true;
        browseButton.disabled = true;

        showUploadStatus(
            "Uploading PDF and extracting questions with Gemini. Please wait...",
            "info"
        );

        try {
            const response = await fetch(
                `${PYQ_API_URL}/upload?${params.toString()}`,
                {
                    method: "POST",
                    body: formData
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    typeof data.detail === "string"
                        ? data.detail
                        : "PYQ upload failed."
                );
            }

            showUploadStatus(
                `${data.message} Total questions extracted: ${data.total_questions}.`,
                "success"
            );

            uploadForm.reset();
            fileName.textContent = "No file selected";

            subjectFilter.value = subject;
            yearFilter.value = year;

            await refreshPYQData();

        } catch (error) {
            console.error("PYQ upload error:", error);
            showUploadStatus(error.message, "error");

        } finally {
            uploadButton.disabled = false;
            browseButton.disabled = false;
        }
    }

    // Delete one question.
    async function deleteQuestion(questionId, button) {
        const confirmed = window.confirm(
            "Are you sure you want to delete this question?"
        );

        if (!confirmed) return;

        button.disabled = true;
        button.textContent = "Deleting...";

        try {
            const response = await fetch(
                `${PYQ_API_URL}/questions/${encodeURIComponent(questionId)}`,
                {
                    method: "DELETE"
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Unable to delete question.");
            }

            showUploadStatus(
                "Question deleted successfully.",
                "success"
            );

            await refreshPYQData();

        } catch (error) {
            console.error("Question deletion error:", error);

            showUploadStatus(error.message, "error");

            button.disabled = false;
            button.textContent = "Delete";
        }
    }

    // Browse PDF.
    browseButton.addEventListener("click", () => {
        fileInput.click();
    });

    // Show selected filename.
    fileInput.addEventListener("change", () => {
        fileName.textContent = fileInput.files.length
            ? fileInput.files[0].name
            : "No file selected";
    });

    // Form submission.
    uploadForm.addEventListener("submit", uploadPYQ);

    // Apply filters.
    filterButton.addEventListener("click", refreshPYQData);

    // Clear filters.
    clearFilterButton.addEventListener("click", async () => {
        subjectFilter.value = "";
        yearFilter.value = "";

        await refreshPYQData();
    });

    // Refresh button.
    refreshButton.addEventListener("click", refreshPYQData);

    // Initial loading.
    refreshPYQData();
});
