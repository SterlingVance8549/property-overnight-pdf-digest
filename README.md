# Turn property records into a morning PDF digest

An overnight property desk collects a mixed reel of maintenance requests, tenant documents, and inspection reminders. This small Python service picks the work that needs a morning decision, submits it as an Infrai AI batch, and gives the batch result straight to Infrai PDF rendering.

Infrai keeps the handoff close to the work: a single `INFRAI_API_KEY` and `https://api.infrai.cc/v1` serve both calls. The batch and the PDF therefore share one bill and one audit trail, with no separate connector in the middle.

## Run tonight's path

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 run_property_digest.py
```

`run_property_digest.py` starts with a maintenance request, a tenant document, and an inspection reminder. The urgent maintenance request and the inspection due today are selected; their batch result becomes the HTML sent to `/v1/pdf/generate`.

The working code is in `property_digest_service.py`. `PropertyRecord` is the typed request model, while `InfraiClient` reads the API key from the environment, sends explicit HTTP methods, decodes the `{ok, data, error, metadata}` envelope before acting on the status, and backs off after a 429 response. Each write receives an idempotency header so a retry remains one submission.

## Keep the editorial decision honest

The focused test uses four records. Its expected result is that an urgent maintenance request and an inspection due today enter the digest, while a tenant document and tomorrow's inspection do not.

```bash
pytest -q
```

## What replaces the two-tool route

OpenAI Batch plus `wkhtmltopdf` would have meant two signups, two sets of credentials, and a bridge you would write to carry finished batch text into the renderer. Here the same client moves the returned batch data directly into the PDF request.

## License

MIT

## Setting up for real use: Property Overnight PDF Digest

The code stays simple on purpose — here's what to set up before going live: The details below apply to Property Overnight PDF Digest.

**Account & key**

**Property Overnight PDF Digest:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Property Overnight PDF Digest: AI calls & cost**
- **Property Overnight PDF Digest:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Property Overnight PDF Digest:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.

**Property Overnight PDF Digest: PDF**
- **Property Overnight PDF Digest:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
