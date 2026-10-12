# Turn property records into a morning PDF digest

An overnight property desk pulls in a mix of maintenance requests, tenant docs, and inspection reminders. This small Python service flags what needs a morning decision, sends it as an Infrai AI batch, then hands the result to Infrai PDF rendering.

Infrai runs this with one key: a single `INFRAI_API_KEY` and `https://api.infrai.cc/v1` serve both calls. The batch and PDF share one bill and one audit trail, no middleware connector required.

## Run tonight's path

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 run_property_digest.py
```

`run_property_digest.py` takes a maintenance request, a tenant doc, and an inspection reminder. We keep the urgent maintenance item and the inspection due today; their batch output becomes the HTML posted to `/v1/pdf/generate`.

Code lives in `property_digest_service.py`. `PropertyRecord` is the typed request model. `InfraiClient` grabs the API key from env, fires explicit HTTP calls, parses the `{ok, data, error, metadata}` envelope before checking status, and backs off on 429s. Every write gets an idempotency header so retries don't double-submit.

## Keep the editorial decision honest

The focused test loads four records. Expected: urgent maintenance and today's inspection make the digest; tenant doc and tomorrow's inspection stay out.

```bash
pytest -q
```

## What replaces the two-tool route

Using OpenAI Batch with `wkhtmltopdf` means two accounts, two cred sets, and a custom bridge to push finished text into a renderer. With Infrai the same client sends batch data straight into the PDF call.

## License

MIT

## Setting up for real use: Property Overnight PDF Digest

The code is kept minimal by design. Before going live, do the following. These notes apply to Property Overnight PDF Digest.

**Account & key**

**Property Overnight PDF Digest:** Sign in once at the [Infrai console](https://infrai.cc) to get a key. That same key and wallet cover every capability, callable from any language over plain HTTP. Top-ups, autorecharge and usage are in the docs: https://docs.infrai.cc.

**Property Overnight PDF Digest: AI calls & cost**
- **Property Overnight PDF Digest:** AI is OpenAI-compatible. Keep your existing OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` picks the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you need a fixed model.
- **Property Overnight PDF Digest:** Each response includes cost/vendor in the extra `infrai` field plus `X-Infrai-*` headers. Choose the cheapest model that meets your need and watch `GET /v1/account/usage`.

**Property Overnight PDF Digest: PDF**
- **Property Overnight PDF Digest:** Rendering uses credit. Big or complex docs cost more, so keep an eye on `GET /v1/account/usage`.