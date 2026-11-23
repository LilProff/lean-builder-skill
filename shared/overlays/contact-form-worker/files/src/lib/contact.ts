// Contact form validation. No imports, so it runs anywhere (Workers, Node, browser).

export type ContactData = { name: string; email: string; message: string };
export type ContactResult = { ok: boolean; errors: string[]; data?: ContactData };

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const MAX_MESSAGE = 5000;

export function validateContact(body: unknown): ContactResult {
  if (typeof body !== "object" || body === null) {
    return { ok: false, errors: ["The form was empty."] };
  }
  const input = body as Record<string, unknown>;
  // Honeypot: a hidden field real people never fill in.
  if (typeof input.website === "string" && input.website.trim() !== "") {
    return { ok: false, errors: ["Rejected."] };
  }
  const name = typeof input.name === "string" ? input.name.trim() : "";
  const email = typeof input.email === "string" ? input.email.trim() : "";
  const message = typeof input.message === "string" ? input.message.trim() : "";
  const errors: string[] = [];
  if (!name) errors.push("Please add your name.");
  if (!EMAIL.test(email)) errors.push("Please add a valid email address.");
  if (!message) errors.push("Please add a message.");
  if (message.length > MAX_MESSAGE) errors.push(`Please keep the message under ${MAX_MESSAGE} characters.`);
  if (errors.length) return { ok: false, errors };
  return { ok: true, errors: [], data: { name, email, message } };
}
