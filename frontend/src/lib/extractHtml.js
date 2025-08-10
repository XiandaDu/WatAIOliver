export function extractHtml(content) {
  if (!content) return null;

  const fence = content.match(/```html\s*([\s\S]*?)```/i);
  if (fence && fence[1] && fence[1].trim()) {
    return fence[1].trim();
  }

  const trimmed = String(content).trim();
  const looksLikeHtml =
    /^<!doctype html>/i.test(trimmed) ||
    /^<html[\s>]/i.test(trimmed) ||
    (/<head[\s>]/i.test(trimmed) && /<body[\s>]/i.test(trimmed));

  if (looksLikeHtml) return trimmed;

  const anyFence = content.match(/```([\s\S]*?)```/);
  if (anyFence && anyFence[1]) {
    const raw = anyFence[1].trim();
    if (/<(html|head|body|div|section|article|main|header|footer)[\s>]/i.test(raw)) {
      return raw;
    }
  }
  return null;
}
