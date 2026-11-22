
// =====================================
// STUDYMATE AI - MAIN JAVASCRIPT
// =====================================

const BACKEND_URL = "http://127.0.0.1:8000";


// =====================================
// PAGE NAVIGATION
// =====================================

const navLinks = document.querySelectorAll(".nav-link");

const pages = document.querySelectorAll(".page");

const pageTitle = document.getElementById("page-title");

const pageSubtitle = document.getElementById("page-subtitle");

const pageDetails = {
    dashboard: {
        title: "Dashboard",
        subtitle: "Welcome back! Here's your learning overview."
    },

    chat: {
        title: "AI Study Assistant",
        subtitle: "Ask questions and learn with your AI assistant."
    },

    documents: {
        title: "My Documents",
        subtitle: "Manage your study materials."
    },

    pyq: {
        title: "PYQ Analyzer",
        subtitle: "Analyze previous year question papers."
    },

    tests: {
        title: "Mock Tests",
        subtitle: "Practice and test your knowledge."
    },

    performance: {
        title: "Performance",
        subtitle: "Track your learning progress."
    },

    planner: {
        title: "Study Planner",
        subtitle: "Organize your study schedule."
    }
};


function showPage(pageName) {

    // Hide all pages
    pages.forEach(page => {
        page.classList.remove("active");
    });

    // Remove active navigation style
    navLinks.forEach(link => {
        link.classList.remove("active");
    });

    // Show selected page
    const selectedPage = document.getElementById(
        `${pageName}-page`
    );

    if (!selectedPage || !pageDetails[pageName]) {
        return;
    }

    selectedPage.classList.add("active");

    // Update active sidebar link
    const selectedLink = document.querySelector(
        `.nav-link[data-page="${pageName}"]`
    );

    if (selectedLink) {
        selectedLink.classList.add("active");
    }

    // Update topbar
    pageTitle.textContent = pageDetails[pageName].title;

    pageSubtitle.textContent = pageDetails[pageName].subtitle;

    // Refresh icons if necessary
    if (window.lucide) {
        lucide.createIcons();
    }
}


// Sidebar navigation
navLinks.forEach(link => {

    link.addEventListener("click", function(event) {

        event.preventDefault();

        const pageName = this.dataset.page;

        showPage(pageName);

    });

});


// Quick action navigation
const actionCards = document.querySelectorAll(".action-card");

actionCards.forEach(card => {

    card.addEventListener("click", function() {

        const targetPage = this.dataset.target;

        showPage(targetPage);

    });

});


// =====================================
// BACKEND CONNECTION CHECK
// =====================================

async function checkBackend() {

    const statusText = document.getElementById(
        "backend-status-text"
    );

    const statusDot = document.querySelector(
        ".status-dot"
    );

    const cardStatus = document.getElementById(
        "backend-card-status"
    );

    try {

        const response = await fetch(
            `${BACKEND_URL}/health`
        );

        if (!response.ok) {
            throw new Error("Backend request failed.");
        }

        const data = await response.json();

        statusText.textContent = "Backend Connected";

        statusDot.style.background = "#10b981";

        statusDot.style.boxShadow = "0 0 8px #10b981";

        cardStatus.textContent = "Connected";

        cardStatus.style.color = "#34d399";

        console.log("Backend health:", data);

    }

    catch (error) {

        statusText.textContent = "Backend Disconnected";

        statusDot.style.background = "#ef4444";

        statusDot.style.boxShadow = "0 0 8px #ef4444";

        cardStatus.textContent = "Disconnected";

        cardStatus.style.color = "#f87171";

        console.error("Backend connection error:", error);

    }

}


// Check backend when application loads
checkBackend();


// Check backend every 30 seconds
setInterval(checkBackend, 30000);


// =====================================
// INITIALIZE APPLICATION
// =====================================

document.addEventListener("DOMContentLoaded", () => {

    showPage("dashboard");

});
