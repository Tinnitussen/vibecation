import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import apiClient from '../api/client'
import './TripChat.css'

function TripChat({ tripID }) {
  const { userID } = useAuth()
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const wsRef = useRef(null)
  const messagesEndRef = useRef(null)
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Convert HTTP URL to WebSocket URL
  const getWebSocketUrl = () => {
    const wsUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://')
    return `${wsUrl}/ws/trips/${tripID}/chat`
  }

  // Load chat history
  const loadChatHistory = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get(`/trips/${tripID}/chat/messages`, {
        params: { userID, limit: 50 }
      })
      setMessages(response.data.messages || [])
    } catch (err) {
      console.error('Failed to load chat history:', err)
    } finally {
      setLoading(false)
    }
  }

  // Connect to WebSocket
  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return // Already connected
    }

    const ws = new WebSocket(getWebSocketUrl())
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'message') {
        // New message received - check if it's our own message to replace optimistic one
        setMessages(prev => {
          // Remove any optimistic messages with matching content from this user
          const filtered = prev.filter(m => 
            !(m.isOptimistic && m.userID === data.userID && m.content === data.content)
          )
          // Check if message already exists (avoid duplicates)
          const exists = filtered.some(m => m.messageID === data.messageID)
          if (exists) {
            return filtered
          }
          // Add the new message
          return [...filtered, {
            messageID: data.messageID,
            userID: data.userID,
            userName: data.userName,
            content: data.content,
            createdAt: data.createdAt
          }]
        })
      } else if (data.type === 'error') {
        console.error('WebSocket error:', data.message)
        // If membership error, try to reload chat history to refresh connection
        if (data.message && data.message.includes('not a member')) {
          setTimeout(() => {
            loadChatHistory()
          }, 1000)
        }
      } else if (data.type === 'sent') {
        // Message sent confirmation - do nothing, message will come via broadcast
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnected(false)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          connectWebSocket()
        }
      }, 3000)
    }
  }

  // Send message
  const sendMessage = () => {
    if (!inputValue.trim() || !connected || !wsRef.current) return

    const messageContent = inputValue.trim()
    const message = {
      userID,
      content: messageContent
    }

    // Optimistic update: add message to UI immediately
    const tempMessageID = `temp_${Date.now()}`
    const optimisticMessage = {
      messageID: tempMessageID,
      userID,
      userName: 'You', // Will be replaced with actual username from server
      content: messageContent,
      createdAt: new Date().toISOString(),
      isOptimistic: true // Flag to identify optimistic messages
    }
    setMessages(prev => [...prev, optimisticMessage])
    setInputValue('')

    try {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(message))
      } else {
        console.warn('WebSocket not open, attempting to reconnect...')
        setConnected(false)
        connectWebSocket()
        // Remove optimistic message if connection failed
        setMessages(prev => prev.filter(m => m.messageID !== tempMessageID))
      }
    } catch (err) {
      console.error('Failed to send message:', err)
      setConnected(false)
      // Remove optimistic message on error
      setMessages(prev => prev.filter(m => m.messageID !== tempMessageID))
    }
  }

  // Handle Enter key
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Initialize: load history and connect WebSocket
  useEffect(() => {
    if (!tripID || !userID) return

    loadChatHistory()
    connectWebSocket()

    return () => {
      // Cleanup: close WebSocket on unmount
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tripID, userID])

  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    
    // If less than 1 minute ago, show "just now"
    if (diff < 60000) {
      return 'just now'
    }
    
    // If today, show time
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    
    // If yesterday
    const yesterday = new Date(now)
    yesterday.setDate(yesterday.getDate() - 1)
    if (date.toDateString() === yesterday.toDateString()) {
      return 'yesterday ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    
    // Otherwise show date and time
    return date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const isOwnMessage = (messageUserID) => messageUserID === userID

  return (
    <div className="trip-chat">
      <div className="chat-header">
        <h3>💬 Trip Chat</h3>
        <div className="chat-status">
          <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}></span>
          <span className="status-text">{connected ? 'Connected' : 'Connecting...'}</span>
        </div>
      </div>

      <div className="chat-messages">
        {loading ? (
          <div className="chat-loading">Loading messages...</div>
        ) : messages.length === 0 ? (
          <div className="chat-empty">
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.messageID}
              className={`chat-message ${isOwnMessage(message.userID) ? 'own-message' : ''}`}
            >
              <div className="message-header">
                <span className="message-author">{message.userName}</span>
                <span className="message-time">{formatTime(message.createdAt)}</span>
              </div>
              <div className="message-content">{message.content}</div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <textarea
          className="chat-input"
          placeholder={connected ? "Type a message..." : "Connecting..."}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={!connected}
          rows={2}
        />
        <button
          className="chat-send-button"
          onClick={sendMessage}
          disabled={!inputValue.trim() || !connected}
        >
          Send
        </button>
      </div>
    </div>
  )
}

export default TripChat

