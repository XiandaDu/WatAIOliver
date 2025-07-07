"use client";
import React from "react"
import { FileIcon, FileText, Image, Download } from "lucide-react"
import { Button } from "./button"

export const ChatFileAttachment = ({ attachment }) => {
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileIcon = () => {
    if (attachment.type.startsWith("image/")) {
      return <Image className="h-4 w-4" />
    }
    if (attachment.type === "application/pdf" || attachment.name.toLowerCase().endsWith(".pdf")) {
      return <FileText className="h-4 w-4" />
    }
    return <FileIcon className="h-4 w-4" />
  }

  const getFileTypeColor = () => {
    if (attachment.type.startsWith("image/")) {
      return "bg-blue-50 border-blue-200 text-blue-700"
    }
    if (attachment.type === "application/pdf" || attachment.name.toLowerCase().endsWith(".pdf")) {
      return "bg-red-50 border-red-200 text-red-700"
    }
    return "bg-gray-50 border-gray-200 text-gray-700"
  }

  const handleDownload = () => {
    // Create a temporary link to download the file
    const link = document.createElement('a')
    link.href = attachment.url
    link.download = attachment.name
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className={`inline-flex items-center gap-2 rounded-lg border p-2 text-sm ${getFileTypeColor()}`}>
      <div className="flex items-center gap-2">
        {getFileIcon()}
        <div className="flex flex-col">
          <span className="font-medium truncate max-w-[200px]">
            {attachment.name}
          </span>
          <span className="text-xs opacity-70">
            {formatFileSize(attachment.size || 0)}
          </span>
        </div>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleDownload}
        className="h-6 w-6 p-0 hover:bg-white/50"
      >
        <Download className="h-3 w-3" />
      </Button>
    </div>
  )
} 