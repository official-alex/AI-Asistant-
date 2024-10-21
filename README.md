# 🎤 Speech Recognition AI Conversation System

This repository contains a real-time speech recognition system powered by [Groq](https://console.groq.com) and [ElevenLabs](https://elevenlabs.io). It listens for audio input 🎧, processes it using an AI personality 🤖, and responds via speech synthesis 🎙️.

---

### 🌟 **Features:**
- **🛠️ Custom Trigger Word:** Set your own trigger word for AI activation.
- **🧠 AI Personality:** Customize the AI's personality and response style.
- **🔊 Speech Synthesis:** Uses ElevenLabs API to convert text responses into speech.

---

## 🚀 **Setup Instructions**

1. **📥 Clone the Repository:**
   ```bash
   https://github.com/official-alex/AI-Assistant.git
   cd AI-Assistant
   ```

2. **📦 Install Dependencies:**
   Ensure Python 3.8+ is installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **🔑 Set Up Environment Variables:**
   Edit a `.env` file in the project root and add the following:
   ```plaintext
   GROQ_API_KEY=your_groq_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```

   - For the Groq API key, go to [Groq Console](https://console.groq.com/keys) 🔗.
   - For the ElevenLabs API key, log in to [ElevenLabs](https://elevenlabs.io), click your profile (bottom left), and navigate to "API Keys" 🔑.

4. **▶️ Run the Application:**
   Start the live speech recognition system with:
   ```bash
   python main.py
   ```

5. **⚙️ Modify AI Personality & Trigger Word:**
   Change the `trigger_word` and `personality` in the `LiveSpeechRecognition` class to customize how the AI interacts with you.

---

## 📝 **Usage**

- **▶️ Start Listening:** The system will start listening for your input.
- **🗣️ Trigger Word:** Say the trigger word (default: `bob`) to activate AI processing.
- **🛑 Stop:** You can say "stop" to halt the recognition.

---

### 💾 Save Transcriptions and Errors

Upon termination, the system saves a transcript of recognized speech to `transcription_history.txt` and logs any errors in `error_log.txt`.
