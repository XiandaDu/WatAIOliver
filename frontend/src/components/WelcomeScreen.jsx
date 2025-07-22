import { PromptSuggestions } from "@/components/ui/prompt-suggestions"
import { CustomSelect } from "@/components/ui/custom-select"
import { CourseSelector } from "@/components/ui/course-selector"
import { ChatForm } from "@/components/ui/chat"
import { MessageInput } from "@/components/ui/message-input"
import { transcribeAudio } from "@/lib/utils/audio"

export function WelcomeScreen({ 
  selectedModel, 
  setSelectedModel, 
  modelOptions, 
  selectedCourseId,
  setSelectedCourseId,
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
        <div className="mt-4 flex flex-col items-center space-y-3">
          <CustomSelect
            value={selectedModel}
            onChange={setSelectedModel}
            options={modelOptions}
            placeholder="Select a model"
            className="w-48"
          />
          {selectedModel === "rag" && (
            <CourseSelector
              value={selectedCourseId}
              onChange={setSelectedCourseId}
              className="w-64"
            />
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