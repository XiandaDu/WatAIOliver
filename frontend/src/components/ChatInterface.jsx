import { ChatForm, ChatMessages } from "@/components/ui/chat"
import { MessageInput } from "@/components/ui/message-input"
import { CustomSelect } from "@/components/ui/custom-select"
import { ChatFileAttachment } from "@/components/ui/chat-file-attachment"
import { transcribeAudio } from "@/lib/utils/audio"
import { MarkdownRenderer } from "@/components/ui/markdown-renderer"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { HtmlPreview } from "@/components/HtmlPreview"

export function ChatInterface({ 
  selectedConversation,
  selectedModel,
  setSelectedModel,
  modelOptions,
  selectedBaseModel,
  setSelectedBaseModel,
  baseModelOptions,
  selectedRagModel,
  setSelectedRagModel,
  ragModelOptions,
  selectedHeavyModel,
  setSelectedHeavyModel,
  heavyModelOptions,
  selectedCourseId,
  setSelectedCourseId,
  selectedCourse,
  useAgents,
  setUseAgents,
  messages,
  isTyping,
  handleSubmit,
  input,
  handleInputChange,
  isLoading,
  stop,
  messagesContainerRef
}) {
  const navigate = useNavigate()
  
  const handleLogout = () => {
    localStorage.removeItem('user')
    localStorage.removeItem('access_token')
    navigate('/login')
  }
  return (
    <>
      <div className="px-6 py-4 flex-shrink-0">
        <div className="flex flex-col items-start">
          <div className="flex justify-between items-center w-full mb-2">
            <h1 className="text-xl font-semibold text-gray-900">
              {selectedConversation ? selectedConversation.title : 'Oliver Chat'}
            </h1>
            <Button
              onClick={handleLogout}
              variant="outline"
              size="sm"
              className="text-red-600 border-red-300 hover:bg-red-50 hover:text-red-700"
            >
              Logout
            </Button>
          </div>
          <div className="mt-2 space-y-3">
            <CustomSelect
              value={selectedModel}
              onChange={setSelectedModel}
              options={modelOptions}
              placeholder="Select mode"
              className="w-40"
            />
            <CustomSelect
              value={selectedBaseModel}
              onChange={setSelectedBaseModel}
              options={baseModelOptions}
              placeholder="Foundation model"
              className="w-48"
            />
            {selectedModel === "daily" && (
              <>
                {selectedCourse && (
                  <div className="w-64 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                    <label className="block text-xs font-medium text-gray-700 mb-1">Course</label>
                    <p className="text-sm text-blue-700 font-medium">{selectedCourse.title}</p>
                    <p className="text-xs text-blue-600">{selectedCourse.term}</p>
                  </div>
                )}
              </>
            )}
            {selectedModel === "rag" && (
              <>
                <CustomSelect
                  value={selectedRagModel}
                  onChange={setSelectedRagModel}
                  options={ragModelOptions}
                  placeholder="Embedding model"
                  className="w-48"
                />
                <CustomSelect
                  value={selectedHeavyModel}
                  onChange={setSelectedHeavyModel}
                  options={heavyModelOptions}
                  placeholder="Heavy reasoning model"
                  className="w-48"
                />

                {selectedCourse && (
                  <div className="w-64 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                    <label className="block text-xs font-medium text-gray-700 mb-1">Course</label>
                    <p className="text-sm text-blue-700 font-medium">{selectedCourse.title}</p>
                    <p className="text-xs text-blue-600">{selectedCourse.term}</p>
                  </div>
                )}
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    className="form-checkbox h-4 w-4 text-blue-600"
                    checked={useAgents}
                    onChange={(e) => setUseAgents(e.target.checked)}
                  />
                  <span className="text-sm text-gray-700">Enable multi-agent debate</span>
                </label>
              </>
            )}
          </div>
        </div>
      </div>
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-8 py-8 min-h-0 bg-gradient-to-b from-gray-50 to-white"
        style={{ minHeight: 0 }}
      >
        <ChatMessages className="py-8">
          <div className="space-y-8">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`${
                  message.role === "user" ? "flex justify-end" : "flex justify-start"
                }`}
              >
                {message.role === "user" ? (
                  <div className="max-w-xs lg:max-w-md">
                    {/* Display file attachments if present */}
                    {message.experimental_attachments && message.experimental_attachments.length > 0 && (
                      <div className="mb-2 flex flex-wrap gap-2">
                        {message.experimental_attachments.map((attachment, index) => (
                          <ChatFileAttachment key={index} attachment={attachment} />
                        ))}
                      </div>
                    )}
                    {/* User message bubble */}
                    <div className="px-6 py-3 rounded-2xl bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg">
                      <span className="text-sm font-medium">{message.content}</span>
                    </div>
                  </div>
                ) : (
                  <div className="max-w-4xl w-full">
                    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
                      <div className="flex items-center mb-4">
                        <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mr-3">
                          {/* TODO: replace with oliver logo */}
                          <span className="text-white text-sm font-bold">O</span>
                        </div>
                        <span className="text-sm font-medium text-gray-600">Oliver Assistant</span>
                      </div>
                      {message?.meta?.type === "html" ? (
                        <HtmlPreview html={message.meta.html} />
                      ) : (
                        <div className="prose prose-lg max-w-none">
                          <MarkdownRenderer>{message.content}</MarkdownRenderer>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="max-w-4xl w-full">
                  <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
                    <div className="flex items-center mb-4">
                      <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mr-3">
                        {/* TODO: replace with oliver logo */}
                        <span className="text-white text-sm font-bold">O</span>
                      </div>
                      <span className="text-sm font-medium text-gray-600">Oliver Assistant</span>
                    </div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                    </div>
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
  )
} 