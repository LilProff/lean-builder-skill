// Cloudflare Pages Function: POST /contact sends the form to the owner's inbox through Resend.
// Env vars (set in the Cloudflare dashboard, never in the repo):
//   RESEND_API_KEY, CONTACT_TO_EMAIL, CONTACT_FROM_EMAIL
import { validateContact } from "../src/lib/contact";

type Env = { RESEND_API_KEY: string; CONTACT_TO_EMAIL: string; CONTACT_FROM_EMAIL: string };

export async function onRequestPost(context: { request: Request; env: Env }): Promise<Response> {
  const { request, env } = context;
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ ok: false, errors: ["Send the form as JSON."] }, { status: 400 });
  }
  const result = validateContact(body);
  if (!result.ok || !result.data) {
    return Response.json({ ok: false, errors: result.errors }, { status: 422 });
  }
  if (!env.RESEND_API_KEY) {
    return Response.json({ ok: false, errors: ["The form is not connected yet."] }, { status: 503 });
  }
  const { name, email, message } = result.data;
  const sent = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from: env.CONTACT_FROM_EMAIL,
      to: [env.CONTACT_TO_EMAIL],
      reply_to: email,
      subject: `New enquiry from ${name}`,
      text: `${message}\n\nFrom: ${name} <${email}>`,
    }),
  });
  if (!sent.ok) {
    return Response.json({ ok: false, errors: ["Could not send right now. Please try again."] }, { status: 502 });
  }
  return Response.json({ ok: true });
}
