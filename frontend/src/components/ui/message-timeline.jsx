import React, { useState, useMemo } from 'react'

export function MessageTimeline({ messages, onDateFilter }) {
  const [selectedDate, setSelectedDate] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedMessages, setExpandedMessages] = useState(new Set())

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
    
    const diffTime = today - messageDate
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined 
    })
  }

  const getTimeLabel = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    })
  }

  const toggleMessageExpansion = (messageId) => {
    const newExpanded = new Set(expandedMessages)
    if (newExpanded.has(messageId)) {
      newExpanded.delete(messageId)
    } else {
      newExpanded.add(messageId)
    }
    setExpandedMessages(newExpanded)
  }

  const findBotResponse = (userMessage) => {
    if (!messages || !userMessage.conversation_id) return null
    
    const userMessageTime = new Date(userMessage.created_at)
    const botResponse = messages.find(msg => 
      msg.sender === 'assistant' && 
      msg.conversation_id === userMessage.conversation_id &&
      new Date(msg.created_at) > userMessageTime
    )
    return botResponse
  }

  const messagesByDate = useMemo(() => {
    if (!messages) return {}
    
    const filtered = messages.filter(msg => 
      msg.sender === 'user' && 
      (searchTerm === '' || msg.content.toLowerCase().includes(searchTerm.toLowerCase()))
    )
    
    return filtered.reduce((acc, message) => {
      const date = new Date(message.created_at).toDateString()
      if (!acc[date]) {
        acc[date] = []
      }
      acc[date].push(message)
      return acc
    }, {})
  }, [messages, searchTerm])

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Student Questions Timeline</h2>
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Search questions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="space-y-8">
        {Object.entries(messagesByDate)
          .sort(([a], [b]) => new Date(b) - new Date(a))
          .map(([date, dayMessages]) => (
            <div key={date} className="relative">
              <div className="flex items-center mb-4">
                <div className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium">
                  {formatDate(date)}
                </div>
                <div className="ml-3 text-sm text-gray-500">
                  {dayMessages.length} question{dayMessages.length !== 1 ? 's' : ''}
                </div>
              </div>

              <div className="ml-6 space-y-4">
                {dayMessages
                  .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
                  .map((message, idx) => (
                    <div key={message.message_id || idx} className="relative">
                      <div className="absolute -left-6 top-0 w-px h-full bg-gray-200"></div>
                      <div className="absolute -left-8 top-2 w-4 h-4 bg-blue-500 rounded-full border-2 border-white shadow"></div>
                      
                      <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-sm font-medium text-blue-600">
                            {getTimeLabel(message.created_at)}
                          </span>
                          {message.model && (
                            <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                              {message.model}
                            </span>
                          )}
                        </div>
                        <p className="text-gray-800 leading-relaxed mb-3">
                          {message.content}
                        </p>
                        
                        <div className="flex justify-between items-center">
                          {message.conversation_id && (
                            <div className="text-xs text-gray-500">
                              Conversation: {message.conversation_id.slice(0, 8)}...
                            </div>
                          )}
                          
                          {findBotResponse(message) && (
                            <button
                              onClick={() => toggleMessageExpansion(message.message_id)}
                              className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full hover:bg-blue-200 transition-colors"
                            >
                              {expandedMessages.has(message.message_id) ? 'Hide Response' : 'Show Bot Response'}
                            </button>
                          )}
                        </div>
                        
                        {expandedMessages.has(message.message_id) && findBotResponse(message) && (
                          <div className="mt-3 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-300">
                            <div className="text-xs font-medium text-blue-800 mb-2">Bot Response:</div>
                            <p className="text-gray-700 text-sm leading-relaxed">
                              {findBotResponse(message).content}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
      </div>

      {Object.keys(messagesByDate).length === 0 && (
        <div className="text-center py-12 text-gray-500">
          {searchTerm ? 'No questions found matching your search.' : 'No student questions found.'}
        </div>
      )}
    </div>
  )
}

export function MessageStats({ messages }) {
  const stats = useMemo(() => {
    if (!messages) return {}
    
    const userMessages = messages.filter(msg => msg.sender === 'user')
    const today = new Date()
    const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())
    
    const todayMessages = userMessages.filter(msg => 
      new Date(msg.created_at) >= todayStart
    )
    
    const hourCounts = {}
    userMessages.forEach(msg => {
      const hour = new Date(msg.created_at).getHours()
      hourCounts[hour] = (hourCounts[hour] || 0) + 1
    })
    
    const peakHour = Object.entries(hourCounts)
      .sort(([,a], [,b]) => b - a)[0]?.[0]
    
    const modelCounts = {}
    messages.forEach(msg => {
      if (msg.model) {
        modelCounts[msg.model] = (modelCounts[msg.model] || 0) + 1
      }
    })
    
    return {
      totalQuestions: userMessages.length,
      todayQuestions: todayMessages.length,
      peakHour: peakHour ? `${String(peakHour).padStart(2, '0')}:00` : 'N/A',
      topModel: Object.entries(modelCounts)
        .sort(([,a], [,b]) => b - a)[0]?.[0] || 'N/A'
    }
  }, [messages])

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-blue-50 rounded-lg p-4 text-center">
        <div className="text-2xl font-bold text-blue-600">{stats.totalQuestions}</div>
        <div className="text-sm text-blue-800">Total Questions</div>
      </div>
      <div className="bg-green-50 rounded-lg p-4 text-center">
        <div className="text-2xl font-bold text-green-600">{stats.todayQuestions}</div>
        <div className="text-sm text-green-800">Today</div>
      </div>
      <div className="bg-purple-50 rounded-lg p-4 text-center">
        <div className="text-2xl font-bold text-purple-600">{stats.peakHour}</div>
        <div className="text-sm text-purple-800">Peak Hour</div>
      </div>
      <div className="bg-orange-50 rounded-lg p-4 text-center">
        <div className="text-lg font-bold text-orange-600">{stats.topModel}</div>
        <div className="text-sm text-orange-800">Top Model</div>
      </div>
    </div>
  )
}
