// Telegram bot webhook helpers. No imports.

/** Compare the X-Telegram-Bot-Api-Secret-Token header with the secret you set in setWebhook. */
export function checkSecretToken(headerValue: string | null, expected: string): boolean {
  if (!headerValue || !expected || headerValue.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= headerValue.charCodeAt(i) ^ expected.charCodeAt(i);
  return diff === 0;
}

/** Return the chat id and text of a plain text message, or null for anything else. */
export function extractTelegramText(update: unknown): { chatId: number; text: string } | null {
  const message = (update as { message?: { chat?: { id?: unknown }; text?: unknown } })?.message;
  if (!message || typeof message.text !== "string" || typeof message.chat?.id !== "number") return null;
  return { chatId: message.chat.id, text: message.text };
}
