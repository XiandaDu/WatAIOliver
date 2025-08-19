export function extractHtml(content) {
  if (!content) return null;

  // DEBUG: Log what extractHtml receives
  console.log("=== EXTRACT HTML INPUT ===");
  console.log("Content received:", content.substring(0, 500));
  console.log("==========================");

  const fence = content.match(/```html\s*([\s\S]*?)```/i);
  if (fence && fence[1] && fence[1].trim()) {
    console.log("=== HTML EXTRACTED ===");
    console.log("Extracted HTML:", fence[1].trim().substring(0, 300));
    console.log("=====================");
    return fence[1].trim();
  }

  const trimmed = String(content).trim();
  const looksLikeHtml =
    /^<!doctype html>/i.test(trimmed) ||
    /^<html[\s>]/i.test(trimmed) ||
    (/<head[\s>]/i.test(trimmed) && /<body[\s>]/i.test(trimmed));

  if (looksLikeHtml) {
    console.log("=== DETECTED AS HTML ===");
    console.log("Will render as HTML instead of Markdown");
    console.log("========================");
    return trimmed;
  }

  const anyFence = content.match(/```([\s\S]*?)```/);
  if (anyFence && anyFence[1]) {
    const raw = anyFence[1].trim();
    if (/<(html|head|body|div|section|article|main|header|footer)[\s>]/i.test(raw)) {
      console.log("=== DETECTED HTML IN FENCE ===");
      console.log("Extracted from fence:", raw.substring(0, 300));
      console.log("===============================");
      return raw;
    }
  }
  
  console.log("=== NO HTML DETECTED ===");
  console.log("Will use MarkdownRenderer");
  console.log("========================");
  return null;
}
