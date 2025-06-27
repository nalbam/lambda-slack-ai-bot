# Google Gemini API - Video API Documentation (Markdown Format)

> Source: [https://ai.google.dev/gemini-api/docs/video](https://ai.google.dev/gemini-api/docs/video)

---

# Gemini API - Video Input Support

Google's Gemini API supports multimodal input, including video. You can send video content to the API as a sequence of image frames. This document explains how to handle video input using Gemini models.

## Overview

Gemini models do not support direct video file input (e.g., `.mp4`, `.mov`). Instead, videos must be converted into a sequence of individual frames (images). These image frames are then sent to the API as part of the `multimodalContent` field.

This enables tasks such as:

* Action recognition
* Scene understanding
* Instruction following based on visual context

## Requirements

* Input video should be split into a series of still image frames.
* Each image must be one of the supported formats:

  * `image/png`
  * `image/jpeg`
  * `image/webp`
* Each frame should be less than **20MB**.
* The full sequence of images (along with other inputs) must fit within the model's context window (see model-specific limits).

## Example (Python)

```python
import base64
import os
from google import genai
from google.generativeai.types import content_types

client = genai.GenerativeModel("gemini-pro-vision")

video_frames = ["frame1.jpg", "frame2.jpg", "frame3.jpg"]
image_parts = []

for path in video_frames:
    with open(path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
        image_parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": image_data
            }
        })

response = client.generate_content(
    contents=[
        {
            "role": "user",
            "parts": [
                *image_parts,
                {"text": "What is happening in this video?"}
            ]
        }
    ]
)

print(response.text())
```

## Tips for Best Results

* **Frame Sampling:** Avoid sending too many consecutive frames. Instead, sample key frames at regular intervals (e.g., 1 frame per second).
* **Compression:** Compress images to stay under the size limit without losing too much quality.
* **Descriptive Prompts:** Provide a clear and concise text prompt with your image frames.
* **Context Management:** If needed, split video analysis across multiple API calls to stay within context limits.

## Limitations

* **No audio support.**
* **No raw video formats.** You must extract and convert frames manually.
* **Latency and size constraints**: large sequences may increase latency or result in context overflow.

## Related Topics

* [Multimodal Content Input](https://ai.google.dev/gemini-api/docs/prompting#multimodal)
* [Model Capabilities](https://ai.google.dev/gemini-api/docs/models)
* [Supported Media Types](https://ai.google.dev/gemini-api/docs/prompting#media-types)

---

# Generate Video using Veo

The Gemini API provides access to **Veo 2**, Google's most capable video generation model. Veo supports a wide range of cinematic and visual styles, capturing nuanced prompts to generate consistent details across frames.

> 💡 **Note:** Veo is a paid feature. It is not available on the Free tier. Refer to the [Pricing](https://ai.google.dev/pricing) page for details.

## Prerequisites

Ensure your SDK is installed and an API key is configured. Supported SDK versions:

* Python: `v1.10.0+`
* JavaScript/TypeScript: `v0.8.0+`
* Go: `v1.0.0+`

## Generate from Text (Python Example)

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

operation = client.models.generate_videos(
    model="veo-2.0-generate-001",
    prompt="Panning wide shot of a calico kitten sleeping in the sunshine",
    config=types.GenerateVideosConfig(
        person_generation="dont_allow",
        aspect_ratio="16:9",
    ),
)

while not operation.done:
    time.sleep(20)
    operation = client.operations.get(operation)

for n, generated_video in enumerate(operation.response.generated_videos):
    client.files.download(file=generated_video.video)
    generated_video.video.save(f"video{n}.mp4")
```

## Generate from Image (Python Example)

```python
prompt = "Panning wide shot of a calico kitten sleeping in the sunshine"

imagen = client.models.generate_images(
    model="imagen-3.0-generate-002",
    prompt=prompt,
    config=types.GenerateImagesConfig(
        aspect_ratio="16:9",
        number_of_images=1
    )
)

operation = client.models.generate_videos(
    model="veo-2.0-generate-001",
    prompt=prompt,
    image=imagen.generated_images[0].image,
    config=types.GenerateVideosConfig(
        person_generation="dont_allow",
        aspect_ratio="16:9",
        number_of_videos=2
    ),
)

while not operation.done:
    time.sleep(20)
    operation = client.operations.get(operation)

for n, video in enumerate(operation.response.generated_videos):
    fname = f'with_image_input{n}.mp4'
    client.files.download(file=video.video)
    video.video.save(fname)
```

## Veo Parameters

| Parameter          | Description                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| `prompt`           | Required. The video prompt text.                                                                  |
| `image`            | Optional. Use as starting frame.                                                                  |
| `negativePrompt`   | Describe what to avoid.                                                                           |
| `aspectRatio`      | "16:9" (default) or "9:16".                                                                       |
| `personGeneration` | Control people in videos: `dont_allow`, `allow_adult`, `allow_all`. Restrictions apply by region. |
| `numberOfVideos`   | `1` or `2`.                                                                                       |
| `durationSeconds`  | Length in seconds: 5-8.                                                                           |
| `enhance_prompt`   | Enable/disable rewriter. Default is enabled.                                                      |

## Specifications

* **Modalities**: Text-to-video, Image-to-video
* **Latency**: 11s–6min
* **Duration**: 5–8 seconds
* **Resolution**: 720p
* **Frame rate**: 24fps
* **Aspect ratio**: 16:9 or 9:16
* **Languages**: English (text input)

## Limitations

* Regional restrictions apply to `personGeneration` settings.
* Videos are watermarked with SynthID.
* Safety filters are applied to detect and block unsafe or policy-violating content.

## Prompt Writing Tips

To create effective prompts:

* **Subject**: What should appear in the video.
* **Context**: Where it happens.
* **Action**: What is the subject doing?
* **Style**: e.g., horror film, noir, cartoon.
* **Camera Motion**: e.g., aerial, eye-level, dolly shot.
* **Composition**: e.g., wide shot, close-up.
* **Ambiance**: Lighting and tone, e.g., warm tones.

### More Tips

* Use rich, descriptive language.
* Provide context or background.
* Reference artistic styles.
* Use tools for prompt engineering.

## Related

* [Veo Prompt Guide](https://ai.google.dev/gemini-api/docs/veo/prompt-guide)
* [Models](https://ai.google.dev/gemini-api/docs/models)
* [Pricing](https://ai.google.dev/pricing)
* [Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)
