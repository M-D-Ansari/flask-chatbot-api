document.getElementById("chat-form").addEventListener("submit", async function (event) {
    event.preventDefault();

    const userInput = document.getElementById("user-input").value.trim();
    if (!userInput) return;

    addMessageToChat(userInput, "user");
    document.getElementById("user-input").value = "";

    hideSuggestions();

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query: userInput })
        });

        const data = await response.json();

        if (response.ok) {
            addMessageToChat(data.response, "bot");

            // Show suggestions if available
            if (data.suggestions && Array.isArray(data.suggestions)) {
                showSuggestions(data.suggestions);
            }
        } else {
            addMessageToChat("Sorry, an error occurred: " + data.error, "bot");
        }
    } catch (error) {
        addMessageToChat("Sorry, something went wrong: " + error.message, "bot");
    }
});

function addMessageToChat(message, sender) {
    const chatWindow = document.getElementById("chat-window");

    const messageDiv = document.createElement("div");
    messageDiv.classList.add("chat-message", sender);

    const messageText = document.createElement("p");
    messageText.textContent = message;

    messageDiv.appendChild(messageText);
    chatWindow.appendChild(messageDiv);

    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showSuggestions(suggestions) {
    hideSuggestions(); // Clear any existing ones

    const chatWindow = document.getElementById("chat-window");
    const suggestionContainer = document.createElement("div");
    suggestionContainer.className = "suggestions";

    suggestions.forEach(text => {
        const button = document.createElement("button");
        button.className = "suggestion-button";
        button.textContent = text;
        button.onclick = () => {
            document.getElementById("user-input").value = text;
            document.getElementById("chat-form").dispatchEvent(new Event("submit"));
        };
        suggestionContainer.appendChild(button);
    });

    chatWindow.appendChild(suggestionContainer);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function hideSuggestions() {
    document.querySelectorAll(".suggestions").forEach(el => el.remove());
}
