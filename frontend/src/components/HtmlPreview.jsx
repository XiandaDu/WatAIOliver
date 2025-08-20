import React, { useMemo, useState } from "react";

export function HtmlPreview({ html }) {
  const [view, setView] = useState("preview");

  const downloadUrl = useMemo(() => {
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    return URL.createObjectURL(blob);
  }, [html]);

  return (
    <div className="w-full border rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b bg-gray-50">
        <div className="text-xs font-medium">HTML</div>
        <div className="flex items-center gap-2">
          <button
            className={`text-xs px-2 py-1 rounded ${view === "preview" ? "bg-black text-white" : "bg-white border"}`}
            onClick={() => setView("preview")}
          >
            Preview
          </button>
          <button
            className={`text-xs px-2 py-1 rounded ${view === "code" ? "bg-black text-white" : "bg-white border"}`}
            onClick={() => setView("code")}
          >
            Code
          </button>
          <a
            href={downloadUrl}
            download="render.html"
            className="text-xs px-2 py-1 rounded border bg-white"
          >
            Download
          </a>
        </div>
      </div>

      {view === "preview" ? (
        <iframe
          title="HTML Preview"
          className="w-full h-[600px] bg-white"
          srcDoc={html}
          sandbox="allow-scripts allow-same-origin"
        />
      ) : (
        <pre className="p-4 text-sm overflow-auto">
          <code>{html}</code>
        </pre>
      )}
    </div>
  );
}
