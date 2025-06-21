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
  const [selectedModel, setSelectedModel] = useState("GPT-4")
  const modelOptions = [
    { label: "Model 1", value: "model-1" },
    { label: "Model 2", value: "model-2" },
    { label: "Model 3", value: "model-3" },
  ]

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
    <div className="flex h-screen bg-white">
      <Sidebar onSelectConversation={handleSelectConversation} />
      <div className="flex-1 flex flex-col items-center justify-center w-full h-screen">
        <div
          className="flex flex-col min-h-0 w-full h-full items-center justify-center"
          style={{ aspectRatio: '16/10', maxWidth: '100vw', maxHeight: '100vh' }}
        >
          <ChatContainer className="flex flex-col h-full w-full">
            {isEmpty ? (
              <div className="flex-1 flex flex-col items-center justify-center gap-8 p-8">
                <div className="text-center">
                  <h1 className="text-2xl font-semibold text-gray-900 mb-2">
                    Welcome to Oliver.
                  </h1>
                  <p className="text-gray-600">
                    Ask me anything about your course!
                  </p>
                  <div className="mt-4 flex flex-col items-center">
                    <select
                      id="model-select-empty"
                      value={selectedModel}
                      onChange={e => setSelectedModel(e.target.value)}
                      className="w-48 rounded-md border border-gray-300 bg-white py-2 px-3 text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      {modelOptions.map(option => (
                        <option key={option.value} value={option.label}>{option.label}</option>
                      ))}
                    </select>
                  </div>
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
                <div className="px-6 py-4 flex-shrink-0">
                  <div className="flex flex-col items-start">
                    <h1 className="text-xl font-semibold text-gray-900">Oliver Chat</h1>
                    <select
                      id="model-select"
                      value={selectedModel}
                      onChange={e => setSelectedModel(e.target.value)}
                      className="mt-2 w-40 rounded-md border border-gray-300 bg-white py-2 px-3 text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      {modelOptions.map(option => (
                        <option key={option.value} value={option.label}>{option.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div
                  ref={messagesContainerRef}
                  className="flex-1 overflow-y-auto px-6 py-6 min-h-0"
                  style={{ minHeight: 0 }}
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
                <div className="px-6 py-4 flex-shrink-0 bg-white mb-12">
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