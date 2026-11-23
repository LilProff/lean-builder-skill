// Next.js route: POST /api/paystack/webhook
// Env var (host settings only): PAYSTACK_SECRET_KEY
import { verifyPaystackSignature, verifyTransaction } from "../../../../lib/paystack";

export async function POST(request: Request): Promise<Response> {
  const raw = await request.text();
  const secret = process.env.PAYSTACK_SECRET_KEY ?? "";
  const valid = await verifyPaystackSignature(raw, request.headers.get("x-paystack-signature"), secret);
  if (!valid) return new Response("Invalid signature", { status: 401 });

  const event = JSON.parse(raw) as { event: string; data?: { reference?: string } };
  if (event.event !== "charge.success" || !event.data?.reference) {
    return new Response("Ignored", { status: 200 });
  }

  const payment = await verifyTransaction(event.data.reference, secret, fetch);
  if (payment.status === "success") {
    // ORDER UPDATE GOES HERE. Make it idempotent: look up the order by payment.reference and
    // mark it paid only if it is not paid already. Paystack can send the same event more than once.
  }
  // Always answer 200 quickly, or Paystack will retry.
  return new Response("OK", { status: 200 });
}
