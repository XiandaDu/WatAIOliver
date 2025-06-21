import { useState, useRef } from "react"
import { cn } from "@/lib/utils"

export function DragDropZone({ onFilesDrop, acceptedFileTypes = "*", multiple = true, className }) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
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
      // Filter files by accepted types if specified
      const filteredFiles = acceptedFileTypes === "*" 
        ? files 
        : files.filter(file => {
            const extension = file.name.split('.').pop().toLowerCase()
            return acceptedFileTypes.includes(extension)
          })

      if (filteredFiles.length === 0) {
        console.log("No valid files found")
        setIsUploading(false)
        return
      }

      // Call the parent handler
      await onFilesDrop(filteredFiles)
    } catch (error) {
      console.error("Error handling files:", error)
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
        {/* Upload Icon */}
        <div className="mb-4">
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

        {/* Text Content */}
        <div className="space-y-2">
          <p className={cn(
            "text-lg font-medium transition-colors",
            isDragOver ? "text-blue-600" : "text-gray-700"
          )}>
            {isUploading ? "Uploading..." : "Drop files here or click to browse"}
          </p>
          <p className="text-sm text-gray-500">
            {acceptedFileTypes === "*" 
              ? "All file types accepted" 
              : `Accepted formats: ${acceptedFileTypes.join(", ")}`
            }
          </p>
          {multiple && (
            <p className="text-xs text-gray-400">
              You can select multiple files
            </p>
          )}
        </div>

        {/* Drag Overlay */}
        {isDragOver && (
          <div className="absolute inset-0 bg-blue-500/10 rounded-lg border-2 border-blue-500 border-dashed flex items-center justify-center">
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