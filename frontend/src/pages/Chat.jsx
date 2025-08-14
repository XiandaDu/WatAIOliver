"use client"

import { useState, useRef, useEffect } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { ChatContainer } from "@/components/ui/chat"
import { Button } from "@/components/ui/button"
import { Sidebar } from "@/components/Sidebar"
import { WelcomeScreen } from "@/components/WelcomeScreen"
import { ChatInterface } from "@/components/ChatInterface"
import { extractHtml } from "@/lib/extractHtml";

export default function ChatPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [conversations, setConversations] = useState([])
  const [isLoadingConversations, setIsLoadingConversations] = useState(true)
  // Track loading states per conversation
  const [conversationLoadingStates, setConversationLoadingStates] = useState({})
  const [isSendingMessage, setIsSendingMessage] = useState(false)
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const [selectedModel, setSelectedModel] = useState("rag")
  const [selectedBaseModel, setSelectedBaseModel] = useState("gemini-2.5-flash")
  const [selectedRagModel, setSelectedRagModel] = useState("text-embedding-004")
  const [selectedHeavyModel, setSelectedHeavyModel] = useState("")
  const [selectedCourseId, setSelectedCourseId] = useState("")
  const [selectedCourse, setSelectedCourse] = useState(null)
  const [useAgents, setUseAgents] = useState(false)
  const modelOptions = [
    { label: "Daily", value: "daily", description: "RAG-enhanced response with course-specific prompt" },
    { label: "Problem Solving", value: "rag", description: "Multi-agent system with built-in RAG for complex problems" }
  ]
  const ragModelOptions = [
    { label: "Gemini 004", value: "text-embedding-004", description: "Google's latest embedding model (Default)" },
    { label: "Gemini 001", value: "gemini-embedding-001", description: "Google's legacy embedding model" },
    { label: "OpenAI Small", value: "text-embedding-3-small", description: "Fast and cost-effective OpenAI embedding" },
    { label: "OpenAI Large", value: "text-embedding-3-large", description: "High-quality OpenAI embedding model" },
    { label: "OpenAI Ada", value: "text-embedding-ada-002", description: "OpenAI's legacy embedding model" }
  ]
  const baseModelOptions = [
    { label: "Gemini Flash", value: "gemini-2.5-flash", description: "Google's fast and efficient model (Default)" },
    { label: "Cerebras Qwen MoE", value: "qwen-3-235b-a22b-instruct-2507", description: "Fast Mixture-of-Experts model from Cerebras" },
    { label: "GPT-4.1 Mini", value: "gpt-4.1-mini", description: "Lightweight version of OpenAI's GPT-4.1" }
  ]
  const heavyModelOptions = [
    { label: "None", value: "", description: "Use base model only (Default)" },
    { label: "Gemini Pro", value: "gemini-2.5-pro", description: "Google's most capable model for complex reasoning" },
    { label: "GPT-4o", value: "gpt-4o", description: "OpenAI's optimized model for speed and quality" },
    { label: "Claude Sonnet", value: "claude-3-sonnet-20240229", description: "Anthropic's balanced model for nuanced tasks" }
  ]

  const [userId, setUserId] = useState(null);
  const [userRole, setUserRole] = useState(null);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (!userData) {
      navigate('/login');
      return;
    }
    
    const user = JSON.parse(userData);
    if (!user.id) {
      console.error('No user ID found in stored user data');
      navigate('/login');
      return;
    }
    
    setUserId(user.id);
    setUserRole(user.role);
  }, [navigate]);

  useEffect(() => {
    if (userId) {
      loadConversations()
    }
  }, [userId])

  useEffect(() => {
    const courseParam = searchParams.get('course') || searchParams.get('course_id')
    if (courseParam) {
      setSelectedCourseId(courseParam)
      console.log('Course ID loaded from URL:', courseParam)
      
      // Fetch course details
      fetch(`http://localhost:8000/course/${courseParam}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }

      })
        .then(response => response.json())
        .then(course => {
          setSelectedCourse(course)
          console.log('Course details loaded:', course)
        })
        .catch(error => {
          console.error('Error loading course details:', error)
        })
    }
  }, [searchParams])

  useEffect(() => {
    // Don't load messages if we're currently sending a message
    if (isSendingMessage) {
      console.log('Skipping message load - currently sending message')
      return
    }
    
    if (selectedConversation) {
      loadMessages(selectedConversation.conversation_id)
    } else {
      setMessages([])
    }
  }, [selectedConversation, isSendingMessage])

  // Get loading state for current conversation
  const getCurrentConversationLoadingState = () => {
    if (!selectedConversation) return { isLoading: false, isTyping: false }
    return conversationLoadingStates[selectedConversation.conversation_id] || { isLoading: false, isTyping: false }
  }

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
        const transformedMessages = data.map(msg => {
          const maybeHtml = msg.sender === "assistant" ? extractHtml(msg.content) : null;
          return {
            id: msg.message_id,
            role: msg.sender,
            content: msg.content,
            createdAt: new Date(msg.created_at),
            meta: maybeHtml ? { type: "html", html: maybeHtml } : undefined
          };
        });        
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

    console.log('Submit - Input value:', input)
    console.log('Submit - Input trimmed:', input.trim())
    console.log('Submit - Has attachments:', experimental_attachments?.length > 0)

    setIsSendingMessage(true)

    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim() || (experimental_attachments?.length ? "Please analyze the uploaded file." : ""),
      createdAt: new Date(),
      experimental_attachments: experimental_attachments ? Array.from(experimental_attachments).map(file => ({
        name: file.name,
        url: URL.createObjectURL(file),
        type: file.type,
        size: file.size
      })) : null
    }
    
    console.log('User message content:', userMessage.content)
    
    setMessages(prev => [...prev, userMessage])
    setInput("")
    
    // Set loading state for current conversation
    const currentConversationId = selectedConversation?.conversation_id
    let newConversationId = currentConversationId // Declare at function level
    
    if (currentConversationId) {
      setConversationLoadingStates(prev => ({
        ...prev,
        [currentConversationId]: { isLoading: true, isTyping: true }
      }))
    } else {
      setIsLoading(true)
      setIsTyping(true)
    }

    try {
      // If no conversation is selected, create a new one
      if (!newConversationId) {
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
          newConversationId = conversationData[0]?.conversation_id
          
          if (newConversationId) {
            const newConversation = {
              conversation_id: newConversationId,
              title: input || (experimental_attachments?.length ? 'File Upload' : 'New Chat'),
              course_id: selectedModel === "rag" ? selectedCourseId : null,
              user_id: userId,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
            setSelectedConversation(newConversation)
            setConversations(prev => [newConversation, ...prev])
            
            // Set loading state for the new conversation
            setConversationLoadingStates(prev => ({
              ...prev,
              [newConversationId]: { isLoading: true, isTyping: true }
            }))
          }
        }
      }

      // Handle file uploads if present - this can take a long time
      // Handle file attachments and extract content for context
      let fileContext = ""
      if (experimental_attachments?.length && newConversationId) {
        const formData = new FormData()
        formData.append('conversation_id', newConversationId)
        formData.append('user_id', userId)
        
        for (const file of experimental_attachments) {
          formData.append('files', file)
        }
        
        try {
          console.log('Starting file upload...')
          const uploadResponse = await fetch('http://localhost:8000/chat/upload_files', {
            method: 'POST',
            body: formData,
            signal: AbortSignal.timeout(300000)
          })
          
          if (uploadResponse.ok) {
            const uploadData = await uploadResponse.json()
            console.log('File upload completed successfully')
            
            // Extract file content for context
            const fileContents = []
            for (const result of uploadData.results) {
              if (result.status === 'completed') {
                if (result.type === 'pdf' && result.markdown_content) {
                  fileContents.push(`File: ${result.filename}\nContent:\n${result.markdown_content}`)
                } else if (result.type === 'text' && result.text_content) {
                  fileContents.push(`File: ${result.filename}\nContent:\n${result.text_content}`)
                }
              }
            }
            
            if (fileContents.length > 0) {
              fileContext = fileContents.join('\n\n---\n\n')
            }
          } else {
            console.error('File upload failed:', uploadResponse.status, uploadResponse.statusText)
          }
        } catch (uploadError) {
          console.error('File upload error:', uploadError)
        }
      }

      // Save user message
      if (newConversationId) {
        try {
          await fetch('http://localhost:8000/chat/create_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message_id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              conversation_id: newConversationId,
              user_id: userId,
              sender: 'user',
              content: input.trim() || (experimental_attachments?.length ? 'Please analyze the uploaded file.' : ''),
              course_id: selectedCourseId || null,  // Always save course_id if available
              model: selectedBaseModel
            })
          })
        } catch (messageError) {
          console.error('Failed to save user message:', messageError)
          // Continue anyway, the message is already in the UI
        }
      }

      // Get AI response
      let aiResponse = "I'm processing your request..."
      try {
        const chatRequestData = {
          prompt: input.trim() || (experimental_attachments?.length ? 'Please help me analyze the uploaded file.' : ''),
          conversation_id: newConversationId,
          file_context: fileContext || null,
          model: selectedBaseModel,
          mode: selectedModel,
          course_id: selectedCourseId,
          rag_model: selectedRagModel,
          heavy_model: useAgents ? selectedHeavyModel : null,
          use_agents: useAgents
        }
        
        console.log('=== CHAT REQUEST DEBUG ===')
        console.log('selectedModel:', selectedModel)
        console.log('useAgents:', useAgents)
        console.log('Full request:', chatRequestData)
        console.log('==========================')
        

        
        const chatResponse = await fetch("http://localhost:8000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(chatRequestData)
        })
        
        if (chatResponse.ok) {
          const chatData = await chatResponse.json()
          aiResponse = chatData.result || "No response from AI"
        } else {
          console.error('Chat API error:', chatResponse.status, chatResponse.statusText)
          aiResponse = "I'm sorry, I encountered an error while processing your request. Please try again."
        }
      } catch (chatError) {
        console.error('Chat error:', chatError)
        aiResponse = "I'm sorry, I encountered an error while processing your request. Please try again."
      }

      // Save AI response
      if (newConversationId) {
        try {
          await fetch('http://localhost:8000/chat/create_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message_id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              conversation_id: newConversationId,
              user_id: userId,
              sender: 'assistant',
              content: aiResponse,
              course_id: selectedCourseId || null,  // Always save course_id if available
              model: selectedBaseModel
            })
          })
        } catch (saveError) {
          console.error('Failed to save AI response:', saveError)
          // Continue anyway, the response is already in the UI
        }
      }

      // Add AI response to messages
      const maybeHtml = extractHtml(aiResponse);
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: aiResponse,
        createdAt: new Date(),
        meta: maybeHtml ? { type: "html", html: maybeHtml } : undefined
      };
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
      // Clear loading state for the conversation that was actually used
      if (newConversationId) {
        setConversationLoadingStates(prev => ({
          ...prev,
          [newConversationId]: { isLoading: false, isTyping: false }
        }))
      } else if (currentConversationId) {
        setConversationLoadingStates(prev => ({
          ...prev,
          [currentConversationId]: { isLoading: false, isTyping: false }
        }))
      } else {
        setIsLoading(false)
        setIsTyping(false)
      }
      setIsSendingMessage(false)
    }
  }

  const append = async (message) => {
    setIsSendingMessage(true)
    

    
    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content: message.content,
      createdAt: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    
    // Set loading state for current conversation
    const currentConversationId = selectedConversation?.conversation_id
    let newConversationId = currentConversationId // Declare at function level
    
    if (currentConversationId) {
      setConversationLoadingStates(prev => ({
        ...prev,
        [currentConversationId]: { isLoading: true, isTyping: true }
      }))
    } else {
      setIsLoading(true)
      setIsTyping(true)
    }
    
    try {
      // If no conversation is selected, create a new one
      if (!newConversationId) {
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
          newConversationId = conversationData[0]?.conversation_id
          
          if (newConversationId) {
            const newConversation = {
              conversation_id: newConversationId,
              title: message.content.length > 50 ? message.content.substring(0, 50) + '...' : message.content,
              user_id: userId,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
            setSelectedConversation(newConversation)
            setConversations(prev => [newConversation, ...prev])
            
            // Set loading state for the new conversation
            setConversationLoadingStates(prev => ({
              ...prev,
              [newConversationId]: { isLoading: true, isTyping: true }
            }))
          }
        }
      }

      // Save user message
      if (newConversationId) {
        await fetch('http://localhost:8000/chat/create_message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message_id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            conversation_id: newConversationId,
            user_id: userId,
            sender: 'user',
            content: message.content,
            course_id: selectedCourseId || null,  // Always save course_id if available
            model: selectedBaseModel
          })
        })
      }

      // Get AI response
      const chatResponse = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: message.content,
          conversation_id: newConversationId,
          model: selectedBaseModel,
          mode: selectedModel,
          course_id: selectedCourseId,
          rag_model: selectedRagModel,
          heavy_model: useAgents ? selectedHeavyModel : null,
          use_agents: useAgents
        })
      })
      
      const chatData = await chatResponse.json()
      const aiResponse = chatData.result || "No response from AI"

      // Save AI response
      if (newConversationId) {
        await fetch('http://localhost:8000/chat/create_message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: newConversationId,
            user_id: userId,
            sender: 'assistant',
            content: aiResponse,
            course_id: selectedCourseId || null,  // Always save course_id if available
            model: selectedBaseModel
          })
        })
      }

      const maybeHtml = extractHtml(aiResponse);
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: aiResponse,
        createdAt: new Date(),
        meta: maybeHtml ? { type: "html", html: maybeHtml } : undefined
      };
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
      // Clear loading state for the conversation that was actually used
      if (newConversationId) {
        setConversationLoadingStates(prev => ({
          ...prev,
          [newConversationId]: { isLoading: false, isTyping: false }
        }))
      } else if (currentConversationId) {
        setConversationLoadingStates(prev => ({
          ...prev,
          [currentConversationId]: { isLoading: false, isTyping: false }
        }))
      } else {
        setIsLoading(false)
        setIsTyping(false)
      }
      setIsSendingMessage(false)
    }
  }

  const stop = () => {
    // Clear loading state for current conversation
    const currentConversationId = selectedConversation?.conversation_id
    if (currentConversationId) {
      setConversationLoadingStates(prev => ({
        ...prev,
        [currentConversationId]: { isLoading: false, isTyping: false }
      }))
    } else {
      setIsLoading(false)
      setIsTyping(false)
    }
  }

  const isEmpty = messages.length === 0 && !selectedConversation

  const handleSelectConversation = (conversation) => {
    console.log('Selecting conversation:', conversation)
    setSelectedConversation(conversation)
    if (conversation === null) {
      // Only clear messages if we're explicitly selecting no conversation
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
        
        // Remove loading state for deleted conversation
        setConversationLoadingStates(prev => {
          const newState = { ...prev }
          delete newState[conversationId]
          return newState
        })
        
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

  // Get current loading states
  const currentLoadingState = getCurrentConversationLoadingState()

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
        {/* Navigation and Logout Buttons */}
        <div className="absolute top-4 right-4 z-10 flex space-x-2">
          {/* Back to Admin Panel - Only for instructors/admins */}
          {(userRole === 'instructor' || userRole === 'admin') && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/admin')}
              className="bg-white/90 backdrop-blur-sm border-gray-300 hover:bg-gray-50"
            >
              ← Admin Panel
            </Button>
          )}
          
          {/* Back to Course Selection - Only for students */}
          {userRole === 'student' && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/courses')}
              className="bg-white/90 backdrop-blur-sm border-gray-300 hover:bg-gray-50"
            >
              ← Course Selection
            </Button>
          )}
          
          {/* Logout - For everyone */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              localStorage.removeItem('user');
              localStorage.removeItem('access_token');
              navigate('/login');
            }}
            className="bg-white/90 backdrop-blur-sm border-red-300 hover:bg-red-50 text-red-600 hover:text-red-700"
          >
            Logout
          </Button>
        </div>
        <div className="flex flex-col min-h-0 w-full h-full items-center justify-center max-w-full">
          <ChatContainer className="flex flex-col h-full w-full">
            {messages.length === 0 ? (
              <WelcomeScreen
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
                modelOptions={modelOptions}
                selectedBaseModel={selectedBaseModel}
                setSelectedBaseModel={setSelectedBaseModel}
                baseModelOptions={baseModelOptions}
                selectedRagModel={selectedRagModel}
                setSelectedRagModel={setSelectedRagModel}
                ragModelOptions={ragModelOptions}
                selectedHeavyModel={selectedHeavyModel}
                setSelectedHeavyModel={setSelectedHeavyModel}
                heavyModelOptions={heavyModelOptions}
                selectedCourseId={selectedCourseId}
                setSelectedCourseId={setSelectedCourseId}
                selectedCourse={selectedCourse}
                useAgents={useAgents}
                setUseAgents={setUseAgents}
                append={append}
                handleSubmit={handleSubmit}
                input={input}
                handleInputChange={handleInputChange}
                isLoading={currentLoadingState.isLoading}
                isTyping={currentLoadingState.isTyping}
                stop={stop}
              />
            ) : (
              <ChatInterface
                selectedConversation={selectedConversation}
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
                modelOptions={modelOptions}
                selectedBaseModel={selectedBaseModel}
                setSelectedBaseModel={setSelectedBaseModel}
                baseModelOptions={baseModelOptions}
                selectedRagModel={selectedRagModel}
                setSelectedRagModel={setSelectedRagModel}
                ragModelOptions={ragModelOptions}
                selectedHeavyModel={selectedHeavyModel}
                setSelectedHeavyModel={setSelectedHeavyModel}
                heavyModelOptions={heavyModelOptions}
                selectedCourseId={selectedCourseId}
                setSelectedCourseId={setSelectedCourseId}
                selectedCourse={selectedCourse}
                useAgents={useAgents}
                setUseAgents={setUseAgents}
                messages={messages}
                isTyping={currentLoadingState.isTyping}
                handleSubmit={handleSubmit}
                input={input}
                handleInputChange={handleInputChange}
                isLoading={currentLoadingState.isLoading}
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