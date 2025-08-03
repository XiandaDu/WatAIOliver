import { PromptSuggestions } from "@/components/ui/prompt-suggestions"
import { SelectWithInfo } from "@/components/ui/select-with-info"
import { CourseSelector } from "@/components/ui/course-selector"
import { ChatForm } from "@/components/ui/chat"
import { MessageInput } from "@/components/ui/message-input"
import { transcribeAudio } from "@/lib/utils/audio"

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
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">
          Welcome to Oliver.
        </h1>
        <p className="text-gray-600">
          Ask me anything about your course!
        </p>
        <div className="mt-4 flex flex-col items-center space-y-4">
          <SelectWithInfo
            label="Mode"
            value={selectedModel}
            onChange={setSelectedModel}
            options={modelOptions}
            placeholder="Select mode"
            className="w-48"
          />
          <SelectWithInfo
            label="Foundation Model"
            value={selectedBaseModel}
            onChange={setSelectedBaseModel}
            options={baseModelOptions}
            placeholder="Foundation model"
            className="w-48"
          />
          {selectedModel === "rag" && (
            <>
              <SelectWithInfo
                label="Embedding Model"
                value={selectedRagModel}
                onChange={setSelectedRagModel}
                options={ragModelOptions}
                placeholder="Embedding model"
                className="w-48"
              />
              <SelectWithInfo
                label="Heavy Reasoning Model"
                value={selectedHeavyModel}
                onChange={setSelectedHeavyModel}
                options={heavyModelOptions}
                placeholder="Heavy reasoning model"
                className="w-48"
              />
              <CourseSelector
                value={selectedCourseId}
                onChange={setSelectedCourseId}
                className="w-64"
              />
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