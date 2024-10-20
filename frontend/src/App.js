import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'https://supreme-space-robot-j6r74gj996q29vg-8000.app.github.dev';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const chatContainerRef = useRef(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (input.trim() === '') return;
  
    setMessages(prevMessages => [...prevMessages, { text: input, sender: 'user' }]);
    setInput('');
    setIsLoading(true);
  
    try {
      const response = await axios.post(`${API_URL}/chat`, { message: input }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      console.log('Chat response:', response.data);
      setMessages(prevMessages => [
        ...prevMessages,
        { text: response.data.response, sender: 'bot' },
        { text: "Sources:", sender: 'bot' },
        ...response.data.sources.map(source => ({ text: source, sender: 'source' }))
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prevMessages => [...prevMessages, { text: 'An error occurred. Please try again.', sender: 'bot' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setFile(file);
    setIsLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      console.log('Upload response:', response.data);
      setMessages(prevMessages => [...prevMessages, { text: 'Document uploaded and processed successfully. You can now ask questions about it.', sender: 'bot' }]);
    } catch (error) {
      console.error('Error uploading file:', error);
      let errorMessage = 'Error uploading file. Please try again.';
      if (error.response) {
        console.error('Error response:', error.response.data);
        errorMessage = `Upload error: ${error.response.data.detail || error.response.statusText}`;
      }
      setMessages(prevMessages => [...prevMessages, { text: errorMessage, sender: 'bot' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>Document Chatter</h1>
      <div className="file-upload">
        <label htmlFor="file-upload" className="custom-file-upload">
          Choose PDF File
        </label>
        <input id="file-upload" type="file" onChange={handleFileUpload} accept=".pdf" />
        {file && <p>Selected file: {file.name}</p>}
      </div>
      <div className="chat-container" ref={chatContainerRef}>
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.sender}`}>
            {message.text}
          </div>
        ))}
        {isLoading && <div className="loading">Processing...</div>}
      </div>
      <div className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage()}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button onClick={sendMessage} disabled={isLoading}>Send</button>
      </div>
    </div>
  );
}

export default App;