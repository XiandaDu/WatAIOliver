// API Service Layer for Past Conversations
const API_BASE_URL = 'http://localhost:8000'

// HTTP client configuration
const apiClient = {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: 'GET' })
  },

  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' })
  },
}

// Conversation API service
export const conversationAPI = {
  // Get all conversations for a user
  async getConversations(userId = 'user123') {
    try {
      const response = await apiClient.get(`/conversations/${userId}`)
      
      return {
        success: true,
        data: response,
        error: null
      }
    } catch (error) {
      return {
        success: false,
        data: [],
        error: error.message || 'Failed to fetch conversations'
      }
    }
  },

  // Create a new conversation
  async createConversation(conversationData) {
    try {
      const response = await apiClient.post('/conversations/', conversationData)
      
      return {
        success: true,
        data: response,
        error: null
      }
    } catch (error) {
      return {
        success: false,
        data: null,
        error: error.message || 'Failed to create conversation'
      }
    }
  },

  // Update a conversation
  async updateConversation(conversationId, updateData) {
    try {
      const response = await apiClient.put(`/conversations/${conversationId}`, updateData)
      
      return {
        success: true,
        data: response,
        error: null
      }
    } catch (error) {
      return {
        success: false,
        data: null,
        error: error.message || 'Failed to update conversation'
      }
    }
  },

  // Delete a conversation
  async deleteConversation(conversationId) {
    try {
      const response = await apiClient.delete(`/conversations/${conversationId}`)
      
      return {
        success: true,
        data: response,
        error: null
      }
    } catch (error) {
      return {
        success: false,
        data: null,
        error: error.message || 'Failed to delete conversation'
      }
    }
  },

  // Get messages for a conversation
  async getMessages(conversationId) {
    try {
      const response = await apiClient.get(`/chat/messages/${conversationId}`)
      
      return {
        success: true,
        data: response.data || response,
        error: null
      }
    } catch (error) {
      return {
        success: false,
        data: [],
        error: error.message || 'Failed to fetch messages'
      }
    }
  },

  // Create a new message
  async createMessage(messageData) {
    try {
      const response = await apiClient.post('/chat/create_message', messageData)
      
      return {
        success: true,
        data: response.data?.[0] || response,
        error: null
      }
    } catch (error) {
      return {
        success: false,
        data: null,
        error: error.message || 'Failed to create message'
      }
    }
  },

  // Send chat message and get AI response
  async sendChatMessage(prompt, conversationId = null, userId = 'user123') {
    try {
      // First, create or get conversation
      let currentConversationId = conversationId
      
      if (!currentConversationId) {
        // Create new conversation with first message as title
        const title = prompt.length > 50 ? prompt.substring(0, 50) + '...' : prompt
        const conversationResponse = await this.createConversation({
          title: title,
          user_id: userId
        })
        
        if (!conversationResponse.success) {
          throw new Error('Failed to create conversation')
        }
        
        currentConversationId = conversationResponse.data.conversation_id
      }

      // Save user message
      const userMessage = await this.createMessage({
        conversation_id: currentConversationId,
        user_id: userId,
        sender: 'user',
        content: prompt
      })

      if (!userMessage.success) {
        throw new Error('Failed to save user message')
      }

      // Get AI response from chat endpoint
      const chatResponse = await apiClient.post('/chat', { prompt: prompt })
      
      // Save AI response
      const aiMessage = await this.createMessage({
        conversation_id: currentConversationId,
        user_id: userId,
        sender: 'assistant',
        content: chatResponse.result || 'No response from AI'
      })

      if (!aiMessage.success) {
        throw new Error('Failed to save AI message')
      }

      return {
        success: true,
        data: {
          conversation_id: currentConversationId,
          user_message: userMessage.data,
          ai_message: aiMessage.data,
          ai_response: chatResponse.result
        },
        error: null
      }
    } catch (error) {
      return {
        success: false,
        data: null,
        error: error.message || 'Failed to send chat message'
      }
    }
  }
}

// Utility functions for conversation data
export const conversationUtils = {
  // Format timestamp for display
  formatTimestamp(timestamp) {
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
  },

  // Sort conversations by most recent
  sortConversationsByDate(conversations) {
    return [...conversations].sort((a, b) => {
      return new Date(b.updated_at) - new Date(a.updated_at)
    })
  },

  // Filter conversations by search term
  filterConversations(conversations, searchTerm) {
    if (!searchTerm.trim()) return conversations
    
    const term = searchTerm.toLowerCase()
    return conversations.filter(conversation => 
      conversation.title.toLowerCase().includes(term) ||
      (conversation.lastMessage && conversation.lastMessage.toLowerCase().includes(term))
    )
  }
}

export default conversationAPI 