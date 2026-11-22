
const CHAT_API_URL = "http://127.0.0.1:8000/api/chat";

const SYSTEM_INSTRUCTION =
    "You are StudyMate AI, a helpful college study assistant. " +
    "Explain concepts in simple English with examples. " +
    "Use headings and bullet points when helpful. " +
    "Keep explanations clear and suitable for college students.";

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatMessages = document.getElementById("chat-messages");
    const sendButton = document.getElementById("send-btn");
    const useDocuments = document.getElementById("use-documents");
    const newChatButton = document.getElementById("new-chat-btn");
    const welcomeMessage = document.getElementById("chat-welcome");

    if (!chatForm || !chatInput || !chatMessages) {
        return;
    }

    // Remove the welcome screen when the first message is sent.
    function removeWelcomeMessage() {
        const welcome = document.getElementById("chat-welcome");

        if (welcome) {
            welcome.remove();
        }
    }

    // Add a chat message safely using textContent.
    function addMessage(role, message) {
        const messageElement = document.createElement("div");
        messageElement.className = `chat-message ${role}-message`;

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = role === "user" ? "U" : "AI";

        const content = document.createElement("div");
        content.className = "message-content";
        content.textContent = message;

        messageElement.appendChild(avatar);
        messageElement.appendChild(content);

        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return messageElement;
    }

    // Display source references returned by the RAG API.
    function addSources(sources, messageElement) {
        if (!sources || sources.length === 0) {
            return;
        }

        const sourceContainer = document.createElement("div");
        sourceContainer.className = "chat-sources";

        const heading = document.createElement("strong");
        heading.textContent = "Sources";
        sourceContainer.appendChild(heading);

        const sourceList = document.createElement("ul");

        sources.forEach((source) => {
            const item = document.createElement("li");

            let label = source.filename || "Uploaded document";

            if (source.page_number !== null &&
                source.page_number !== undefined) {
                label += ` — Page ${source.page_number}`;
            }

            if (source.slide_number !== null &&
                source.slide_number !== undefined) {
                label += ` — Slide ${source.slide_number}`;
            }

            item.textContent = label;
            sourceList.appendChild(item);
        });

        sourceContainer.appendChild(sourceList);

        const content = messageElement.querySelector(".message-content");
        content.appendChild(sourceContainer);

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Show a temporary loading message.
    function showLoading() {
        const loadingElement = document.createElement("div");
        loadingElement.className = "chat-message assistant-message";
        loadingElement.id = "chat-loading";

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = "AI";

        const content = document.createElement("div");
        content.className = "message-content";
        content.textContent = "StudyMate is thinking...";

        loadingElement.appendChild(avatar);
        loadingElement.appendChild(content);

        chatMessages.appendChild(loadingElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeLoading() {
        const loading = document.getElementById("chat-loading");

        if (loading) {
            loading.remove();
        }
    }

    // Send a message to FastAPI.
    async function sendMessage(message) {
        const prompt = message.trim();

        if (!prompt) {
            return;
        }

        removeWelcomeMessage();

        addMessage("user", prompt);

        chatInput.value = "";
        chatInput.disabled = true;
        sendButton.disabled = true;

        showLoading();

        try {
            const response = await fetch(CHAT_API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    prompt: prompt,
                    system_instruction: SYSTEM_INSTRUCTION,
                    use_documents: useDocuments.checked
                })
            });

            const data = await response.json();

            removeLoading();

            if (!response.ok) {
                const errorMessage =
                    typeof data.detail === "string"
                        ? data.detail
                        : "Something went wrong. Please try again.";

                addMessage("assistant", `Error: ${errorMessage}`);
                return;
            }

            const assistantMessage = addMessage(
                "assistant",
                data.response || "I could not generate a response."
            );

            addSources(data.sources, assistantMessage);

        } catch (error) {
            removeLoading();

            addMessage(
                "assistant",
                "Unable to connect to the backend. Please check that your FastAPI server is running."
            );

            console.error("Chat error:", error);

        } finally {
            chatInput.disabled = false;
            sendButton.disabled = false;
            chatInput.focus();
        }
    }

    // Handle form submission.
    chatForm.addEventListener("submit", (event) => {
        event.preventDefault();
        sendMessage(chatInput.value);
    });

    // Handle suggested prompts.
    document.querySelectorAll(".suggestion-card").forEach((button) => {
        button.addEventListener("click", () => {
            const prompt = button.dataset.prompt;

            if (prompt) {
                sendMessage(prompt);
            }
        });
    });

    // Reset the chat.
    if (newChatButton) {
        newChatButton.addEventListener("click", () => {
            chatMessages.replaceChildren();

            if (welcomeMessage) {
                chatMessages.appendChild(welcomeMessage);
            }

            chatInput.value = "";
            chatInput.disabled = false;
            sendButton.disabled = false;
            chatInput.focus();
        });
    }
});
