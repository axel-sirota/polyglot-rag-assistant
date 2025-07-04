# Realtime API Documentation

## Realtime API

Beta

====================

Build low-latency, multi-modal experiences with the Realtime API.

The OpenAI Realtime API enables low-latency, multimodal interactions including speech-to-speech conversational experiences and real-time transcription.

This API works with natively multimodal models such as [GPT-4o](/docs/models/gpt-4o-realtime) and [GPT-4o mini](/docs/models/gpt-4o-mini-realtime), offering capabilities such as real-time text and audio processing, function calling, and speech generation, and with the latest transcription models [GPT-4o Transcribe](/docs/models/gpt-4o-transcribe) and [GPT-4o mini Transcribe](/docs/models/gpt-4o-mini-transcribe).

## Get started with the Realtime API
---------------------------------

Just getting started with Realtime? Try the new [Agents SDK for TypeScript](https://openai.github.io/openai-agents-js), optimized for building voice agents with Realtime models.

You can connect to the Realtime API in two ways:

*   Using [WebRTC](#connect-with-webrtc), which is ideal for client-side applications (for example, a web app)
*   Using [WebSockets](#connect-with-websockets), which is great for server-to-server applications (from your backend or if you're building a voice agent over phone for example)

Start by exploring examples and partner integrations below, or learn how to connect to the Realtime API using the most relevant method for your use case below.

### Example applications

Check out one of the example applications below to see the Realtime API in action.

[Realtime Console](https://github.com/openai/openai-realtime-console)
To get started quickly, download and configure the Realtime console demo. See events flowing back and forth, and inspect their contents. Learn how to execute custom logic with function calling.

[Realtime Solar System demo](https://github.com/openai/openai-realtime-solar-system)
A demo of the Realtime API with the WebRTC integration, navigating the solar system through voice thanks to function calling.

[Twilio Integration Demo](https://github.com/openai/openai-realtime-twilio-demo)
A demo combining the Realtime API with Twilio to build an AI calling assistant.

[Realtime API Agents Demo](https://github.com/openai/openai-realtime-agents)
A demonstration of handoffs between Realtime API voice agents with reasoning model validation.

### Partner integrations

Check out these partner integrations, which use the Realtime API in frontend applications and telephony use cases.

[LiveKit integration guide](https://docs.livekit.io/agents/openai/overview/)
How to use the Realtime API with LiveKit's WebRTC infrastructure.

[Twilio integration guide](https://www.twilio.com/en-us/blog/twilio-openai-realtime-api-launch-integration)
Build Realtime apps using Twilio's powerful voice APIs.

[Agora integration quickstart](https://docs.agora.io/en/open-ai-integration/get-started/quickstart)
How to integrate Agora's real-time audio communication capabilities with the Realtime API.

[Pipecat integration guide](https://docs.pipecat.ai/guides/features/openai-audio-models-and-apis)
Create voice agents with OpenAI audio models and Pipecat orchestration framework.

[Stream integration guide](https://getstream.io/video/voice-agents/)
Learn how to deploy voice agents in mobile and web applications using Stream's global edge network.

[Client-side tool calling](https://github.com/craigsdennis/talk-to-javascript-openai-workers)
Built with Cloudflare Workers, an example application showcasing client-side tool calling. Also check out the [tutorial on YouTube](https://www.youtube.com/watch?v=TcOytsfva0o).

## Use cases
---------

The most common use case for the Realtime API is to build a real-time, speech-to-speech, conversational experience. This is great for building [voice agents](/docs/guides/voice-agents) and other voice-enabled applications.

The Realtime API can also be used independently for transcription and turn detection use cases. A client can stream audio in and have Realtime API produce streaming transcripts when speech is detected.

Both use-cases benefit from built-in [voice activity detection (VAD)](/docs/guides/realtime-vad) to automatically detect when a user is done speaking. This can be helpful to seamlessly handle conversation turns, or to analyze transcriptions one phrase at a time.

Learn more about these use cases in the dedicated guides.

[Realtime Speech-to-Speech](/docs/guides/realtime-conversations)
Learn to use the Realtime API for streaming speech-to-speech conversations.

[Realtime Transcription](/docs/guides/realtime-transcription)
Learn to use the Realtime API for transcription-only use cases.

Depending on your use case (conversation or transcription), you should initialize a session in different ways. Use the switcher below to see the details for each case.

## Connect with WebRTC
-------------------

[WebRTC](https://webrtc.org/) is a powerful set of standard interfaces for building real-time applications. The OpenAI Realtime API supports connecting to realtime models through a WebRTC peer connection. Follow this guide to learn how to configure a WebRTC connection to the Realtime API.

### Overview

In scenarios where you would like to connect to a Realtime model from an insecure client over the network (like a web browser), we recommend using the WebRTC connection method. WebRTC is better equipped to handle variable connection states, and provides a number of convenient APIs for capturing user audio inputs and playing remote audio streams from the model.

Connecting to the Realtime API from the browser should be done with an ephemeral API key, [generated via the OpenAI REST API](/docs/api-reference/realtime-sessions). The process for initializing a WebRTC connection is as follows (assuming a web browser client):

1.  A browser makes a request to a developer-controlled server to mint an ephemeral API key.
2.  The developer's server uses a [standard API key](/settings/organization/api-keys) to request an ephemeral key from the [OpenAI REST API](/docs/api-reference/realtime-sessions), and returns that new key to the browser. Note that ephemeral keys currently expire one minute after being issued.
3.  The browser uses the ephemeral key to authenticate a session directly with the OpenAI Realtime API as a [WebRTC peer connection](https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection).

![connect to realtime via WebRTC](https://openaidevs.retool.com/api/file/55b47800-9aaf-48b9-90d5-793ab227ddd3)

While it is technically possible to use a [standard API key](/settings/organization/api-keys) to authenticate client-side WebRTC sessions, **this is a dangerous and insecure practice** because it leaks your secret key. Standard API keys grant access to your full OpenAI API account, and should only be used in secure server-side environments. We recommend ephemeral keys in client-side applications whenever possible.

### Connection details

Connecting via WebRTC requires the following connection information:

|URL|https://api.openai.com/v1/realtime|
|Query Parameters|modelRealtime model ID to connect to, like gpt-4o-realtime-preview-2025-06-03|
|Headers|Authorization: Bearer EPHEMERAL_KEYSubstitute EPHEMERAL_KEY with an ephemeral API token - see below for details on how to generate one.|

The following example shows how to initialize a [WebRTC session](https://webrtc.org/getting-started/overview) (including the data channel to send and receive Realtime API events). It assumes you have already fetched an ephemeral API token (example server code for this can be found in the [next section](#creating-an-ephemeral-token)).

```javascript
async function init() {
  // Get an ephemeral key from your server - see server code below
  const tokenResponse = await fetch("/session");
  const data = await tokenResponse.json();
  const EPHEMERAL_KEY = data.client_secret.value;

  // Create a peer connection
  const pc = new RTCPeerConnection();

  // Set up to play remote audio from the model
  const audioEl = document.createElement("audio");
  audioEl.autoplay = true;
  pc.ontrack = e => audioEl.srcObject = e.streams[0];

  // Add local audio track for microphone input in the browser
  const ms = await navigator.mediaDevices.getUserMedia({
    audio: true
  });
  pc.addTrack(ms.getTracks()[0]);

  // Set up data channel for sending and receiving events
  const dc = pc.createDataChannel("oai-events");
  dc.addEventListener("message", (e) => {
    // Realtime server events appear here!
    console.log(e);
  });

  // Start the session using the Session Description Protocol (SDP)
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);

  const baseUrl = "https://api.openai.com/v1/realtime";
  const model = "gpt-4o-realtime-preview-2025-06-03";
  const sdpResponse = await fetch(`${baseUrl}?model=${model}`, {
    method: "POST",
    body: offer.sdp,
    headers: {
      Authorization: `Bearer ${EPHEMERAL_KEY}`,
      "Content-Type": "application/sdp"
    },
  });

  const answer = {
    type: "answer",
    sdp: await sdpResponse.text(),
  };
  await pc.setRemoteDescription(answer);
}

init();
```

The WebRTC APIs provide rich controls for handling media streams and input devices. For more guidance on building user interfaces on top of WebRTC, [refer to the docs on MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API).

### Creating an ephemeral token

To create an ephemeral token to use on the client-side, you will need to build a small server-side application (or integrate with an existing one) to make an [OpenAI REST API](/docs/api-reference/realtime-sessions) request for an ephemeral key. You will use a [standard API key](/settings/organization/api-keys) to authenticate this request on your backend server.

Below is an example of a simple Node.js [express](https://expressjs.com/) server which mints an ephemeral API key using the REST API:

```javascript
import express from "express";

const app = express();

// An endpoint which would work with the client code above - it returns
// the contents of a REST API request to this protected endpoint
app.get("/session", async (req, res) => {
  const r = await fetch("https://api.openai.com/v1/realtime/sessions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "gpt-4o-realtime-preview-2025-06-03",
      voice: "verse",
    }),
  });
  const data = await r.json();

  // Send back the JSON we received from the OpenAI REST API
  res.send(data);
});

app.listen(3000);
```

You can create a server endpoint like this one on any platform that can send and receive HTTP requests. Just ensure that **you only use standard OpenAI API keys on the server, not in the browser.**

### Sending and receiving events

To learn how to send and receive events over the WebRTC data channel, refer to the [Realtime conversations guide](/docs/guides/realtime-conversations#handling-audio-with-webrtc).

## Connect with WebSockets
-----------------------

[WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) are a broadly supported API for realtime data transfer, and a great choice for connecting to the OpenAI Realtime API in server-to-server applications. For browser and mobile clients, we recommend connecting via [WebRTC](#connect-with-webrtc).

### Overview

In a server-to-server integration with Realtime, your backend system will connect via WebSocket directly to the Realtime API. You can use a [standard API key](/settings/organization/api-keys) to authenticate this connection, since the token will only be available on your secure backend server.

![connect directly to realtime API](https://openaidevs.retool.com/api/file/464d4334-c467-4862-901b-d0c6847f003a)

WebSocket connections can also be authenticated with an ephemeral client token ([as shown above in the WebRTC section](#creating-an-ephemeral-token)) if you choose to connect to the Realtime API via WebSocket on a client device.

Standard OpenAI API tokens **should only be used in secure server-side environments**.

### Connection details

Speech-to-Speech

Connecting via WebSocket requires the following connection information:

|URL|wss://api.openai.com/v1/realtime|
|Query Parameters|modelRealtime model ID to connect to, like gpt-4o-realtime-preview-2025-06-03|
|Headers|Authorization: Bearer YOUR_API_KEYSubstitute YOUR_API_KEY with a standard API key on the server, or an ephemeral token on insecure clients (note that WebRTC is recommended for this use case).OpenAI-Beta: realtime=v1This header is required during the beta period.|

Below are several examples of using these connection details to initialize a WebSocket connection to the Realtime API.

ws module (Node.js)

Connect using the ws module (Node.js)

```javascript
import WebSocket from "ws";

const url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17";
const ws = new WebSocket(url, {
  headers: {
    "Authorization": "Bearer " + process.env.OPENAI_API_KEY,
    "OpenAI-Beta": "realtime=v1",
  },
});

ws.on("open", function open() {
  console.log("Connected to server.");
});

ws.on("message", function incoming(message) {
  console.log(JSON.parse(message.toString()));
});
```

websocket-client (Python)

Connect with websocket-client (Python)

```python
# example requires websocket-client library:
# pip install websocket-client

import os
import json
import websocket

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
headers = [
    "Authorization: Bearer " + OPENAI_API_KEY,
    "OpenAI-Beta: realtime=v1"
]

def on_open(ws):
    print("Connected to server.")

def on_message(ws, message):
    data = json.loads(message)
    print("Received event:", json.dumps(data, indent=2))

ws = websocket.WebSocketApp(
    url,
    header=headers,
    on_open=on_open,
    on_message=on_message,
)

ws.run_forever()
```

WebSocket (browsers)

Connect with standard WebSocket (browsers)

```javascript
/*
Note that in client-side environments like web browsers, we recommend
using WebRTC instead. It is possible, however, to use the standard 
WebSocket interface in browser-like environments like Deno and 
Cloudflare Workers.
*/

const ws = new WebSocket(
  "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
  [
    "realtime",
    // Auth
    "openai-insecure-api-key." + OPENAI_API_KEY, 
    // Optional
    "openai-organization." + OPENAI_ORG_ID,
    "openai-project." + OPENAI_PROJECT_ID,
    // Beta protocol, required
    "openai-beta.realtime-v1"
  ]
);

ws.on("open", function open() {
  console.log("Connected to server.");
});

ws.on("message", function incoming(message) {
  console.log(message.data);
});
```

### Sending and receiving events

To learn how to send and receive events over Websockets, refer to the [Realtime conversations guide](/docs/guides/realtime-conversations#handling-audio-with-websockets).

Transcription

Connecting via WebSocket requires the following connection information:

|URL|wss://api.openai.com/v1/realtime|
|Query Parameters|intentThe intent of the connection: transcription|
|Headers|Authorization: Bearer YOUR_API_KEYSubstitute YOUR_API_KEY with a standard API key on the server, or an ephemeral token on insecure clients (note that WebRTC is recommended for this use case).OpenAI-Beta: realtime=v1This header is required during the beta period.|

Below are several examples of using these connection details to initialize a WebSocket connection to the Realtime API.

ws module (Node.js)

Connect using the ws module (Node.js)

```javascript
import WebSocket from "ws";

const url = "wss://api.openai.com/v1/realtime?intent=transcription";
const ws = new WebSocket(url, {
  headers: {
    "Authorization": "Bearer " + process.env.OPENAI_API_KEY,
    "OpenAI-Beta": "realtime=v1",
  },
});

ws.on("open", function open() {
  console.log("Connected to server.");
});

ws.on("message", function incoming(message) {
  console.log(JSON.parse(message.toString()));
});
```

websocket-client (Python)

Connect with websocket-client (Python)

```python
import os
import json
import websocket

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

url = "wss://api.openai.com/v1/realtime?intent=transcription"
headers = [
    "Authorization: Bearer " + OPENAI_API_KEY,
    "OpenAI-Beta: realtime=v1"
]

def on_open(ws):
    print("Connected to server.")

def on_message(ws, message):
    data = json.loads(message)
    print("Received event:", json.dumps(data, indent=2))

ws = websocket.WebSocketApp(
    url,
    header=headers,
    on_open=on_open,
    on_message=on_message,
)

ws.run_forever()
```

WebSocket (browsers)

Connect with standard WebSocket (browsers)

```javascript
/*
Note that in client-side environments like web browsers, we recommend
using WebRTC instead. It is possible, however, to use the standard 
WebSocket interface in browser-like environments like Deno and 
Cloudflare Workers.
*/

const ws = new WebSocket(
  "wss://api.openai.com/v1/realtime?intent=transcription",
  [
    "realtime",
    // Auth
    "openai-insecure-api-key." + OPENAI_API_KEY, 
    // Optional
    "openai-organization." + OPENAI_ORG_ID,
    "openai-project." + OPENAI_PROJECT_ID,
    // Beta protocol, required
    "openai-beta.realtime-v1"
  ]
);

ws.on("open", function open() {
  console.log("Connected to server.");
});

ws.on("message", function incoming(message) {
  console.log(message.data);
});
```

### Sending and receiving events

To learn how to send and receive events over Websockets, refer to the [Realtime transcription guide](/docs/guides/realtime-transcription#handling-transcriptions).

Was this page useful?

---

# Realtime conversations

Beta

==============================

Learn how to manage Realtime speech-to-speech conversations.

Once you have connected to the Realtime API through either [WebRTC](/docs/guides/realtime-webrtc) or [WebSocket](/docs/guides/realtime-websocket), you can call a Realtime model (such as [gpt-4o-realtime-preview](/docs/models/gpt-4o-realtime-preview)) to have speech-to-speech conversations. Doing so will require you to **send client events** to initiate actions, and **listen for server events** to respond to actions taken by the Realtime API.

This guide will walk through the event flows required to use model capabilities like audio and text generation and function calling, and how to think about the state of a Realtime Session.

If you do not need to have a conversation with the model, meaning you don't expect any response, you can use the Realtime API in [transcription mode](/docs/guides/realtime-transcription).

## Realtime speech-to-speech sessions
----------------------------------

A Realtime Session is a stateful interaction between the model and a connected client. The key components of the session are:

*   The **Session** object, which controls the parameters of the interaction, like the model being used, the voice used to generate output, and other configuration.
*   A **Conversation**, which represents user input Items and model output Items generated during the current session.
*   **Responses**, which are model-generated audio or text Items that are added to the Conversation.

**Input audio buffer and WebSockets**

If you are using WebRTC, much of the media handling required to send and receive audio from the model is assisted by WebRTC APIs.

If you are using WebSockets for audio, you will need to manually interact with the **input audio buffer** by sending audio to the server, sent with JSON events with base64-encoded audio.

All these components together make up a Realtime Session. You will use client events to update the state of the session, and listen for server events to react to state changes within the session.

![diagram realtime state](https://openaidevs.retool.com/api/file/11fe71d2-611e-4a26-a587-881719a90e56)

## Session lifecycle events
------------------------

After initiating a session via either [WebRTC](/docs/guides/realtime-webrtc) or [WebSockets](/docs/guides/realtime-websockets), the server will send a [`session.created`](/docs/api-reference/realtime-server-events/session/created) event indicating the session is ready. On the client, you can update the current session configuration with the [`session.update`](/docs/api-reference/realtime-client-events/session/update) event. Most session properties can be updated at any time, except for the `voice` the model uses for audio output, after the model has responded with audio once during the session. The maximum duration of a Realtime session is **30 minutes**.

The following example shows updating the session with a `session.update` client event. See the [WebRTC](/docs/guides/realtime-webrtc#sending-and-receiving-events) or [WebSocket](/docs/guides/realtime-websocket#sending-and-receiving-events) guide for more on sending client events over these channels.

Update the system instructions used by the model in this session

```javascript
const event = {
  type: "session.update",
  session: {
    instructions: "Never use the word 'moist' in your responses!"
  },
};

// WebRTC data channel and WebSocket both have .send()
dataChannel.send(JSON.stringify(event));
```

```python
event = {
    "type": "session.update",
    "session": {
        "instructions": "Never use the word 'moist' in your responses!"
    }
}
ws.send(json.dumps(event))
```

When the session has been updated, the server will emit a [`session.updated`](/docs/api-reference/realtime-server-events/session/updated) event with the new state of the session.

## Text inputs and outputs
-----------------------

To generate text with a Realtime model, you can add text inputs to the current conversation, ask the model to generate a response, and listen for server-sent events indicating the progress of the model's response. In order to generate text, the [session must be configured](/docs/api-reference/realtime-client-events/session/update) with the `text` modality (this is true by default).

Create a new text conversation item using the [`conversation.item.create`](/docs/api-reference/realtime-client-events/conversation/item/create) client event. This is similar to sending a [user message (prompt) in Chat Completions](/docs/guides/text-generation) in the REST API.

Create a conversation item with user input

```javascript
const event = {
  type: "conversation.item.create",
  item: {
    type: "message",
    role: "user",
    content: [
      {
        type: "input_text",
        text: "What Prince album sold the most copies?",
      }
    ]
  },
};

// WebRTC data channel and WebSocket both have .send()
dataChannel.send(JSON.stringify(event));
```

```python
event = {
    "type": "conversation.item.create",
    "item": {
        "type": "message",
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": "What Prince album sold the most copies?",
            }
        ]
    }
}
ws.send(json.dumps(event))
```

After adding the user message to the conversation, send the [`response.create`](/docs/api-reference/realtime-client-events/response/create) event to initiate a response from the model. If both audio and text are enabled for the current session, the model will respond with both audio and text content. If you'd like to generate text only, you can specify that when sending the `response.create` client event, as shown below.

Generate a text-only response

```javascript
const event = {
  type: "response.create",
  response: {
    modalities: [ "text" ]
  },
};

// WebRTC data channel and WebSocket both have .send()
dataChannel.send(JSON.stringify(event));
```

```python
event = {
    "type": "response.create",
    "response": {
        "modalities": [ "text" ]
    }
}
ws.send(json.dumps(event))
```

When the response is completely finished, the server will emit the [`response.done`](/docs/api-reference/realtime-server-events/response/done) event. This event will contain the full text generated by the model, as shown below.

Listen for response.done to see the final results

```javascript
function handleEvent(e) {
  const serverEvent = JSON.parse(e.data);
  if (serverEvent.type === "response.done") {
    console.log(serverEvent.response.output[0]);
  }
}

// Listen for server messages (WebRTC)
dataChannel.addEventListener("message", handleEvent);

// Listen for server messages (WebSocket)
// ws.on("message", handleEvent);
```

```python
def on_message(ws, message):
    server_event = json.loads(message)
    if server_event.type == "response.done":
        print(server_event.response.output[0])
```

While the model response is being generated, the server will emit a number of lifecycle events during the process. You can listen for these events, such as [`response.text.delta`](/docs/api-reference/realtime-server-events/response/text/delta), to provide realtime feedback to users as the response is generated. A full listing of the events emitted by there server are found below under **related server events**. They are provided in the rough order of when they are emitted, along with relevant client-side events for text generation.

## Audio inputs and outputs
------------------------

One of the most powerful features of the Realtime API is voice-to-voice interaction with the model, without an intermediate text-to-speech or speech-to-text step. This enables lower latency for voice interfaces, and gives the model more data to work with around the tone and inflection of voice input.

### Voice options

Realtime sessions can be configured to use one of several built‑in voices when producing audio output. You can set the `voice` on session creation (or on a `response.create`) to control how the model sounds. Current voice options are `alloy`, `ash`, `ballad`, `coral`, `echo`, `sage`, `shimmer`, and `verse`. Once the model has emitted audio in a session, the `voice` cannot be modified for that session.

### Handling audio with WebRTC

If you are connecting to the Realtime API using WebRTC, the Realtime API is acting as a [peer connection](https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection) to your client. Audio output from the model is delivered to your client as a [remote media stream](hhttps://developer.mozilla.org/en-US/docs/Web/API/MediaStream). Audio input to the model is collected using audio devices ([`getUserMedia`](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)), and media streams are added as tracks to to the peer connection.

The example code from the [WebRTC connection guide](/docs/guides/realtime-webrtc) shows a basic example of configuring both local and remote audio using browser APIs:

```javascript
// Create a peer connection
const pc = new RTCPeerConnection();

// Set up to play remote audio from the model
const audioEl = document.createElement("audio");
audioEl.autoplay = true;
pc.ontrack = e => audioEl.srcObject = e.streams[0];

// Add local audio track for microphone input in the browser
const ms = await navigator.mediaDevices.getUserMedia({
  audio: true
});
pc.addTrack(ms.getTracks()[0]);
```

The snippet above enables simple interaction with the Realtime API, but there's much more that can be done. For more examples of different kinds of user interfaces, check out the [WebRTC samples](https://github.com/webrtc/samples) repository. Live demos of these samples can also be [found here](https://webrtc.github.io/samples/).

Using [media captures and streams](https://developer.mozilla.org/en-US/docs/Web/API/Media_Capture_and_Streams_API) in the browser enables you to do things like mute and unmute microphones, select which device to collect input from, and more.

### Client and server events for audio in WebRTC

By default, WebRTC clients don't need to send any client events to the Realtime API before sending audio inputs. Once a local audio track is added to the peer connection, your users can just start talking!

However, WebRTC clients still receive a number of server-sent lifecycle events as audio is moving back and forth between client and server over the peer connection. Examples include:

*   When input is sent over the local media track, you will receive [`input_audio_buffer.speech_started`](/docs/api-reference/realtime-server-events/input_audio_buffer/speech_started) events from the server.
*   When local audio input stops, you'll receive the [`input_audio_buffer.speech_stopped`](/docs/api-reference/realtime-server-events/input_audio_buffer/speech_started) event.
*   You'll receive [delta events for the in-progress audio transcript](/docs/api-reference/realtime-server-events/response/audio_transcript/delta).
*   You'll receive a [`response.done`](/docs/api-reference/realtime-server-events/response/done) event when the model has transcribed and completed sending a response.

Manipulating WebRTC APIs for media streams may give you all the control you need. However, it may occasionally be necessary to use lower-level interfaces for audio input and output. Refer to the WebSockets section below for more information and a listing of events required for granular audio input handling.

### Handling audio with WebSockets

When sending and receiving audio over a WebSocket, you will have a bit more work to do in order to send media from the client, and receive media from the server. Below, you'll find a table describing the flow of events during a WebSocket session that are necessary to send and receive audio over the WebSocket.

The events below are given in lifecycle order, though some events (like the `delta` events) may happen concurrently.

||
|Session initialization|session.update|session.createdsession.updated|
|User audio input|conversation.item.create  (send whole audio message)input_audio_buffer.append  (stream audio in chunks)input_audio_buffer.commit  (used when VAD is disabled)response.create  (used when VAD is disabled)|input_audio_buffer.speech_startedinput_audio_buffer.speech_stoppedinput_audio_buffer.committed|
|Server audio output|input_audio_buffer.clear  (used when VAD is disabled)|conversation.item.createdresponse.createdresponse.output_item.createdresponse.content_part.addedresponse.audio.deltaresponse.audio_transcript.deltaresponse.text.deltaresponse.audio.doneresponse.audio_transcript.doneresponse.text.doneresponse.content_part.doneresponse.output_item.doneresponse.donerate_limits.updated|

### Streaming audio input to the server

To stream audio input to the server, you can use the [`input_audio_buffer.append`](/docs/api-reference/realtime-client-events/input_audio_buffer/append) client event. This event requires you to send chunks of **Base64-encoded audio bytes** to the Realtime API over the socket. Each chunk cannot exceed 15 MB in size.

The format of the input chunks can be configured either for the entire session, or per response.

*   Session: `session.input_audio_format` in [`session.update`](/docs/api-reference/realtime-client-events/session/update)
*   Response: `response.input_audio_format` in [`response.create`](/docs/api-reference/realtime-client-events/response/create)

Append audio input bytes to the conversation

```javascript
import fs from 'fs';
import decodeAudio from 'audio-decode';

// Converts Float32Array of audio data to PCM16 ArrayBuffer
function floatTo16BitPCM(float32Array) {
  const buffer = new ArrayBuffer(float32Array.length * 2);
  const view = new DataView(buffer);
  let offset = 0;
  for (let i = 0; i < float32Array.length; i++, offset += 2) {
    let s = Math.max(-1, Math.min(1, float32Array[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return buffer;
}

// Converts a Float32Array to base64-encoded PCM16 data
base64EncodeAudio(float32Array) {
  const arrayBuffer = floatTo16BitPCM(float32Array);
  let binary = '';
  let bytes = new Uint8Array(arrayBuffer);
  const chunkSize = 0x8000; // 32KB chunk size
  for (let i = 0; i < bytes.length; i += chunkSize) {
    let chunk = bytes.subarray(i, i + chunkSize);
    binary += String.fromCharCode.apply(null, chunk);
  }
  return btoa(binary);
}

// Fills the audio buffer with the contents of three files,
// then asks the model to generate a response.
const files = [
  './path/to/sample1.wav',
  './path/to/sample2.wav',
  './path/to/sample3.wav'
];

for (const filename of files) {
  const audioFile = fs.readFileSync(filename);
  const audioBuffer = await decodeAudio(audioFile);
  const channelData = audioBuffer.getChannelData(0);
  const base64Chunk = base64EncodeAudio(channelData);
  ws.send(JSON.stringify({
    type: 'input_audio_buffer.append',
    audio: base64Chunk
  }));
});

ws.send(JSON.stringify({type: 'input_audio_buffer.commit'}));
ws.send(JSON.stringify({type: 'response.create'}));
```

```python
import base64
import json
import struct
import soundfile as sf
from websocket import create_connection

# ... create websocket-client named ws ...

def float_to_16bit_pcm(float32_array):
    clipped = [max(-1.0, min(1.0, x)) for x in float32_array]
    pcm16 = b''.join(struct.pack('<h', int(x * 32767)) for x in clipped)
    return pcm16

def base64_encode_audio(float32_array):
    pcm_bytes = float_to_16bit_pcm(float32_array)
    encoded = base64.b64encode(pcm_bytes).decode('ascii')
    return encoded

files = [
    './path/to/sample1.wav',
    './path/to/sample2.wav',
    './path/to/sample3.wav'
]

for filename in files:
    data, samplerate = sf.read(filename, dtype='float32')  
    channel_data = data[:, 0] if data.ndim > 1 else data
    base64_chunk = base64_encode_audio(channel_data)
    
    # Send the client event
    event = {
        "type": "input_audio_buffer.append",
        "audio": base64_chunk
    }
    ws.send(json.dumps(event))
```

### Send full audio messages

It is also possible to create conversation messages that are full audio recordings. Use the [`conversation.item.create`](/docs/api-reference/realtime-client-events/conversation/item/create) client event to create messages with `input_audio` content.

Create full audio input conversation items

```javascript
const fullAudio = "<a base64-encoded string of audio bytes>";

const event = {
  type: "conversation.item.create",
  item: {
    type: "message",
    role: "user",
    content: [
      {
        type: "input_audio",
        audio: fullAudio,
      },
    ],
  },
};

// WebRTC data channel and WebSocket both have .send()
dataChannel.send(JSON.stringify(event));
```

```python
fullAudio = "<a base64-encoded string of audio bytes>"

event = {
    "type": "conversation.item.create",
    "item": {
        "type": "message",
        "role": "user",
        "content": [
            {
                "type": "input_audio",
                "audio": fullAudio,
            }
        ],
    },
}

ws.send(json.dumps(event))
```

### Working with audio output from a WebSocket

**To play output audio back on a client device like a web browser, we recommend using WebRTC rather than WebSockets**. WebRTC will be more robust sending media to client devices over uncertain network conditions.

But to work with audio output in server-to-server applications using a WebSocket, you will need to listen for [`response.audio.delta`](/docs/api-reference/realtime-server-events/response/audio/delta) events containing the Base64-encoded chunks of audio data from the model. You will either need to buffer these chunks and write them out to a file, or maybe immediately stream them to another source like [a phone call with Twilio](https://www.twilio.com/en-us/blog/twilio-openai-realtime-api-launch-integration).

Note that the [`response.audio.done`](/docs/api-reference/realtime-server-events/response/audio/done) and [`response.done`](/docs/api-reference/realtime-server-events/response/done) events won't actually contain audio data in them - just audio content transcriptions. To get the actual bytes, you'll need to listen for the [`response.audio.delta`](/docs/api-reference/realtime-server-events/response/audio/delta) events.

The format of the output chunks can be configured either for the entire session, or per response.

*   Session: `session.output_audio_format` in [`session.update`](/docs/api-reference/realtime-client-events/session/update)
*   Response: `response.output_audio_format` in [`response.create`](/docs/api-reference/realtime-client-events/response/create)

Listen for response.audio.delta events

```javascript
function handleEvent(e) {
  const serverEvent = JSON.parse(e.data);
  if (serverEvent.type === "response.audio.delta") {
    // Access Base64-encoded audio chunks
    // console.log(serverEvent.delta);
  }
}

// Listen for server messages (WebSocket)
ws.on("message", handleEvent);
```

```python
def on_message(ws, message):
    server_event = json.loads(message)
    if server_event.type == "response.audio.delta":
        # Access Base64-encoded audio chunks:
        # print(server_event.delta)
```

## Voice activity detection
------------------------

By default, Realtime sessions have **voice activity detection (VAD)** enabled, which means the API will determine when the user has started or stopped speaking and respond automatically.

Read more about how to configure VAD in our [voice activity detection](/docs/guides/realtime-vad) guide.

### Disable VAD

VAD can be disabled by setting `turn_detection` to `null` with the [`session.update`](/docs/api-reference/realtime-client-events/session/update) client event. This can be useful for interfaces where you would like to take granular control over audio input, like [push to talk](https://en.wikipedia.org/wiki/Push-to-talk) interfaces.

When VAD is disabled, the client will have to manually emit some additional client events to trigger audio responses:

*   Manually send [`input_audio_buffer.commit`](/docs/api-reference/realtime-client-events/input_audio_buffer/commit), which will create a new user input item for the conversation.
*   Manually send [`response.create`](/docs/api-reference/realtime-client-events/response/create) to trigger an audio response from the model.
*   Send [`input_audio_buffer.clear`](/docs/api-reference/realtime-client-events/input_audio_buffer/clear) before beginning a new user input.

### Keep VAD, but disable automatic responses

If you would like to keep VAD mode enabled, but would just like to retain the ability to manually decide when a response is generated, you can set `turn_detection.interrupt_response` and `turn_detection.create_response` to `false` with the [`session.update`](/docs/api-reference/realtime-client-events/session/update) client event. This will retain all the behavior of VAD but not automatically create new Responses. Clients can trigger these manually with a [`response.create`](/docs/api-reference/realtime-client-events/response/create) event.

This can be useful for moderation or input validation or RAG patterns, where you're comfortable trading a bit more latency in the interaction for control over inputs.

## Create responses outside the default conversation
-------------------------------------------------

By default, all responses generated during a session are added to the session's conversation state (the "default conversation"). However, you may want to generate model responses outside the context of the session's default conversation, or have multiple responses generated concurrently. You might also want to have more granular control over which conversation items are considered while the model generates a response (e.g. only the last N number of turns).

Generating "out-of-band" responses which are not added to the default conversation state is possible by setting the `response.conversation` field to the string `none` when creating a response with the [`response.create`](/docs/api-reference/realtime-client-events/response/create) client event.

When creating an out-of-band response, you will probably also want some way to identify which server-sent events pertain to this response. You can provide `metadata` for your model response that will help you identify which response is being generated for this client-sent event.

Create an out-of-band model response

```javascript
const prompt = `
Analyze the conversation so far. If it is related to support, output
"support". If it is related to sales, output "sales".
`;

const event = {
  type: "response.create",
  response: {
    // Setting to "none" indicates the response is out of band
    // and will not be added to the default conversation
    conversation: "none",

    // Set metadata to help identify responses sent back from the model
    metadata: { topic: "classification" },
    
    // Set any other available response fields
    modalities: [ "text" ],
    instructions: prompt,
  },
};

// WebRTC data channel and WebSocket both have .send()
dataChannel.send(JSON.stringify(event));
```

```python
prompt = """
Analyze the conversation so far. If it is related to support, output
"support". If it is related to sales, output "sales".
"""

event = {
    "type": "response.create",
    "response": {
        # Setting to "none" indicates the response is out of band,
        # and will not be added to the default conversation
        "conversation": "none",

        # Set metadata to help identify responses sent back from the model
        "metadata": { "topic": "classification" },

        # Set any other available response fields
        "modalities": [ "text" ],
        "instructions": prompt,
    },
}

ws.send(json.dumps(event))
```

Now, when you listen for the [`response.done`](/docs/api-reference/realtime-server-events/response/done) server event, you can identify the result of your out-of-band response.

Create an out-of-band model response

```javascript
function handleEvent(e) {
  const serverEvent = JSON.parse(e.data);
  if (
    serverEvent.type === "response.done" &&
    serverEvent.response.metadata?.topic === "classification"
  ) {
    // this server event pertained to our OOB model response
    console.log(serverEvent.response.output[0]);
  }
}

// Listen for server messages (WebRTC)
dataChannel.addEventListener("message", handleEvent);

// Listen for server messages (WebSocket)
// ws.on("message", handleEvent);
```

```python
def on_message(ws, message):
    server_event = json.loads(message)
    topic = ""

    # See if metadata is present
    try:
        topic = server_event.response.metadata.topic
    except AttributeError:
        print("topic not set")
    
    if server_event.type == "response.done" and topic == "classification":
        # this server event pertained to our OOB model response
        print(server_event.response.output[0])
```

### Create a custom context for responses

You can also construct a custom context that the model will use to generate a response, outside the default/current conversation. This can be done using the `input` array on a [`response.create`](/docs/api-reference/realtime-client-events/response/create) client event. You can use new inputs, or reference existing input items in the conversation by ID.

Listen for out-of-band model response with custom context

```javascript
const event = {
  type: "response.create",
  response: {
    conversation: "none",
    metadata: { topic: "pizza" },
    modalities: [ "text" ],

    // Create a custom input array for this request with whatever context
    // is appropriate
    input: [
      // potentially include existing conversation items:
      {
        type: "item_reference",
        id: "some_conversation_item_id"
      },
      {
        type: "message",
        role: "user",
        content: [
          {
            type: "input_text",
            text: "Is it okay to put pineapple on pizza?",
          },
        ],
      },
    ],
  },
};

// WebRTC data channel and WebSocket both have .send()
dataChannel.send(JSON.stringify(event));
```

```python
event = {
    "type": "response.create",
    "response": {
        "conversation": "none",
        "metadata": { "topic": "pizza" },
        "modalities": [ "text" ],

        # Create a custom input array for this request with whatever 
        # context is appropriate
        "input": [
            # potentially include existing conversation items:
            {
                "type": "item_reference",
                "id": "some_conversation_item_id"
            },

            # include new content as well
            {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Is it okay to put pineapple on pizza?",
                    }
                ],
            }
        ],
    },
}

ws.send(json.dumps(event))
```

### Create responses with no context

You can also insert responses into the default conversation, ignoring all other instructions and context. Do this by setting `input` to an empty array.

Insert no-context model responses into the default conversation

```javascript
const prompt = `
Say exactly the following:
I'm a little teapot, short and stout! 
This is my handle, this is my spout!
`;

const event = {
  type: "response.create",
  response: {
    // An empty input array removes existing context
    input: [],
    instructions: prompt,
  },
};

// WebRTC data channel and WebSocket both have .send()
dataChannel.send(JSON.stringify(event));
```

```python
prompt = """
Say exactly the following:
I'm a little teapot, short and stout! 
This is my handle, this is my spout!
"""

event = {
    "type": "response.create",
    "response": {
        # An empty input array removes all prior context
        "input": [],
        "instructions": prompt,
    },
}

ws.send(json.dumps(event))
```

## Function calling
----------------

The Realtime models also support **function calling**, which enables you to execute custom code to extend the capabilities of the model. Here's how it works at a high level:

1.  When [updating the session](/docs/api-reference/realtime-client-events/session/update) or [creating a response](/docs/api-reference/realtime-client-events/response/create), you can specify a list of available functions for the model to call.
2.  If when processing input, the model determines it should make a function call, it will add items to the conversation representing arguments to a function call.
3.  When the client detects conversation items that contain function call arguments, it will execute custom code using those arguments
4.  When the custom code has been executed, the client will create new conversation items that contain the output of the function call, and ask the model to respond.

Let's see how this would work in practice by adding a callable function that will provide today's horoscope to users of the model. We'll show the shape of the client event objects that need to be sent, and what the server will emit in turn.

### Configure callable functions

First, we must give the model a selection of functions it can call based on user input. Available functions can be configured either at the session level, or the individual response level.

*   Session: `session.tools` property in [`session.update`](/docs/api-reference/realtime-client-events/session/update)
*   Response: `response.tools` property in [`response.create`](/docs/api-reference/realtime-client-events/response/create)

Here's an example client event payload for a `session.update` that configures a horoscope generation function, that takes a single argument (the astrological sign for which the horoscope should be generated):

[`session.update`](/docs/api-reference/realtime-client-events/session/update)

```json
{
  "type": "session.update",
  "session": {
    "tools": [
      {
        "type": "function",
        "name": "generate_horoscope",
        "description": "Give today's horoscope for an astrological sign.",
        "parameters": {
          "type": "object",
          "properties": {
            "sign": {
              "type": "string",
              "description": "The sign for the horoscope.",
              "enum": [
                "Aries",
                "Taurus",
                "Gemini",
                "Cancer",
                "Leo",
                "Virgo",
                "Libra",
                "Scorpio",
                "Sagittarius",
                "Capricorn",
                "Aquarius",
                "Pisces"
              ]
            }
          },
          "required": ["sign"]
        }
      }
    ],
    "tool_choice": "auto",
  }
}
```

The `description` fields for the function and the parameters help the model choose whether or not to call the function, and what data to include in each parameter. If the model receives input that indicates the user wants their horoscope, it will call this function with a `sign` parameter.

### Detect when the model wants to call a function

Based on inputs to the model, the model may decide to call a function in order to generate the best response. Let's say our application adds the following conversation item and attempts to generate a response:

[`conversation.item.create`](/docs/api-reference/realtime-client-events/conversation/item/create)

```json
{
  "type": "conversation.item.create",
  "item": {
    "type": "message",
    "role": "user",
    "content": [
      {
        "type": "input_text",
        "text": "What is my horoscope? I am an aquarius."
      }
    ]
  }
}
```

Followed by a client event to generate a response:

[`response.create`](/docs/api-reference/realtime-client-events/response/create)

```json
{
  "type": "response.create"
}
```

Instead of immediately returning a text or audio response, the model will instead generate a response that contains the arguments that should be passed to a function in the developer's application. You can listen for realtime updates to function call arguments using the [`response.function_call_arguments.delta`](/docs/api-reference/realtime-server-events/response/function_call_arguments/delta) server event, but `response.done` will also have the complete data we need to call our function.

[`response.done`](/docs/api-reference/realtime-server-events/response/done)

```json
{
  "type": "response.done",
  "event_id": "event_AeqLA8iR6FK20L4XZs2P6",
  "response": {
    "object": "realtime.response",
    "id": "resp_AeqL8XwMUOri9OhcQJIu9",
    "status": "completed",
    "status_details": null,
    "output": [
      {
        "object": "realtime.item",
        "id": "item_AeqL8gmRWDn9bIsUM2T35",
        "type": "function_call",
        "status": "completed",
        "name": "generate_horoscope",
        "call_id": "call_sHlR7iaFwQ2YQOqm",
        "arguments": "{\"sign\":\"Aquarius\"}"
      }
    ],
    "usage": {
      "total_tokens": 541,
      "input_tokens": 521,
      "output_tokens": 20,
      "input_token_details": {
        "text_tokens": 292,
        "audio_tokens": 229,
        "cached_tokens": 0,
        "cached_tokens_details": { "text_tokens": 0, "audio_tokens": 0 }
      },
      "output_token_details": {
        "text_tokens": 20,
        "audio_tokens": 0
      }
    },
    "metadata": null
  }
}
```

In the JSON emitted by the server, we can detect that the model wants to call a custom function:

|Property|Function calling purpose|
|---|---|
|response.output[0].type|When set to function_call, indicates this response contains arguments for a named function call.|
|response.output[0].name|The name of the configured function to call, in this case generate_horoscope|
|response.output[0].arguments|A JSON string containing arguments to the function. In our case, "{\"sign\":\"Aquarius\"}".|
|response.output[0].call_id|A system-generated ID for this function call - you will need this ID to pass a function call result back to the model.|

Given this information, we can execute code in our application to generate the horoscope, and then provide that information back to the model so it can generate a response.

### Provide the results of a function call to the model

Upon receiving a response from the model with arguments to a function call, your application can execute code that satisfies the function call. This could be anything you want, like talking to external APIs or accessing databases.

Once you are ready to give the model the results of your custom code, you can create a new conversation item containing the result via the `conversation.item.create` client event.

[`conversation.item.create`](/docs/api-reference/realtime-client-events/conversation/item/create)

```json
{
  "type": "conversation.item.create",
  "item": {
    "type": "function_call_output",
    "call_id": "call_sHlR7iaFwQ2YQOqm",
    "output": "{\"horoscope\": \"You will soon meet a new friend.\"}"
  }
}
```

*   The conversation item type is `function_call_output`
*   `item.call_id` is the same ID we got back in the `response.done` event above
*   `item.output` is a JSON string containing the results of our function call

Once we have added the conversation item containing our function call results, we again emit the `response.create` event from the client. This will trigger a model response using the data from the function call.

[`response.create`](/docs/api-reference/realtime-client-events/response/create)

```json
{
  "type": "response.create"
}
```

## Error handling
--------------

The [`error`](/docs/api-reference/realtime-server-events/error) event is emitted by the server whenever an error condition is encountered on the server during the session. Occasionally, these errors can be traced to a client event that was emitted by your application.

Unlike HTTP requests and responses, where a response is implicitly tied to a request from the client, we need to use an `event_id` property on client events to know when one of them has triggered an error condition on the server. This technique is shown in the code below, where the client attempts to emit an unsupported event type.

```javascript
const event = {
  event_id: "my_awesome_event",
  type: "scooby.dooby.doo",
};

dataChannel.send(JSON.stringify(event));
```

This unsuccessful event sent from the client will emit an error event like the following:

```json
{
  "type": "invalid_request_error",
  "code": "invalid_value",
  "message": "Invalid value: 'scooby.dooby.doo' ...",
  "param": "type",
  "event_id": "my_awesome_event"
}
```

Was this page useful?

---

# Realtime transcription

Beta

==============================

Learn how to transcribe audio in real-time with the Realtime API.

You can use the Realtime API for transcription-only use cases, either with input from a microphone or from a file. For example, you can use it to generate subtitles or transcripts in real-time. With the transcription-only mode, the model will not generate responses.

If you want the model to produce responses, you can use the Realtime API in [speech-to-speech conversation mode](/docs/guides/realtime-conversations).

## Realtime transcription sessions
-------------------------------

To use the Realtime API for transcription, you need to create a transcription session, connecting via [WebSockets](/docs/guides/realtime?use-case=transcription#connect-with-websockets) or [WebRTC](/docs/guides/realtime?use-case=transcription#connect-with-webrtc).

Unlike the regular Realtime API sessions for conversations, the transcription sessions typically don't contain responses from the model.

The transcription session object is also different from regular Realtime API sessions:

```json
{
  object: "realtime.transcription_session",
  id: string,
  input_audio_format: string,
  input_audio_transcription: [{
    model: string,
    prompt: string,
    language: string
  }],
  turn_detection: {
    type: "server_vad",
    threshold: float,
    prefix_padding_ms: integer,
    silence_duration_ms: integer,
  } | null,
  input_audio_noise_reduction: {
    type: "near_field" | "far_field"
  },
  include: list[string] | null
}
```

Some of the additional properties transcription sessions support are:

*   `input_audio_transcription.model`: The transcription model to use, currently `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, and `whisper-1` are supported
*   `input_audio_transcription.prompt`: The prompt to use for the transcription, to guide the model (e.g. "Expect words related to technology")
*   `input_audio_transcription.language`: The language to use for the transcription, ideally in ISO-639-1 format (e.g. "en", "fr"...) to improve accuracy and latency
*   `input_audio_noise_reduction`: The noise reduction configuration to use for the transcription
*   `include`: The list of properties to include in the transcription events

Possible values for the input audio format are: `pcm16` (default), `g711_ulaw` and `g711_alaw`.

You can find more information about the transcription session object in the [API reference](/docs/api-reference/realtime-sessions/transcription_session_object).

## Handling transcriptions
-----------------------

When using the Realtime API for transcription, you can listen for the `conversation.item.input_audio_transcription.delta` and `conversation.item.input_audio_transcription.completed` events.

For `whisper-1` the `delta` event will contain full turn transcript, same as `completed` event. For `gpt-4o-transcribe` and `gpt-4o-mini-transcribe` the `delta` event will contain incremental transcripts as they are streamed out from the model.

Here is an example transcription delta event:

```json
{
  "event_id": "event_2122",
  "type": "conversation.item.input_audio_transcription.delta",
  "item_id": "item_003",
  "content_index": 0,
  "delta": "Hello,"
}
```

Here is an example transcription completion event:

```json
{
  "event_id": "event_2122",
  "type": "conversation.item.input_audio_transcription.completed",
  "item_id": "item_003",
  "content_index": 0,
  "transcript": "Hello, how are you?"
}
```

Note that ordering between completion events from different speech turns is not guaranteed. You should use `item_id` to match these events to the `input_audio_buffer.committed` events and use `input_audio_buffer.committed.previous_item_id` to handle the ordering.

To send audio data to the transcription session, you can use the `input_audio_buffer.append` event.

You have 2 options:

*   Use a streaming microphone input
*   Stream data from a wav file

## Voice activity detection
------------------------

The Realtime API supports automatic voice activity detection (VAD). Enabled by default, VAD will control when the input audio buffer is committed, therefore when transcription begins.

Read more about configuring VAD in our [Voice Activity Detection](/docs/guides/realtime-vad) guide.

You can also disable VAD by setting the `turn_detection` property to `null`, and control when to commit the input audio on your end.

## Additional configurations
-------------------------

### Noise reduction

You can use the `input_audio_noise_reduction` property to configure how to handle noise reduction in the audio stream.

The possible values are:

*   `near_field`: Use near-field noise reduction.
*   `far_field`: Use far-field noise reduction.
*   `null`: Disable noise reduction.

The default value is `near_field`, and you can disable noise reduction by setting the property to `null`.

### Using logprobs

You can use the `include` property to include logprobs in the transcription events, using `item.input_audio_transcription.logprobs`.

Those logprobs can be used to calculate the confidence score of the transcription.

```json
{
  "type": "transcription_session.update",
  "input_audio_format": "pcm16",
  "input_audio_transcription": {
    "model": "gpt-4o-transcribe",
    "prompt": "",
    "language": ""
  },
  "turn_detection": {
    "type": "server_vad",
    "threshold": 0.5,
    "prefix_padding_ms": 300,
    "silence_duration_ms": 500,
  },
  "input_audio_noise_reduction": {
    "type": "near_field"
  },
  "include": [ 
    "item.input_audio_transcription.logprobs",
  ],
}
```

Was this page useful?

---

# Voice activity detection (VAD)

Beta

======================================

Learn about automatic voice activity detection in the Realtime API.

Voice activity detection (VAD) is a feature available in the Realtime API allowing to automatically detect when the user has started or stopped speaking. It is enabled by default in [speech-to-speech](/docs/guides/realtime-conversations) or [transcription](/docs/guides/realtime-transcription) Realtime sessions, but is optional and can be turned off.

## Overview
--------

When VAD is enabled, the audio is chunked automatically and the Realtime API sends events to indicate when the user has started or stopped speaking:

*   `input_audio_buffer.speech_started`: The start of a speech turn
*   `input_audio_buffer.speech_stopped`: The end of a speech turn

You can use these events to handle speech turns in your application. For example, you can use them to manage conversation state or process transcripts in chunks.

You can use the `turn_detection` property of the `session.update` event to configure how audio is chunked within each speech-to-text sample.

There are two modes for VAD:

*   `server_vad`: Automatically chunks the audio based on periods of silence.
*   `semantic_vad`: Chunks the audio when the model believes based on the words said by the user that they have completed their utterance.

The default value is `server_vad`.

Read below to learn more about the different modes.

## Server VAD
----------

Server VAD is the default mode for Realtime sessions, and uses periods of silence to automatically chunk the audio.

You can adjust the following properties to fine-tune the VAD settings:

*   `threshold`: Activation threshold (0 to 1). A higher threshold will require louder audio to activate the model, and thus might perform better in noisy environments.
*   `prefix_padding_ms`: Amount of audio (in milliseconds) to include before the VAD detected speech.
*   `silence_duration_ms`: Duration of silence (in milliseconds) to detect speech stop. With shorter values turns will be detected more quickly.

Here is an example VAD configuration:

```json
{
  "type": "session.update",
  "session": {
    "turn_detection": {
      "type": "server_vad",
      "threshold": 0.5,
      "prefix_padding_ms": 300,
      "silence_duration_ms": 500,
      "create_response": true, // only in conversation mode
      "interrupt_response": true, // only in conversation mode
    }
  }
}
```

## Semantic VAD
------------

Semantic VAD is a new mode that uses a semantic classifier to detect when the user has finished speaking, based on the words they have uttered. This classifier scores the input audio based on the probability that the user is done speaking. When the probability is low, the model will wait for a timeout, whereas when it is high, there is no need to wait. For example, user audio that trails off with an "ummm..." would result in a longer timeout than a definitive statement.

With this mode, the model is less likely to interrupt the user during a speech-to-speech conversation, or chunk a transcript before the user is done speaking.

Semantic VAD can be activated by setting `turn_detection.type` to `semantic_vad` in a [`session.update`](/docs/api-reference/realtime-client-events/session/update) event.

It can be configured like this:

```json
{
  "type": "session.update",
  "session": {
    "turn_detection": {
      "type": "semantic_vad",
      "eagerness": "low" | "medium" | "high" | "auto", // optional
      "create_response": true, // only in conversation mode
      "interrupt_response": true, // only in conversation mode
    }
  }
}
```

The optional `eagerness` property is a way to control how eager the model is to interrupt the user, tuning the maximum wait timeout. In transcription mode, even if the model doesn't reply, it affects how the audio is chunked.

*   `auto` is the default value, and is equivalent to `medium`.
*   `low` will let the user take their time to speak.
*   `high` will chunk the audio as soon as possible.

If you want the model to respond more often in conversation mode, or to return transcription events faster in transcription mode, you can set `eagerness` to `high`.

On the other hand, if you want to let the user speak uninterrupted in conversation mode, or if you would like larger transcript chunks in transcription mode, you can set `eagerness` to `low`.

Was this page useful?

---

# LiveKit Integration Documentation

## LiveKit Docs › Partner spotlight › OpenAI › Overview

---

# OpenAI and LiveKit

> Build world-class realtime AI apps with OpenAI and LiveKit Agents.

## OpenAI ecosystem support

[OpenAI](https://openai.com/) provides some of the most powerful AI models and services today, which integrate into LiveKit Agents in the following ways:

- **Realtime API**: The original production-grade speech-to-speech model. Build lifelike voice assistants with just one model.
- **GPT 4o, o1-mini, and more**: Smart and creative models for voice AI.
- **STT models**: From industry-standard `whisper-1` to leading-edge `gpt-4o-transcribe`.
- **TTS models**: Use OpenAI's latest `gpt-4o-mini-tts` to generate lifelike speech in a voice pipeline.

LiveKit Agents supports OpenAI models through the [OpenAI developer platform](https://platform.openai.com/) as well as [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/overview). See the [Azure AI integration guide](https://docs.livekit.io/agents/integrations/azure.md) for more information on Azure OpenAI.

## Getting started

Use the following guide to speak to your own OpenAI-powered voice AI agent in less than 10 minutes.

- **[Voice AI quickstart](https://docs.livekit.io/agents/start/voice-ai.md)**: Build your first voice AI app with the OpenAI Realtime API or GPT-4o.

- **[Realtime playground](https://playground.livekit.io)**: Experiment with the OpenAI Realtime API and personalities like the **Snarky Teenager** or **Opera Singer**.

## LiveKit Agents overview

LiveKit Agents is an open source framework for building realtime AI apps in Python and Node.js. It supports complex voice AI [workflows](https://docs.livekit.io/agents/build/workflows.md) with multiple agents and discrete processing steps, and includes built-in load balancing.

LiveKit provides SIP support for [telephony integration](https://docs.livekit.io/agents/start/telephony.md) and full-featured [frontend SDKs](https://docs.livekit.io/agents/start/frontend.md) in multiple languages. It uses [WebRTC](https://docs.livekit.io/home/get-started/intro-to-livekit.md#what-is-webrtc) transport for end-user devices, enabling high-quality, low-latency realtime experiences. To learn more, see [LiveKit Agents](https://docs.livekit.io/agents.md).

## Realtime API

LiveKit Agents serves as a bridge between your frontend — connected over WebRTC — and the OpenAI Realtime API — connected over WebSockets. LiveKit automatically converts Realtime API audio response buffers to WebRTC audio streams synchronized with text, and handles business logic like interruption handling automatically. You can add your own logic within your agent, and use LiveKit features for realtime state and data to coordinate with your frontend.

Additional benefits of LiveKit Agents for the Realtime API include:

- **Noise cancellation**: One line of code to remove background noise and speakers from your input audio.
- **Telephony**: Inbound and outbound calling using SIP trunks.
- **Interruption handling**: Automatically handles context truncation on interruption.
- **Transcription sync**: Realtime API text output is synced to audio playback automatically.

```mermaid
graph LR
client[App/Phone] <==LiveKit WebRTC==> agents[Agent]
agents <==WebSocket==> rtapi[Realtime API]client <-.Realtime voice.-> agents
agents -.Synced text.-> client
agents <-.Forwarded tools.-> clientagents <-."Voice buffer".-> rtapi
rtapi -."Transcriptions".-> agents
rtapi <-."Tool calls".-> agents
```

- **[Realtime API quickstart](https://docs.livekit.io/agents/start/voice-ai.md)**: Use the Voice AI quickstart with the Realtime API to get up and running in less than 10 minutes.

- **[Web and mobile frontends](https://docs.livekit.io/agents/start/frontend.md)**: Put your agent in your pocket with a custom web or mobile app.

- **[Telephony integration](https://docs.livekit.io/agents/start/telephony.md)**: Your agent can place and receive calls with LiveKit's SIP integration.

- **[Building voice agents](https://docs.livekit.io/agents/build.md)**: Comprehensive documentation to build advanced voice AI apps with LiveKit.

- **[Recipes](https://docs.livekit.io/recipes.md)**: Get inspired by LiveKit's collection of recipes and example apps.

## OpenAI plugin documentation

The following links provide more information on each available OpenAI component in LiveKit Agents.

- **[Realtime API](https://docs.livekit.io/agents/integrations/realtime/openai.md)**: LiveKit Agents docs for the OpenAI Realtime API.

- **[OpenAI Models](https://docs.livekit.io/agents/integrations/llm/openai.md)**: LiveKit Agents docs for `gpt-4o`, `o1-mini`, and other OpenAI LLMs.

- **[OpenAI STT](https://docs.livekit.io/agents/integrations/stt/openai.md)**: LiveKit Agents docs for `whisper-1`, `gpt-4o-transcribe`, and other OpenAI STT models.

- **[OpenAI TTS](https://docs.livekit.io/agents/integrations/tts/openai.md)**: LiveKit Agents docs for `tts-1`, `gpt-4o-mini-tts`, and other OpenAI TTS models.

---

This document was rendered at 2025-07-04T15:08:57.857Z.
For the latest version of this document, see [https://docs.livekit.io/agents/integrations/openai.md](https://docs.livekit.io/agents/integrations/openai.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

---

# LiveKit Docs › Getting started › Voice AI quickstart

---

# Voice AI quickstart

> Build a simple voice assistant with Python in less than 10 minutes.

## Overview

This guide walks you through the setup of your very first voice assistant using LiveKit Agents for Python. In less than 10 minutes, you'll have a voice assistant that you can speak to in your terminal, browser, telephone, or native app.

## Requirements

The following sections describe the minimum requirements to get started with LiveKit Agents.

### Python

LiveKit Agents requires Python 3.9 or later.

> ℹ️ **Looking for Node.js?**
> 
> The Node.js beta is still in development and has not yet reached v1.0. See the [v0.x documentation](https://docs.livekit.io/agents/v0.md) for Node.js reference and join the [LiveKit Community Slack](https://livekit.io/join-slack) to be the first to know when the next release is available.

### LiveKit server

You need a LiveKit server instance to transport realtime media between user and agent. The easiest way to get started is with a free [LiveKit Cloud](https://cloud.livekit.io/) account. Create a project and use the API keys in the following steps. You may also [self-host LiveKit](https://docs.livekit.io/home/self-hosting/local.md) if you prefer.

### AI providers

LiveKit Agents [integrates with most AI model providers](https://docs.livekit.io/agents/integrations.md) and supports both high-performance STT-LLM-TTS voice pipelines, as well as lifelike multimodal models.

The rest of this guide assumes you use one of the following two starter packs, which provide the best combination of value, features, and ease of setup.

**STT-LLM-TTS pipeline**:

Your agent strings together three specialized providers into a high-performance voice pipeline. You need accounts and API keys for each.

![Diagram showing STT-LLM-TTS pipeline.](/images/agents/stt-llm-tts-pipeline.svg)

| Component | Provider | Required Key | Alternatives |
| STT | [Deepgram](https://deepgram.com/) | `DEEPGRAM_API_KEY` | [STT integrations](https://docs.livekit.io/agents/integrations/stt.md#providers) |
| LLM | [OpenAI](https://platform.openai.com/) | `OPENAI_API_KEY` | [LLM integrations](https://docs.livekit.io/agents/integrations/llm.md#providers) |
| TTS | [Cartesia](https://cartesia.ai) | `CARTESIA_API_KEY` | [TTS integrations](https://docs.livekit.io/agents/integrations/tts.md#providers) |

---

**Realtime model**:

Your agent uses a single realtime model to provide an expressive and lifelike voice experience.

![Diagram showing realtime model.](/images/agents/realtime-model.svg)

| Component | Provider | Required Key | Alternatives |
| Realtime model | [OpenAI](https://platform.openai.com/docs/guides/realtime) | `OPENAI_API_KEY` | [Realtime models](https://docs.livekit.io/agents/integrations/realtime.md#providers) |

## Setup

Use the instructions in the following sections to set up your new project.

### Packages

> ℹ️ **Noise cancellation**
> 
> This example integrates LiveKit Cloud [enhanced background voice/noise cancellation](https://docs.livekit.io/home/cloud/noise-cancellation.md), powered by Krisp.
> 
> If you're not using LiveKit Cloud, omit the plugin and the `noise_cancellation` parameter from the following code.
> 
> For telephony applications, use the `BVCTelephony` model for the best results.

**STT-LLM-TTS pipeline**:

Install the following packages to build a complete voice AI agent with your STT-LLM-TTS pipeline, noise cancellation, and [turn detection](https://docs.livekit.io/agents/build/turns.md):

```shell
pip install \
  "livekit-agents[deepgram,openai,cartesia,silero,turn-detector]~=1.0" \
  "livekit-plugins-noise-cancellation~=0.2" \
  "python-dotenv"

```

---

**Realtime model**:

Install the following packages to build a complete voice AI agent with your realtime model and noise cancellation.

```shell
pip install \
  "livekit-agents[openai]~=1.0" \
  "livekit-plugins-noise-cancellation~=0.2" \
  "python-dotenv"

```

### Environment variables

Create a file named `.env` and add your LiveKit credentials along with the necessary API keys for your AI providers.

**STT-LLM-TTS pipeline**:

** Filename: `.env`**

```shell
DEEPGRAM_API_KEY=<Your Deepgram API Key>
OPENAI_API_KEY=<Your OpenAI API Key>
CARTESIA_API_KEY=<Your Cartesia API Key>
LIVEKIT_API_KEY=%{apiKey}%
LIVEKIT_API_SECRET=%{apiSecret}%
LIVEKIT_URL=%{wsURL}%

```

---

**Realtime model**:

** Filename: `.env`**

```shell
OPENAI_API_KEY=<Your OpenAI API Key>
LIVEKIT_API_KEY=%{apiKey}%
LIVEKIT_API_SECRET=%{apiSecret}%
LIVEKIT_URL=%{wsURL}%

```

### Agent code

Create a file named `agent.py` containing the following code for your first voice agent.

**STT-LLM-TTS pipeline**:

** Filename: `agent.py`**

```python
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))


```

---

**Realtime model**:

** Filename: `agent.py`**

```python
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    noise_cancellation,
)

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="coral"
        )
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))


```

## Download model files

To use the `turn-detector`, `silero`, or `noise-cancellation` plugins, you first need to download the model files:

```shell
python agent.py download-files

```

## Speak to your agent

Start your agent in `console` mode to run inside your terminal:

```shell
python agent.py console

```

Your agent speaks to you in the terminal, and you can speak to it as well.

![Screenshot of the CLI console mode.](/images/agents/start/cli-console.png)

## Connect to playground

Start your agent in `dev` mode to connect it to LiveKit and make it available from anywhere on the internet:

```shell
python agent.py dev

```

Use the [Agents playground](https://docs.livekit.io/agents/start/playground.md) to speak with your agent and explore its full range of multimodal capabilities.

Congratulations, your agent is up and running. Continue to use the playground or the `console` mode as you build and test your agent.

> 💡 **Agent CLI modes**
> 
> In the `console` mode, the agent runs locally and is only available within your terminal.
> 
> Run your agent in `dev` (development / debug) or `start` (production) mode to connect to LiveKit and join rooms.

## Next steps

Follow these guides bring your voice AI app to life in the real world.

- **[Web and mobile frontends](https://docs.livekit.io/agents/start/frontend.md)**: Put your agent in your pocket with a custom web or mobile app.

- **[Telephony integration](https://docs.livekit.io/agents/start/telephony.md)**: Your agent can place and receive calls with LiveKit's SIP integration.

- **[Building voice agents](https://docs.livekit.io/agents/build.md)**: Comprehensive documentation to build advanced voice AI apps with LiveKit.

- **[Worker lifecycle](https://docs.livekit.io/agents/worker.md)**: Learn how to manage your agents with workers and jobs.

- **[Deploying to production](https://docs.livekit.io/agents/ops/deployment.md)**: Guide to deploying your voice agent in a production environment.

- **[Integration guides](https://docs.livekit.io/agents/integrations.md)**: Explore the full list of AI providers available for LiveKit Agents.

- **[Recipes](https://docs.livekit.io/recipes.md)**: A comprehensive collection of examples, guides, and recipes for LiveKit Agents.

---

This document was rendered at 2025-07-04T15:09:45.424Z.
For the latest version of this document, see [https://docs.livekit.io/agents/start/voice-ai.md](https://docs.livekit.io/agents/start/voice-ai.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

---

# LiveKit Docs › Getting started › Web & mobile frontends

---

# Web and mobile frontends

> Bring your agent to life through a web or mobile app.

## Overview

LiveKit Agents is ready to integrate with your preferred frontend platform using the [LiveKit SDKs](https://docs.livekit.io/home/client/connect.md) for JavaScript, Swift, Android, Flutter, React Native, and more. Your agent can communicate with your frontend through LiveKit WebRTC, which provides fast and reliable realtime connectivity.

For example, a simple voice agent subscribes to the user's microphone track and publishes its own. [Text transcriptions](https://docs.livekit.io/agents/build/text.md) are also available as text streams. A more complex agent with vision capabilities can subscribe to a video track published from the user's camera or shared screen. An agent can also publish its own video to implement a virtual avatar or other features.

In all of these cases, the LiveKit SDKs are production grade and easy to use so you can build useful and advanced agents without worrying about the complexities of realtime media delivery. This topic contains resources and tips for building a high-quality frontend for your agent.

## Starter apps

LiveKit recommends using one of the following starter apps to get up and running quickly on your preferred platform. Each app is open source under the MIT License so you can freely modify it to your own needs. The mobile apps require a hosted token server, but include a [LiveKit Cloud Sandbox](https://cloud.livekit.io/projects/p_/sandbox/templates/token-server) for development purposes.

- **[SwiftUI Voice Agent](https://github.com/livekit-examples/agent-starter-swift)**: A native iOS, macOS, and visionOS voice AI assistant built in SwiftUI.

- **[Next.js Voice Agent](https://github.com/livekit-examples/agent-starter-react)**: A web voice AI assistant built with React and Next.js.

- **[Flutter Voice Agent](https://github.com/livekit-examples/voice-assistant-flutter)**: A cross-platform voice AI assistant app built with Flutter.

- **[React Native Voice Agent](https://github.com/livekit-examples/voice-assistant-react-native)**: A native voice AI assistant app built with React Native and Expo.

- **[Android Voice Agent](https://github.com/livekit-examples/android-voice-assistant)**: A native Android voice AI assistant app built with Kotlin and Jetpack Compose.

## Media and text

To learn more about realtime media and text streams, see the following documentation.

- **[Media tracks](https://docs.livekit.io/home/client/tracks.md)**: Use the microphone, speaker, cameras, and screenshare with your agent.

- **[Text streams](https://docs.livekit.io/home/client/data/text-streams.md)**: Send and receive realtime text and transcriptions.

## Data sharing

To share images, files, or any other kind of data between your frontend and your agent, you can use the following features.

- **[Byte streams](https://docs.livekit.io/home/client/data/byte-streams.md)**: Send and receive images, files, or any other data.

- **[Data packets](https://docs.livekit.io/home/client/data/packets.md)**: Low-level API for sending and receiving any kind of data.

## State and control

In some cases, your agent and your frontend code might need a custom integration of state and configuration to meet your application's requirements. In these cases, the LiveKit realtime state and data features can be used to create a tightly-coupled and responsive experience.

AgentSession automatically manages the `lk.agent.state` participant attribute to contain the appropriate string value from among `initializing`, `listening`, `thinking`, or `speaking`.

- **[State synchronization](https://docs.livekit.io/home/client/state.md)**: Share custom state between your frontend and agent.

- **[RPC](https://docs.livekit.io/home/client/data/rpc.md)**: Define and call methods on your agent or your frontend from the other side.

## Audio visualizer

The LiveKit component SDKs for React, SwiftUI, Android Compose, and Flutter include an audio visualizer component that can be used to give your voice agent a visual presence in your application.

For complete examples, see the sample apps listed above. The following documentation is a quick guide to using these components:

**React**:

Install the [React components](https://github.com/livekit/components-js/tree/main/packages/react) and [styles](https://github.com/livekit/components-js/tree/main/packages/styles) packages to use the [useVoiceAssistant](https://docs.livekit.io/reference/components/react/hook/usevoiceassistant.md) hook and the [BarVisualizer](https://docs.livekit.io/reference/components/react/component/barvisualizer.md). These components work automatically within a [LiveKitRoom](https://docs.livekit.io/reference/components/react/component/livekitroom.md) or [RoomContext.Provider](https://docs.livekit.io/reference/components/react/component/roomcontext.md)).

Also see [VoiceAssistantControlBar](https://docs.livekit.io/reference/components/react/component/voiceassistantcontrolbar.md), which provides a simple set of common UI controls for voice agent applications.

```typescript
"use client";

import "@livekit/components-styles";

import {
  useVoiceAssistant,
  BarVisualizer,
} from "@livekit/components-react";

export default function SimpleVoiceAssistant() {
  // Get the agent's audio track and current state
  const { state, audioTrack } = useVoiceAssistant();
  return (
    <div className="h-80">
      <BarVisualizer state={state} barCount={5} trackRef={audioTrack} style={{}} />
      <p className="text-center">{state}</p>
    </div>
  );
}

```

---

**Swift**:

First install the components package from [https://github.com/livekit/components-swift](https://github.com/livekit/components-swift).

Then you can use the `AgentBarAudioVisualizer` view to display the agent's audio and state:

```swift
struct AgentView: View {
    // Load the room from the environment
    @EnvironmentObject private var room: Room

    // Find the first agent participant in the room
    private var agentParticipant: RemoteParticipant? {
        for participant in room.remoteParticipants.values {
            if participant.kind == .agent {
                return participant
            }
        }
        
        return nil
    }

    // Reads the agent state property
    private var agentState: AgentState {
        agentParticipant?.agentState ?? .initializing
    }

    var body: some View {
          AgentBarAudioVisualizer(audioTrack: participant.firstAudioTrack, agentState: agentState, barColor: .primary, barCount: 5)
              .id(participant.firstAudioTrack?.id)
    }
}

```

---

**Android**:

First install the components package from [https://github.com/livekit/components-android](https://github.com/livekit/components-android).

Then you can use the `rememberVoiceAssistant` and `VoiceAssistantBarVisualizer` composables to display the visualizer, assuming you are within a `RoomScope` composable already.

```kotlin
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import io.livekit.android.compose.state.rememberVoiceAssistant
import io.livekit.android.compose.ui.audio.VoiceAssistantBarVisualizer

@Composable
fun AgentAudioVisualizer(modifier: Modifier = Modifier) {
    // Get the voice assistant instance
    val voiceAssistant = rememberVoiceAssistant()
    
    // Display the audio visualization
    VoiceAssistantBarVisualizer(
        voiceAssistant = voiceAssistant,
        modifier = modifier
            .padding(8.dp)
            .fillMaxWidth()
    )
}

```

---

**Flutter**:

First install the components package from [https://github.com/livekit/components-flutter](https://github.com/livekit/components-flutter).

```bash
flutter pub add livekit_components

```

Enable audio visualization when creating the `Room`:

```dart
// Enable audio visualization when creating the Room
final room = Room(roomOptions: const RoomOptions(enableVisualizer: true));

```

Then you can use the `SoundWaveformWidget` to display the agent's audio visualization, assuming you're using a `RoomContext`:

```dart
import 'package:flutter/material.dart';
import 'package:livekit_client/livekit_client.dart';
import 'package:livekit_components/livekit_components.dart' hide ParticipantKind;
import 'package:provider/provider.dart';

/// Shows a simple audio visualizer for an agent participant
class AgentView extends StatelessWidget {
  const AgentView({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<RoomContext>(
      builder: (context, roomContext, child) {
        // Find the agent participant in the room
        final agentParticipant = roomContext.room.remoteParticipants.values
            .where((p) => p.kind == ParticipantKind.AGENT)
            .firstOrNull;
        
        if (agentParticipant == null) {
          return const SizedBox.shrink();
        }
        
        // Get the agent's audio track for visualization
        final audioTrack = agentParticipant.audioTrackPublications
            .firstOrNull?.track as AudioTrack?;
            
        if (audioTrack == null) {
          return const SizedBox.shrink();
        }
        
        // Show the waveform visualization
        return SoundWaveformWidget(
          audioTrack: audioTrack,
          options: AudioVisualizerOptions(
            width: 32,
            minHeight: 32,
            maxHeight: 256,
            color: Theme.of(context).colorScheme.primary,
            count: 7,
          ),
        );
      },
    );
  }
}

```

## Authentication

The LiveKit SDKs require a [token](https://docs.livekit.io/home/get-started/authentication.md) to connect to a room. In web apps, you can typically include a simple token endpoint as part of the app. For mobile apps, you need a separate [token server](https://docs.livekit.io/home/server/generating-tokens.md).

## Virtual avatars

Your frontend can include a video representation of your agent using a virtual avatar from a supported provider. LiveKit includes full support for video rendering on all supported platforms. The [starter apps](#starter-apps) include support for virtual avatars. For more information and a list of supported providers, consult the documentation:

- **[Virtual avatars](https://docs.livekit.io/agents/integrations/avatar.md)**: Use a virtual avatar to give your agent a visual presence in your app.

## Responsiveness tips

This section contains some suggestions to make your app feel more responsive to the user.

### Minimize connection time

To connect your user to your agent, these steps must all occur:

1. Fetch an access token.
2. The user connects to the room.
3. Dispatch an agent process.
4. The agent connects to the room.
5. User and agent publish and subscribe to each other's media tracks.

If done in sequence, this takes up to a few seconds to complete. You can reduce this time by eliminating or parallelizing these steps.

**Option 1: "Warm" token**

In this case, your application will generate a token for the user at login with a long expiration time. When you need to connect to the room, the token is already available in your frontend.

**Option 2: Dispatch agent during token generation**

In this case, your application will optimistically create a room and dispatch the agent at the same time the token is generated, using [explicit agent dispatch](https://docs.livekit.io/agents/worker/agent-dispatch.md#explicit). This allows the user and the agent to connect to the room at the same time.

### Connection indicators

Make your app feel more responsive, even when slow to connect, by linking various events into only one or two status indicators for the user rather than a number of discrete steps and UI changes.  Refer to the [event handling](https://docs.livekit.io/home/client/events.md) documentation for more information on how to monitor the connection state and other events.

In the case that your agent fails to connect, you should notify the user and allow them to try again rather than leaving them to speak into an empty room.

- **Room connection**: The `room.connect` method can be awaited in most SDKs, and most also provide a `room.connectionState` property. Also monitor the `Disconnected` event to know when the connection is lost.
- **Agent presence**: Monitor `ParticipantConnected` events with `participant.kind === ParticipantKind.AGENT`
- **Agent state**: Access the agent's state (`initializing`, `listening`, `thinking`, or `speaking`)
- **Track subscription**: Listen for `TrackSubscribed` events to know when your media has been subscribed to.

### Effects

You should use sound effects, haptic feedback, and visual effects to make your agent feel more responsive. This is especially important during long thinking states (for instance, when performing external lookups or tool use). The [visualizer](#audio-visualizer) includes basic "thinking" state indication and also allows the user to notice when their audio is not working. For more advanced effects, use the [state and control](#state-control) features to trigger effects in your frontend.

---

This document was rendered at 2025-07-04T15:09:51.899Z.
For the latest version of this document, see [https://docs.livekit.io/agents/start/frontend.md](https://docs.livekit.io/agents/start/frontend.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

---

# LiveKit Docs › Building voice agents › Overview

---

# Building voice agents

> In-depth guide to voice AI with LiveKit Agents.

## Overview

Building a great voice AI app requires careful orchestration of multiple components. LiveKit Agents is built on top of the [Realtime SDK](https://github.com/livekit/python-sdks) to provide dedicated abstractions that simplify development while giving you full control over the underlying code.

## Agent sessions

The `AgentSession` is the main orchestrator for your voice AI app. The session is responsible for collecting user input, managing the voice pipeline, invoking the LLM, and sending the output back to the user.

Each session requires at least one `Agent` to orchestrate. The agent is responsible for defining the core AI logic - instructions, tools, etc - of your app. The framework supports the design of custom [workflows](https://docs.livekit.io/agents/build/workflows.md) to orchestrate handoff and delegation between multiple agents.

The following example shows how to begin a simple single-agent session:

```python
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import openai, cartesia, deepgram, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

session = AgentSession(
    stt=deepgram.STT(),
    llm=openai.LLM(),
    tts=cartesia.TTS(),
    vad=silero.VAD.load(),
    turn_detection=turn_detector.MultilingualModel(),
)

await session.start(
    room=ctx.room,
    agent=Agent(instructions="You are a helpful voice AI assistant."),
    room_input_options=RoomInputOptions(
        noise_cancellation=noise_cancellation.BVC(),
    ),
)

```

### RoomIO

Communication between agent and user participants happens using media streams, also known as tracks. For voice AI apps, this is primarily audio, but can include vision. By default, track management is handled by `RoomIO`, a utility class that serves as a bridge between the agent session and the LiveKit room. When an AgentSession is initiated, it automatically creates a `RoomIO` object that enables all room participants to subscribe to available audio tracks.

To learn more about publishing audio and video, see the following topics:

- **[Agent speech and audio](https://docs.livekit.io/agents/build/audio.md)**: Add speech, audio, and background audio to your agent.

- **[Vision](https://docs.livekit.io/agents/build/vision.md)**: Give your agent the ability to see images and live video.

- **[Text and transcription](https://docs.livekit.io/agents/build/text.md)**: Send and receive text messages and transcription to and from your agent.

- **[Realtime media](https://docs.livekit.io/home/client/tracks.md)**: Tracks are a core LiveKit concept. Learn more about publishing and subscribing to media.

- **[Camera and microphone](https://docs.livekit.io/home/client/tracks/publish.md)**: Use the LiveKit SDKs to publish audio and video tracks from your user's device.

#### Custom RoomIO

For greater control over media sharing in a room,  you can create a custom `RoomIO` object. For example, you might want to manually control which input and output devices are used, or to control which participants an agent listens to or responds to.

To replace the default one created in `AgentSession`, create a `RoomIO` object in your entrypoint function and pass it an instance of the `AgentSession` in the constructor. For examples, see the following in the GitHub repository:

- **[Toggling audio](https://github.com/livekit/agents/blob/main/examples/voice_agents/push_to_talk.py)**: Create a push-to-talk interface to toggle audio input and output.

- **[Toggling input and output](https://github.com/livekit/agents/blob/main/examples/voice_agents/toggle_io.py)**: Toggle both audio and text input and output.

## Voice AI providers

You can choose from a variety of providers for each part of the voice pipeline to fit your needs. The framework supports both high-performance STT-LLM-TTS pipelines and speech-to-speech models. In either case, it automatically manages interruptions, transcription forwarding, turn detection, and more.

You may add these components to the `AgentSession`, where they act as global defaults within the app, or to each individual `Agent` if needed.

- **[TTS](https://docs.livekit.io/agents/integrations/tts.md)**: Text-to-speech integrations

- **[STT](https://docs.livekit.io/agents/integrations/stt.md)**: Speech-to-text integrations

- **[LLM](https://docs.livekit.io/agents/integrations/llm.md)**: Language model integrations

- **[Multimodal](https://docs.livekit.io/agents/integrations/realtime.md)**: Realtime multimodal APIs

## Capabilities

The following guides, in addition to others in this section, cover the core capabilities of the `AgentSession` and how to leverage them in your app.

- **[Workflows](https://docs.livekit.io/agents/build/workflows.md)**: Orchestrate complex tasks among multiple agents.

- **[Tool definition & use](https://docs.livekit.io/agents/build/tools.md)**: Use tools to call external services, inject custom logic, and more.

- **[Pipeline nodes](https://docs.livekit.io/agents/build/nodes.md)**: Add custom behavior to any component of the voice pipeline.

---

This document was rendered at 2025-07-04T15:09:57.715Z.
For the latest version of this document, see [https://docs.livekit.io/agents/build.md](https://docs.livekit.io/agents/build.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

---

# Example Repositories

## Voice Assistant React Native
https://github.com/livekit-examples/voice-assistant-react-native

## Python Agents Examples

### Pipeline STT Transcriber
https://github.com/livekit-examples/python-agents-examples/blob/main/pipeline-stt/transcriber.py

### TTS Translator
https://github.com/livekit-examples/python-agents-examples/blob/main/translators/tts_translator.py