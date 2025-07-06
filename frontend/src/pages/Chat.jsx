"use client"

import { useState, useRef, useEffect } from "react"
import { ChatContainer } from "@/components/ui/chat"
import { Sidebar } from "@/components/Sidebar"
import { WelcomeScreen } from "@/components/WelcomeScreen"
import { ChatInterface } from "@/components/ChatInterface"

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [conversations, setConversations] = useState([])
  const [isLoadingConversations, setIsLoadingConversations] = useState(true)
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const [selectedModel, setSelectedModel] = useState("qwen")
  const modelOptions = [
    { label: "Qwen 3", value: "qwen" },
    { label: "Model 2", value: "model-2" }
  ]

  const userId = 'A1' // Using TEST user from database

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    if (selectedConversation) {
      loadMessages(selectedConversation.conversation_id)
    } else {
      setMessages([])
    }
  }, [selectedConversation])

  const loadConversations = async () => {
    setIsLoadingConversations(true)
    try {
      const response = await fetch(`http://localhost:8000/chat/conversations/${userId}`)
      if (response.ok) {
        const data = await response.json()
        setConversations(data || [])
      } else {
        console.error('Failed to load conversations')
      }
    } catch (error) {
      console.error('Error loading conversations:', error)
    } finally {
      setIsLoadingConversations(false)
    }
  }

  const loadMessages = async (conversationId) => {
    console.log('Loading messages for conversation:', conversationId)
    try {
      const response = await fetch(`http://localhost:8000/chat/messages/${conversationId}`)
      console.log('Response status:', response.status)
      if (response.ok) {
        const data = await response.json()
        console.log('Loaded messages:', data)
        // Transform backend message format to frontend format
        const transformedMessages = data.map(msg => ({
          id: msg.message_id,
          role: msg.sender,
          content: msg.content,
          createdAt: new Date(msg.created_at)
        }))
        console.log('Transformed messages:', transformedMessages)
        setMessages(transformedMessages)
      } else {
        console.error('Failed to load messages')
        setMessages([])
      }
    } catch (error) {
      console.error('Error loading messages:', error)
      setMessages([])
    }
  }

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }

  const handleInputChange = (e) => {
    setInput(e.target.value)
  }

  const handleSubmit = async (e, { experimental_attachments } = {}) => {
    e.preventDefault()
    if (!input.trim() && !experimental_attachments?.length) return

    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input || (experimental_attachments?.length ? "File uploaded" : ""),
      createdAt: new Date(),
      experimental_attachments: experimental_attachments ? Array.from(experimental_attachments).map(file => ({
        name: file.name,
        url: URL.createObjectURL(file),
        type: file.type
      })) : null
    }
    
    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)
    setIsTyping(true)

    try {
      let currentConversationId = selectedConversation?.conversation_id

      // If no conversation is selected, create a new one
      if (!currentConversationId) {
        const createResponse = await fetch('http://localhost:8000/chat/create_conversation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            title: input || (experimental_attachments?.length ? 'File Upload' : 'New Chat')
          })
        })

        if (createResponse.ok) {
          const conversationData = await createResponse.json()
          currentConversationId = conversationData[0]?.conversation_id
          
          if (currentConversationId) {
            const newConversation = {
              conversation_id: currentConversationId,
              title: input || (experimental_attachments?.length ? 'File Upload' : 'New Chat'),
              user_id: userId,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
            setSelectedConversation(newConversation)
            setConversations(prev => [newConversation, ...prev])
          }
        }
      }

      // Handle file uploads if present
      if (experimental_attachments?.length && currentConversationId) {
        const formData = new FormData()
        formData.append('conversation_id', currentConversationId)
        formData.append('user_id', userId)
        
        for (const file of experimental_attachments) {
          formData.append('files', file)
        }
        
        try {
          await fetch('http://localhost:8000/chat/upload_files', {
            method: 'POST',
            body: formData
          })
        } catch (uploadError) {
          console.error('File upload error:', uploadError)
        }
      }

      // Save user message
      if (currentConversationId) {
        await fetch('http://localhost:8000/chat/create_message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: currentConversationId,
            user_id: userId,
            sender: 'user',
            content: input || (experimental_attachments?.length ? 'File uploaded' : '')
          })
        })
      }

      // Get AI response
      const chatResponse = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          prompt: input || (experimental_attachments?.length ? 'Please help me analyze the uploaded file.' : ''),
          conversation_id: currentConversationId
        })
      })
      
      const chatData = await chatResponse.json()
      const aiResponse = chatData.result || "No response from AI"

      // Save AI response
      if (currentConversationId) {
        await fetch('http://localhost:8000/chat/create_message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: currentConversationId,
            user_id: userId,
            sender: 'assistant',
            content: aiResponse
          })
        })
      }

      // Add AI response to messages
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: aiResponse,
        createdAt: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])

    } catch (err) {
      console.error('Chat error:', err)
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Error: Could not get response from backend.",
        createdAt: new Date()
      }])
    } finally {
      setIsLoading(false)
      setIsTyping(false)
    }
  }

  const append = async (message) => {
    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content: message.content,
      createdAt: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setIsTyping(true)
    
    try {
      let currentConversationId = selectedConversation?.conversation_id

      // If no conversation is selected, create a new one
      if (!currentConversationId) {
        const createResponse = await fetch('http://localhost:8000/chat/create_conversation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            title: message.content.length > 50 ? message.content.substring(0, 50) + '...' : message.content
          })
        })

        if (createResponse.ok) {
          const conversationData = await createResponse.json()
          currentConversationId = conversationData[0]?.conversation_id
          
          if (currentConversationId) {
            const newConversation = {
              conversation_id: currentConversationId,
              title: message.content.length > 50 ? message.content.substring(0, 50) + '...' : message.content,
              user_id: userId,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
            setSelectedConversation(newConversation)
            setConversations(prev => [newConversation, ...prev])
          }
        }
      }

      // Save user message
      if (currentConversationId) {
        await fetch('http://localhost:8000/chat/create_message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: currentConversationId,
            user_id: userId,
            sender: 'user',
            content: message.content
          })
        })
      }

      // Get AI response
      const chatResponse = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          prompt: message.content,
          conversation_id: currentConversationId
        })
      })
      
      const chatData = await chatResponse.json()
      const aiResponse = chatData.result || "No response from AI"

      // Save AI response
      if (currentConversationId) {
        await fetch('http://localhost:8000/chat/create_message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: currentConversationId,
            user_id: userId,
            sender: 'assistant',
            content: aiResponse
          })
        })
      }

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: aiResponse,
        createdAt: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      console.error('Chat error:', err)
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Error: Could not get response from backend.",
        createdAt: new Date()
      }])
    } finally {
      setIsLoading(false)
      setIsTyping(false)
    }
  }

  const stop = () => {
    setIsLoading(false)
    setIsTyping(false)
  }

  const isEmpty = messages.length === 0

  const handleSelectConversation = (conversation) => {
    console.log('Selecting conversation:', conversation)
    setSelectedConversation(conversation)
    if (conversation === null) {
      // Clear messages to show welcome screen
      setMessages([])
    }
    // If conversation is selected, loadMessages useEffect will handle loading the messages
  }

  const handleNewConversation = () => {
    setSelectedConversation(null)
    setMessages([])
  }

  const handleDeleteConversation = async (conversationId) => {
    try {
      const response = await fetch('http://localhost:8000/chat/delete_conversation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: conversationId })
      })
      
      if (response.ok) {
        // Remove from conversations list
        setConversations(prev => prev.filter(conv => conv.conversation_id !== conversationId))
        
        // If this was the selected conversation, clear it
        if (selectedConversation?.conversation_id === conversationId) {
          setSelectedConversation(null)
          setMessages([])
        }
      } else {
        console.error('Failed to delete conversation')
      }
    } catch (error) {
      console.error('Error deleting conversation:', error)
    }
  }

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInHours = (now - date) / (1000 * 60 * 60)
    
    if (diffInHours < 1) {
      return 'Just now'
    } else if (diffInHours < 24) {
      const hours = Math.floor(diffInHours)
      return `${hours}h ago`
    } else if (diffInHours < 48) {
      return '1d ago'
    } else {
      const days = Math.floor(diffInHours / 24)
      return `${days}d ago`
    }
  }

  const sortConversationsByDate = (conversations) => {
    return [...conversations].sort((a, b) => {
      return new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at)
    })
  }

  return (
    <div className="flex h-screen bg-white">
      <Sidebar 
        conversations={sortConversationsByDate(conversations)}
        isLoading={isLoadingConversations}
        selectedConversation={selectedConversation}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        onRefreshConversations={loadConversations}
        formatTimestamp={formatTimestamp}
      />
      <div className="flex-1 flex flex-col items-center justify-center w-full h-screen">
        <div
          className="flex flex-col min-h-0 w-full h-full items-center justify-center"
          style={{ aspectRatio: '16/10', maxWidth: '100vw', maxHeight: '100vh' }}
        >
          <ChatContainer className="flex flex-col h-full w-full">
            {isEmpty ? (
              <WelcomeScreen
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
                modelOptions={modelOptions}
                append={append}
                handleSubmit={handleSubmit}
                input={input}
                handleInputChange={handleInputChange}
                isLoading={isLoading}
                isTyping={isTyping}
                stop={stop}
              />
            ) : (
              <ChatInterface
                selectedConversation={selectedConversation}
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
                modelOptions={modelOptions}
                messages={messages}
                isTyping={isTyping}
                handleSubmit={handleSubmit}
                input={input}
                handleInputChange={handleInputChange}
                isLoading={isLoading}
                stop={stop}
                messagesContainerRef={messagesContainerRef}
              />
            )}
          </ChatContainer>
        </div>
      </div>
    </div>
  )
}