// Chatbot icon in the bottom-right corner
const chatbotIcon = document.createElement("div");
chatbotIcon.style.position = "fixed";
chatbotIcon.style.bottom = "20px";
chatbotIcon.style.right = "20px";
chatbotIcon.style.width = "60px";
chatbotIcon.style.height = "60px";
chatbotIcon.style.background = "#007bff";
chatbotIcon.style.borderRadius = "50%";
chatbotIcon.style.cursor = "pointer";
chatbotIcon.style.boxShadow = "0px 4px 8px rgba(0, 0, 0, 0.3)";
chatbotIcon.style.zIndex = "9999";
chatbotIcon.style.display = "flex";
chatbotIcon.style.justifyContent = "center";
chatbotIcon.style.alignItems = "center";
chatbotIcon.style.color = "white";
chatbotIcon.innerHTML = "💬";
document.body.appendChild(chatbotIcon);

// Chatbot iframe, covering 40% width by default, from bottom to top of the page
const chatbotIframe = document.createElement("iframe");
chatbotIframe.src = "http://localhost:8501";  // Change this to your Streamlit deployment URL
chatbotIframe.style.position = "fixed";
chatbotIframe.style.bottom = "0";
chatbotIframe.style.right = "0";
chatbotIframe.style.width = "40%";
chatbotIframe.style.height = "100%";
chatbotIframe.style.border = "1px solid #ddd";
chatbotIframe.style.borderRadius = "10px 0 0 10px";
chatbotIframe.style.zIndex = "9999";
chatbotIframe.style.display = "none";  // Hidden by default
document.body.appendChild(chatbotIframe);

// Expand button to increase width to 60%
const expandButton = document.createElement("div");
expandButton.style.position = "fixed";
expandButton.style.bottom = "10px";
expandButton.style.right = "42%";
expandButton.style.width = "50px";
expandButton.style.height = "30px";
expandButton.style.background = "#007bff";
expandButton.style.color = "white";
expandButton.style.borderRadius = "5px";
expandButton.style.textAlign = "center";
expandButton.style.cursor = "pointer";
expandButton.style.zIndex = "10000";
expandButton.style.display = "none"; // Hidden by default
expandButton.innerHTML = "Expand";
document.body.appendChild(expandButton);

// Toggle chatbot iframe visibility on icon click
chatbotIcon.onclick = () => {
    const isIframeVisible = chatbotIframe.style.display === "block";
    chatbotIframe.style.display = isIframeVisible ? "none" : "block";
    expandButton.style.display = isIframeVisible ? "none" : "block"; // Show expand button only when iframe is visible
};

// Expand/Collapse functionality
let isExpanded = false;
expandButton.onclick = () => {
    if (isExpanded) {
        chatbotIframe.style.width = "40%";
        expandButton.style.right = "42%";
        expandButton.innerHTML = "Expand";
    } else {
        chatbotIframe.style.width = "60%";
        expandButton.style.right = "62%";
        expandButton.innerHTML = "Collapse";
    }
    isExpanded = !isExpanded;
};