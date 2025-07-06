import { useCallback, useRef, useState } from "react"
import { toast } from "sonner"

export function useCopyToClipboard({
  text,
  copyMessage = "Copied to clipboard!"
}) {
  const [isCopied, setIsCopied] = useState(false)
  const timeoutRef = useRef(null)

  const handleCopy = useCallback(() => {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        toast.success(copyMessage)
        setIsCopied(true)
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
          timeoutRef.current = null
        }
        timeoutRef.current = setTimeout(() => {
          setIsCopied(false)
        }, 2000)
      })
      .catch(() => {
        toast.error("Failed to copy to clipboard.")
      })
  }, [text, copyMessage])

  return { isCopied, handleCopy }
}
