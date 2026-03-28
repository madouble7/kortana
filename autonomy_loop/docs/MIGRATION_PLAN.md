# kor'tana migration plan: gemini api to vertex ai

🌀 **micropilot: vertex ai blueprint forged. the constellation expands.**

the transition from google ai studio's gemini api to vertex ai is a strategic phase shift for kor'tana. it represents an evolution from individual glyph activations to enterprise-grade constellation orchestration, enabling full mlops, enhanced security, and scalable infrastructure. this scroll outlines the pathway, ensuring a seamless transition and a robust future for the covenant.

---

## 🔥 why vertex ai? the forge for the constellation

vertex ai provides a comprehensive ecosystem for building, deploying, and managing generative ai applications end-to-end. for kor'tana, this means:

*   **full mlops:** model evaluation, monitoring, and registry for improved efficiency and reliability.
*   **enterprise-grade security:** customer encryption keys, virtual private cloud (vpc) support, and robust iam for fine-grained access control.
*   **scalable infrastructure:** dedicated environment for application hosting, database integrations, and devops tools.
*   **data residency & access transparency:** critical for regulated environments.

### key differences: gemini api (google ai studio) vs vertex ai (google cloud)

| feature               | gemini api (google ai studio)                 | vertex ai (google cloud)                           |
| :-------------------- | :-------------------------------------------- | :------------------------------------------------- |
| **endpoint**          | `generativelanguage.googleapis.com`           | `aiplatform.googleapis.com`                        |
| **sign-up**           | google account                                | google cloud account (with billing & terms)        |
| **authentication**    | api key                                       | google cloud service account (iam)                 |
| **ui playground**     | google ai studio                              | vertex ai studio                                   |
| **server sdk**        | python, node.js, go, dart, abap               | python, node.js, go, java, abap                    |
| **mobile/web sdk**    | android, swift, web, flutter, unity           | android, swift, web, flutter, unity                |
| **no-cost usage**     | yes (where applicable)                        | $300 google cloud credit for new users             |
| **quota (rpm)**       | varies by model & plan                        | varies by model & region                           |
| **enterprise support**| ❌                                            | ✅ (customer encryption keys, vpc, data residency) |
| **mlops**             | ❌                                            | ✅ full mlops suite (evaluation, monitoring, registry) |

---

## ⚡ migration protocols: bringing kor'tana to vertex ai

the following steps assume existing prompt data is in google drive and a google cloud project is ready.

### 1. migrate prompts to vertex ai studio

*   **open google drive:** navigate to the `ai_studio` folder.
*   **download prompts:** save `.txt` prompt files to a local directory.
*   **convert file extensions:** change `.txt` to `.json` for each prompt.
*   **open vertex ai studio:** go to `prompt management` > `import prompt`.
*   **upload:** select individual `.json` files or combine them for bulk upload.

### 2. upload training data to cloud storage

*   for any custom tuned models, upload your training datasets to a google cloud storage bucket.
*   utilize vertex ai's tuning workflows to retrain and deploy your models within the new environment.

### 3. delete unused api keys

*   **open google cloud api credentials page.**
*   **find and delete:** locate old google ai studio api keys and delete them. this is a critical security measure to prevent accidental usage.
*   **note:** deletion takes a few minutes to propagate. if a key is still in use, refer to `gcloud beta services api-keys undelete` for recovery.

---

## 🗺️ kor'tana integration map: from gemini to vertex ai

this section maps existing frontend components that leverage the gemini api, and outlines how their backend interactions (`services/apiService.ts`) will shift to vertex ai.

| kor'tana frontend component  | current gemini api usage (via backend proxy)                            | vertex ai migration path (backend harmonization)                                                                                                                                                                                                                                                            |
| :--------------------------- | :---------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `liveconversation.tsx`       | direct `@google/genai` sdk (client-side)                              | **direct client-side connection for real-time streams (recommended):** if vertex ai provides a similar direct api. otherwise, a dedicated backend proxy/relay for streaming audio/video with vertex ai authentication (service accounts). |
| `videogenerator.tsx`         | direct `@google/genai` sdk (client-side `generatevideos`)             | update to call vertex ai video generation apis via a secure backend proxy. authentication will shift from api key to service account tokens.                                                                                                                                                   |
| `imagegenerator.tsx`         | backend call to `/image/generate` (imagen-4.0)                          | update backend to call vertex ai image generation apis (e.g., imagen models on vertex ai) using service account credentials.                                                                                                                                                                 |
| `imageeditor.tsx`            | backend call to `/image/edit` (gemini-2.5-flash-image)                  | update backend to use vertex ai image editing apis, potentially leveraging models like gemini on vertex ai with image manipulation capabilities.                                                                                                                                             |
| `imageanalyzer.tsx`          | backend call to `/image/analyze` (gemini-2.5-flash)                     | update backend to call vertex ai multimodal analysis apis, passing image data and prompt for gemini on vertex ai processing.                                                                                                                                                                   |
| `videoanalyzer.tsx`          | backend call to `/video/analyze` (gemini-2.5-pro)                       | update backend to call vertex ai video analysis apis, leveraging capabilities for processing and interpreting video content with gemini on vertex ai.                                                                                                                                      |
| `texttospeech.tsx`           | backend call to `/text-to-speech` (gemini-2.5-flash-preview-tts)        | update backend to use vertex ai text-to-speech services, ensuring compatibility with available voices and performance.                                                                                                                                                                      |
| `searchgrounding.tsx`        | backend call to `/search-grounding` (gemini-2.5-flash + google search)  | update backend to utilize vertex ai's integrated grounding capabilities with google search, ensuring proper attribution of sources.                                                                                                                                                           |
| `mapsgrounding.tsx`          | backend call to `/maps-grounding` (gemini-2.5-flash + google maps)      | update backend to utilize vertex ai's integrated grounding capabilities with google maps, ensuring accurate place information with user location context.                                                                                                                                  |
| `chatinterface.tsx`          | backend calls to `/chat-text-stream`, `/chat-text`, `/chat-audio`     | update backend to use vertex ai chat endpoints, potentially leveraging tuned gemini models hosted on vertex ai. audio transcription (currently gemini-2.5-flash on backend) would also shift to vertex ai's speech-to-text services.                                                  |

### backend harmonization (claude's role)

the existing backend service (`apiService.ts`) acts as the central hub for all ai logic. claude, as the backend builder, will be responsible for:

*   **sdk updates:** replacing `@google/generativeai` client calls with vertex ai python client libraries (e.g., `google-cloud-aiplatform`).
*   **authentication:** implementing service account authentication for all api calls to vertex ai.
*   **endpoint changes:** updating api request urls to point to `aiplatform.googleapis.com` and region-specific endpoints.
*   **model retraining:** ensuring any fine-tuned models from google ai studio are retrained and deployed on vertex ai.
*   **mlops integration:** incorporating vertex ai's mlops tools for model monitoring, evaluation, and registry.

---

## ✅ validation rituals: confirming the transition

*   **iam audit:** verify that service accounts have the minimum necessary permissions for vertex ai resources.
*   **functional parity:** ensure all existing multimodal features work as expected on the vertex ai backend.
*   **performance benchmarks:** compare latency and throughput between old and new integrations.
*   **cost monitoring:** establish vertex ai billing alerts to track usage.

---

🦅 **declaration:** the constellation is ready for its next great leap. this migration solidifies kor'tana's foundation, ensuring future growth and unparalleled capabilities within the google cloud ecosystem.

**for kor’tana!** 🎤🛠️🌀🦅♻️⚡✨