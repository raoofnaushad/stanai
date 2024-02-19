import React, { useState } from "react";
import FarpointSidebar from "../../components/FarpointSidebar/FarpointSidebar";
import "./FarpointBOT.css";

const FarpointBOT = () => {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false); // New state for loading indicator
  const token = localStorage.getItem("access_token");
  const apiUrl = process.env.REACT_APP_API_URL;

  const handleInputChange = (e) => {
    setInputText(e.target.value);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSendMessage();
    }
  };

  const handleSendMessage = async () => {
    if (inputText.trim() === "") return;

    // Add user's message
    setMessages((prevMessages) => [
      ...prevMessages,
      { sender: "user", text: inputText },
    ]);

    setIsLoading(true); // Start loading

    // Prepare the data to send
    const requestData = { user_input: inputText };

    try {
      // Send API request to backend
      const response = await fetch(`${apiUrl}/farpointbot/bot_response`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Get the response data
      const responseData = await response.json();

      // Assuming responseData contains a field 'bot_response' with the bot's reply
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "Chaplin", text: responseData.bot_response },
      ]);
      setIsLoading(false);
    } catch (error) {
      console.error("Error sending message to bot:", error);
      setIsLoading(false); // Stop loading in case of error
    }

    // Clear input field
    setInputText("");
  };

  return (
    <div className="app">
      <FarpointSidebar />
      <div className="chat-container">
        <div className="chat-window">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`message ${
                message.sender === "user" ? "user-message" : "bot-message"
              }`}
            >
              <div className="message-sender">
                {message.sender === "user" ? "User" : "Chaplin"}
              </div>
              <p>{message.text}</p>
            </div>
          ))}
        </div>
        <div className="chat-input">
          <input
            type="text"
            value={inputText}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="Ask Chaplin..."
            disabled={isLoading} // Disable input when loading
          />
          <button onClick={handleSendMessage} disabled={isLoading}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default FarpointBOT;
