import React from 'react'
import { cn } from "@/lib/utils"

export function HTMLRenderer({
  htmlContent,
  className,
  ...props
}) {
  if (!htmlContent) {
    return null
  }

  return (
    <div
      className={cn("html-response-wrapper", className)}
      dangerouslySetInnerHTML={{ __html: htmlContent }}
      {...props}
    />
  )
}

export default HTMLRenderer 