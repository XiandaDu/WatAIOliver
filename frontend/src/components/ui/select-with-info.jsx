import { CustomSelect } from "./custom-select"

export function SelectWithInfo({ options, label, ...props }) {
  const hasDescriptions = options.some(option => option.description)
  
  return (
    <div className="relative">
      {label && (
        <div className="flex items-center gap-2 mb-1">
          <label className="text-sm font-medium text-gray-700">{label}</label>
          {hasDescriptions && (
            <div className="group relative">
              <svg className="w-4 h-4 text-gray-400 cursor-help" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 text-xs text-white bg-gray-900 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                Hover over options to see descriptions
              </div>
            </div>
          )}
        </div>
      )}
      <CustomSelect options={options} {...props} />
    </div>
  )
} 