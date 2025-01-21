import gradio as gr
import assemblyai as aai
from translate import Translator
import uuid
from elevenlabs.client import ElevenLabs
from elevenlabs import ElevenLabs, VoiceSettings
from pathlib import Path
from langdetect import detect

def voice_to_voice(audio_file, selected_languages):
    # Step 1: Transcribe the audio file
    transcript = audio_transcription(audio_file)
    if transcript.status == aai.TranscriptStatus.error:
        raise gr.Error(transcript.error)
    else:
        transcript = transcript.text  # Extract the text from the transcription

    # Step 2: Detect the language of the transcription
    detected_language = detect(transcript)

    # Step 3: Translate the transcribed text
    list_translations = text_translation(transcript, detected_language, selected_languages)
    if not list_translations:  # Handle potential None or empty cases
        raise gr.Error("Translation failed or returned no data.")

    # Step 4: Convert translated text to speech
    detected_audio_paths = []
    for translation in list_translations:
        translated_file = text_to_speech(translation)
        path = Path(translated_file)
        detected_audio_paths.append(str(path))

    return detected_audio_paths  # Return paths to the audio files

def audio_transcription(audio_file):
    aai.settings.api_key = "YOUR API KEY"
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    return transcript

def text_translation(text: str, source_language: str, selected_languages):
    # Translate text into multiple languages
    list_translations = []
    try:
        for lang in selected_languages:
            translator = Translator(from_lang=source_language, to_lang=lang)
            translation = translator.translate(text)
            list_translations.append(translation)
    except Exception as e:
        print(f"Translation error: {e}")
    return list_translations  # Ensure this returns a list

def text_to_speech(text: str) -> str:
    client = ElevenLabs(
        api_key="YOUR API KEY",
    )

    # Calling the text_to_speech conversion API with detailed parameters
    response = client.text_to_speech.convert(
        voice_id="xCNq7JR1tNb5b06HnQmY",  # Clone your voice on ElevenLabs dashboard and copy the ID
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_multilingual_v2",  # Use the turbo model for low latency, for other languages use eleven_multilingual_v2
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.8,
            style=0.5,
            use_speaker_boost=True,
        ),
    )

    save_file_path = f"{uuid.uuid4()}.mp3"

    # Writing the audio to a file
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{save_file_path}: A new audio file was saved successfully!")
    return str(Path(save_file_path))

audio_input = gr.Audio(
    sources=["microphone"],
    type="filepath",
)

languages = {
    "Hindi": "hi",
    "Spanish": "es",
    "Korean": "ko",
    "French": "fr",
    "German": "de",
    "Bengali": "bn",
    "Japanese": "ja",
    "Arabic": "ar",
    "Turkish": "tr",
}

language_selector = gr.CheckboxGroup(
    choices=list(languages.keys()),
    label="Select languages for translation",
    value=["Hindi", "Spanish", "Korean"]
)

def process_audio_translation(audio_file, langs_selected):
    # Convert selected language names to language codes
    selected_language_codes = [languages[lang] for lang in langs_selected]
    audio_paths = voice_to_voice(audio_file, selected_language_codes)
    
    # Ensure the output list has exactly three items (pad with None if needed)
    while len(audio_paths) < 3:
        audio_paths.append(None)
    return audio_paths[:3]

demo = gr.Interface(
    fn=process_audio_translation,
    inputs=[audio_input, language_selector],
    outputs=[
        gr.Audio(label="Translated Audio 1"),
        gr.Audio(label="Translated Audio 2"),
        gr.Audio(label="Translated Audio 3"),
    ],
    title="Voice-to-Voice Translator",
    description="Upload an audio file, detect the language, select the target languages for translation, and listen to the translated audio in your chosen languages."
)

if __name__ == "__main__":
    demo.launch()
