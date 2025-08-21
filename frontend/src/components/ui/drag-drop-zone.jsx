import { useState, useRef } from "react"
import { cn } from "@/lib/utils"

export function DragDropZone({ onFilesDrop, acceptedFileTypes = "*", multiple = true, className }) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const fileInputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
    setErrorMessage("") // Clear error when user drags again
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    // Only set to false if we're actually leaving this element
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setIsDragOver(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    setIsUploading(true)

    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }

  const handleFileInput = (e) => {
    const files = Array.from(e.target.files)
    handleFiles(files)
  }

  const handleFiles = async (files) => {
    try {
      setErrorMessage("") // Clear any previous errors
      
      // Filter files by accepted types if specified
      const filteredFiles = acceptedFileTypes === "*" 
        ? files 
        : files.filter(file => {
            const extension = file.name.split('.').pop().toLowerCase()
            return acceptedFileTypes.includes(extension)
          })

      if (filteredFiles.length === 0) {
        const rejectedFiles = files.filter(file => {
          const extension = file.name.split('.').pop().toLowerCase()
          return !acceptedFileTypes.includes(extension)
        })
        
        if (rejectedFiles.length > 0) {
          const rejectedNames = rejectedFiles.map(f => f.name).join(", ")
          const supportedFormats = acceptedFileTypes === "*" 
            ? "All file types" 
            : acceptedFileTypes.join(", ").toUpperCase()
          setErrorMessage(`Unsupported file format(s): ${rejectedNames}. Supported formats: ${supportedFormats}`)
        }
        setIsUploading(false)
        return
      }

      // Call the parent handler
      await onFilesDrop(filteredFiles)
    } catch (error) {
      console.error("Error handling files:", error)
      setErrorMessage(`Error processing files: ${error.message}`)
    } finally {
      setIsUploading(false)
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className={cn("w-full", className)}>
      <div
        className={cn(
          "relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 cursor-pointer",
          "hover:border-blue-400 hover:bg-blue-50/50",
          isDragOver && "border-blue-500 bg-blue-100/50 scale-105",
          isUploading && "opacity-50 pointer-events-none"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        {/* Upload Icon - Hidden when dragging */}
        <div className={cn("mb-4 transition-opacity", isDragOver && "opacity-0")}>
          <div className={cn(
            "mx-auto w-16 h-16 rounded-full flex items-center justify-center transition-colors",
            isDragOver ? "bg-blue-100" : "bg-gray-100"
          )}>
            {isUploading ? (
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            ) : (
              <svg 
                className={cn(
                  "w-8 h-8 transition-colors",
                  isDragOver ? "text-blue-600" : "text-gray-400"
                )} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
                />
              </svg>
            )}
          </div>
        </div>

        {/* Text Content - Hidden when dragging */}
        <div className={cn("space-y-1 transition-opacity", isDragOver && "opacity-0")}>
          <p className={cn(
            "text-lg font-medium transition-colors",
            isDragOver ? "text-blue-600" : "text-gray-700"
          )}>
            {isUploading ? "Uploading..." : "Drop files here or click to browse"}
          </p>
          <p className="text-sm text-gray-500">
            {acceptedFileTypes === "*" 
              ? "All file types accepted" 
              : `Supports: ${acceptedFileTypes.join(", ").toUpperCase()}`
            }
          </p>
          
          {/* Error Message */}
          {errorMessage && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700 font-medium">
                ❌ {errorMessage}
              </p>
            </div>
          )}
        </div>

        {/* Drag Overlay - Only show when actively dragging */}
        {isDragOver && (
          <div className="absolute inset-0 bg-blue-500/10 rounded-lg border-2 border-blue-500 border-dashed flex items-center justify-center z-10">
            <div className="text-blue-600 font-medium text-lg">
              Drop files here!
            </div>
          </div>
        )}

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple={multiple}
          accept={acceptedFileTypes === "*" ? "*" : acceptedFileTypes.map(type => `.${type}`).join(",")}
          onChange={handleFileInput}
          className="hidden"
        />
      </div>
    </div>
  )
} 