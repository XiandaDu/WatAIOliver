import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"

export function CustomSelect({ 
  value, 
  onChange, 
  options, 
  placeholder = "Select an option",
  className,
  disabled = false 
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedOption, setSelectedOption] = useState(
    options.find(option => option.value === value) || null
  )
  const selectRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (selectRef.current && !selectRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    setSelectedOption(options.find(option => option.value === value) || null)
  }, [value, options])

  const handleSelect = (option) => {
    setSelectedOption(option)
    onChange(option.value)
    setIsOpen(false)
  }

  return (
    <div className={cn("relative", className)} ref={selectRef}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          "relative w-full bg-white border border-gray-300 rounded-lg px-4 py-2.5 text-left shadow-sm cursor-pointer transition-all duration-200",
          "hover:border-gray-400 hover:shadow-md",
          "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          isOpen && "ring-2 ring-blue-500 border-blue-500 shadow-md"
        )}
      >
        <span className={cn(
          "block truncate",
          selectedOption ? "text-gray-900" : "text-gray-500"
        )}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
          <svg
            className={cn(
              "h-5 w-5 text-gray-400 transition-transform duration-200",
              isOpen && "rotate-180"
            )}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </span>
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-auto">
          <div className="py-1">
            {options.map((option, index) => (
              <button
                key={option.value}
                type="button"
                onClick={() => handleSelect(option)}
                className={cn(
                  "relative w-full px-4 py-3 text-left cursor-pointer transition-colors duration-150",
                  "hover:bg-blue-50 hover:text-blue-900",
                  "focus:outline-none focus:bg-blue-50 focus:text-blue-900",
                  selectedOption?.value === option.value && "bg-blue-100 text-blue-900 font-medium"
                )}
              >
                <div className="flex flex-col space-y-1">
                  <span className="block truncate font-medium">{option.label}</span>
                  {option.description && (
                    <span className="text-xs text-gray-600 leading-tight">
                      {option.description}
                    </span>
                  )}
                </div>
                {selectedOption?.value === option.value && (
                  <span className="absolute inset-y-0 right-0 flex items-center pr-4">
                    <svg
                      className="h-5 w-5 text-blue-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
} 