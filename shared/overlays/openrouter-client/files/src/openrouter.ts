// OpenRouter client: free models first, paid fallback, simple cache. Web platform only.

export type ChatMessage = { role: string; content: string };
export type CompleteOptions = {
  apiKey: string;
  models: string[]; // in order of preference, e.g. free models first, then one paid model
  fetchFn: typeof fetch;
  cache?: Map<string, string>;
};
export type CompleteResult = { model: string; text: string; fromCache: boolean };

const URL = "https://openrouter.ai/api/v1/chat/completions";

export async function complete(messages: ChatMessage[], opts: CompleteOptions): Promise<CompleteResult> {
  const key = JSON.stringify([opts.models, messages]);
  const cached = opts.cache?.get(key);
  if (cached !== undefined) {
    const hit = JSON.parse(cached) as { model: string; text: string };
    return { model: hit.model, text: hit.text, fromCache: true };
  }
  const failures: string[] = [];
  for (const model of opts.models) {
    const res = await opts.fetchFn(URL, {
      method: "POST",
      headers: { Authorization: `Bearer ${opts.apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model, messages }),
    });
    if (res.ok) {
      const json = (await res.json()) as { choices?: Array<{ message?: { content?: string } }> };
      const text = json.choices?.[0]?.message?.content ?? "";
      opts.cache?.set(key, JSON.stringify({ model, text }));
      return { model, text, fromCache: false };
    }
    if (res.status === 429 || res.status >= 500) {
      failures.push(`${model} ${res.status}`); // rate limited or provider down: try the next model
      continue;
    }
    // 400/401/402/403: a bad request or key will not work on another model either.
    throw new Error(`OpenRouter request failed: ${model} ${res.status}`);
  }
  throw new Error(`all models failed: ${failures.join(", ")}`);
}
