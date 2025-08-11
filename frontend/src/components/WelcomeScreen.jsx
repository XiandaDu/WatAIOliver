import { PromptSuggestions } from "@/components/ui/prompt-suggestions"
import { CustomSelect } from "@/components/ui/custom-select"
import { CourseSelector } from "@/components/ui/course-selector"
import { ChatForm } from "@/components/ui/chat"
import { MessageInput } from "@/components/ui/message-input"
import { transcribeAudio } from "@/lib/utils/audio"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"

export function WelcomeScreen({ 
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
  useAgents,
  setUseAgents,
  append,
  handleSubmit,
  input, 
  handleInputChange, 
  isLoading, 
  isTyping, 
  stop 
}) {
  const navigate = useNavigate()
  
  const handleLogout = () => {
    localStorage.removeItem('user')
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-8 p-8 relative">
      <Button
        onClick={handleLogout}
        variant="outline"
        size="sm"
        className="absolute top-4 right-4 text-red-600 border-red-300 hover:bg-red-50"
      >
        Logout
      </Button>
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">
          Welcome to Oliver.
        </h1>
        <p className="text-gray-600">
          Ask me anything about your course!
        </p>
        <div className="mt-4 flex flex-col items-center space-y-4">
          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">Mode</label>
            <CustomSelect
              value={selectedModel}
              onChange={setSelectedModel}
              options={modelOptions}
              placeholder="Select mode"
            />
          </div>
          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">Foundation Model</label>
            <CustomSelect
              value={selectedBaseModel}
              onChange={setSelectedBaseModel}
              options={baseModelOptions}
              placeholder="Foundation model"
            />
          </div>
          {selectedModel === "rag" && (
            <>
              <div className="w-48">
                <label className="block text-sm font-medium text-gray-700 mb-1">Embedding Model</label>
                <CustomSelect
                  value={selectedRagModel}
                  onChange={setSelectedRagModel}
                  options={ragModelOptions}
                  placeholder="Embedding model"
                />
              </div>
              <div className="w-48">
                <label className="block text-sm font-medium text-gray-700 mb-1">Heavy Reasoning Model</label>
                <CustomSelect
                  value={selectedHeavyModel}
                  onChange={setSelectedHeavyModel}
                  options={heavyModelOptions}
                  placeholder="Heavy reasoning model"
                />
              </div>
              {selectedCourseId && (
                <div className="w-64 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Selected Course</label>
                  <p className="text-sm text-blue-700 font-medium">{selectedCourseId}</p>
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
  )
} 