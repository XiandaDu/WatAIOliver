"use client"

import { useState, useRef, useEffect } from "react"
import { ChatContainer, ChatForm, ChatMessages } from "@/components/ui/chat"
import { MessageInput } from "@/components/ui/message-input"
import { transcribeAudio } from "@/lib/utils/audio"
import { MessageList } from "@/components/ui/message-list"
import { PromptSuggestions } from "@/components/ui/prompt-suggestions"
import { Sidebar } from "@/components/Sidebar"

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [selectedConversation, setSelectedConversation] = useState(null)
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }

  const handleInputChange = (e) => {
    setInput(e.target.value)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      createdAt: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "This is a template response. The actual AI integration will be implemented later.",
        createdAt: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
      setIsLoading(false)
      setIsTyping(false)
    }, 1000)
  }

  const append = (message) => {
    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content: message.content,
      createdAt: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setIsTyping(true)

    setTimeout(() => {
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "This is a template response. The actual AI integration will be implemented later.",
        createdAt: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
      setIsLoading(false)
      setIsTyping(false)
    }, 1000)
  }

  const stop = () => {
    setIsLoading(false)
    setIsTyping(false)
  }

  const isEmpty = messages.length === 0

  const handleSelectConversation = (conversation) => {
    setSelectedConversation(conversation)
    if (conversation === null) {
      // Clear messages to show welcome screen
      setMessages([])
    } else {
      // Load conversation messages
      setMessages([
        {
          id: "1",
          role: "assistant",
          content: `Welcome to ${conversation.title}! How can I help you today?`,
          createdAt: new Date()
        }
      ])
    }
  }

  return (
    <div className="flex h-screen">
      <Sidebar onSelectConversation={handleSelectConversation} />
      <div className="flex-1 py-8 flex flex-col">
        <div className="max-w-4xl w-[800px] mx-auto bg-white rounded-lg border shadow-sm flex-1 flex flex-col min-h-0">
          <ChatContainer className="h-full flex flex-col ">
            {isEmpty ? (
              <div className="flex-1 flex flex-col items-center justify-center gap-8 p-8">
                <div className="text-center">
                  <h1 className="text-2xl font-semibold text-gray-900 mb-2">
                    Welcome to Oliver.
                  </h1>
                  <p className="text-gray-600">
                    Ask me anything about your course!
                  </p>
                </div>
                <PromptSuggestions
                  label="Get started with some examples"
                  append={append}
                  suggestions={[
                    "What was covered in yesterday's lesson?",
                    "Did Lecture 16 in ECE 108 cover cardinality?",
                    "How much time do I need to finish yesterday's lecture?"
                  ]}
                />
                <div className="w-full max-w-2xl pt-5">
                  <ChatForm
                    isPending={isLoading || isTyping}
                    handleSubmit={handleSubmit}
                  >
                    {({ files, setFiles }) => (
                      <MessageInput
                        value={input}
                        onChange={handleInputChange}
                        allowAttachments
                        files={files}
                        setFiles={setFiles}
                        stop={stop}
                        isGenerating={false}
                        transcribeAudio={transcribeAudio}
                        placeholder="Ask me about school..."
                      />
                    )}
                  </ChatForm>
                </div>
              </div>
            ) : (
              <>
                <div className="bg-white px-6 py-4 rounded-lg flex-shrink-0">
                  <h1 className="text-xl font-semibold text-gray-900">
                    Oliver Chat
                  </h1>
                </div>
                
                <div 
                  ref={messagesContainerRef}
                  className="flex-1 overflow-y-auto px-6 py-6 min-h-0"
                >
                  <ChatMessages className="py-6">
                    <div className="space-y-4">
                      <MessageList
                        messages={messages}
                        isTyping={isTyping}
                        showTimeStamps={true}
                        messageOptions={(message) => ({
                          className: message.role === "user" 
                            ? "bg-blue-500 text-white ml-auto rounded-2xl px-4 py-3 max-w-[75%]" 
                            : "bg-gray-100 text-gray-900 rounded-2xl px-4 py-3 max-w-[75%]"
                        })}
                      />
                    </div>
                    <div ref={messagesEndRef} />
                  </ChatMessages>
                </div>
                
                <div className="border-t bg-white rounded-b-lg p-4 flex-shrink-0">
                  <ChatForm
                    isPending={isLoading || isTyping}
                    handleSubmit={handleSubmit}
                  >
                    {({ files, setFiles }) => (
                      <MessageInput
                        value={input}
                        onChange={handleInputChange}
                        allowAttachments
                        files={files}
                        setFiles={setFiles}
                        stop={stop}
                        isGenerating={isLoading}
                        transcribeAudio={transcribeAudio}
                        placeholder="Ask about Waterloo..."
                      />
                    )}
                  </ChatForm>
                </div>
              </>
            )}
          </ChatContainer>
        </div>
      </div>
    </div>
  )
}