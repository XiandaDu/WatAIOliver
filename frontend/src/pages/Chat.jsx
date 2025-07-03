"use client"

import { useState, useRef, useEffect } from "react"
import { ChatContainer, ChatForm, ChatMessages } from "@/components/ui/chat"
import { MessageInput } from "@/components/ui/message-input"
import { transcribeAudio } from "@/lib/utils/audio"
import { MessageList } from "@/components/ui/message-list"
import { PromptSuggestions } from "@/components/ui/prompt-suggestions"
import { CustomSelect } from "@/components/ui/custom-select"
import { Sidebar } from "@/components/Sidebar"
import { marked } from "marked"

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [selectedConversation, setSelectedConversation] = useState(null)
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const [selectedModel, setSelectedModel] = useState("qwen")
  const modelOptions = [
    { label: "Qwen 3", value: "qwen" },
    { label: "Model 2", value: "model-2" }
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

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: input })
      })
      const data = await res.json()
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.result || "No result returned",
        createdAt: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
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
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: message.content })
      })
      const data = await res.json()
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.result || "No result returned",
        createdAt: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
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
                    <CustomSelect
                      value={selectedModel}
                      onChange={setSelectedModel}
                      options={modelOptions}
                      placeholder="Select a model"
                      className="w-48"
                    />
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
                    <div className="mt-2">
                      <CustomSelect
                        value={selectedModel}
                        onChange={setSelectedModel}
                        options={modelOptions}
                        placeholder="Select a model"
                        className="w-40"
                      />
                    </div>
                  </div>
                </div>
                <div
                  ref={messagesContainerRef}
                  className="flex-1 overflow-y-auto px-6 py-6 min-h-0"
                  style={{ minHeight: 0 }}
                >
                  <ChatMessages className="py-6">
                    <div className="space-y-4">
                      {messages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex ${
                            message.role === "user" ? "justify-end" : "justify-start"
                          }`}
                        >
                          <div
                            className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                              message.role === "user"
                                ? "bg-blue-500 text-white"
                                : "bg-gray-100 text-gray-900"
                            }`}
                          >
                            {message.role === "assistant" ? (
                              <div dangerouslySetInnerHTML={{ __html: marked.parse(message.content) }} />
                            ) : (
                              <span>{message.content}</span>
                            )}
                          </div>
                        </div>
                      ))}
                      {isTyping && (
                        <div className="flex justify-start">
                          <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg">
                            <div className="flex space-x-1">
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </ChatMessages>
                </div>
                <div className="px-6 py-4 flex-shrink-0">
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
              </>
            )}
          </ChatContainer>
        </div>
      </div>
    </div>
  )
}