import { useState, useEffect, useCallback } from 'react'
import { conversationAPI, conversationUtils } from '@/lib/api'

export function useConversations(userId = 'user123') {
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  // Fetch conversations
  const fetchConversations = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      console.log('Fetching conversations for user:', userId)
      const result = await conversationAPI.getConversations(userId)
      
      console.log('Conversations result:', result)
      
      if (result.success) {
        const sortedConversations = conversationUtils.sortConversationsByDate(result.data)
        console.log('Sorted conversations:', sortedConversations)
        setConversations(sortedConversations)
      } else {
        console.error('Failed to fetch conversations:', result.error)
        setError(result.error)
        setConversations([])
      }
    } catch (err) {
      console.error('Error fetching conversations:', err)
      setError(err.message || 'Failed to fetch conversations')
      setConversations([])
    } finally {
      setLoading(false)
    }
  }, [userId])

  // Create new conversation
  const createConversation = useCallback(async (conversationData) => {
    try {
      console.log('Creating conversation:', conversationData)
      const result = await conversationAPI.createConversation(conversationData)
      
      console.log('Create conversation result:', result)
      
      if (result.success) {
        setConversations(prev => {
          const newConversations = [result.data, ...prev]
          return conversationUtils.sortConversationsByDate(newConversations)
        })
        return { success: true, data: result.data }
      } else {
        console.error('Failed to create conversation:', result.error)
        return { success: false, error: result.error }
      }
    } catch (err) {
      console.error('Error creating conversation:', err)
      return { success: false, error: err.message || 'Failed to create conversation' }
    }
  }, [])

  // Update conversation
  const updateConversation = useCallback(async (conversationId, updateData) => {
    try {
      console.log('Updating conversation:', conversationId, updateData)
      const result = await conversationAPI.updateConversation(conversationId, updateData)
      
      console.log('Update conversation result:', result)
      
      if (result.success) {
        setConversations(prev => 
          prev.map(conv => 
            conv.conversation_id === conversationId 
              ? { ...conv, ...updateData, updated_at: new Date().toISOString() }
              : conv
          )
        )
        return { success: true, data: result.data }
      } else {
        console.error('Failed to update conversation:', result.error)
        return { success: false, error: result.error }
      }
    } catch (err) {
      console.error('Error updating conversation:', err)
      return { success: false, error: err.message || 'Failed to update conversation' }
    }
  }, [])

  // Delete conversation
  const deleteConversation = useCallback(async (conversationId) => {
    try {
      console.log('Deleting conversation:', conversationId)
      const result = await conversationAPI.deleteConversation(conversationId)
      
      console.log('Delete conversation result:', result)
      
      if (result.success) {
        setConversations(prev => 
          prev.filter(conv => conv.conversation_id !== conversationId)
        )
        return { success: true }
      } else {
        console.error('Failed to delete conversation:', result.error)
        return { success: false, error: result.error }
      }
    } catch (err) {
      console.error('Error deleting conversation:', err)
      return { success: false, error: err.message || 'Failed to delete conversation' }
    }
  }, [])

  // Filter conversations based on search term
  const filteredConversations = conversationUtils.filterConversations(conversations, searchTerm)

  // Refresh conversations
  const refreshConversations = useCallback(() => {
    fetchConversations()
  }, [fetchConversations])

  // Initial fetch
  useEffect(() => {
    fetchConversations()
  }, [fetchConversations])

  return {
    conversations: filteredConversations,
    loading,
    error,
    searchTerm,
    setSearchTerm,
    createConversation,
    updateConversation,
    deleteConversation,
    refreshConversations,
    // Raw conversations (unfiltered) for other operations
    allConversations: conversations
  }
} 