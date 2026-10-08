import os
import tempfile
import re

import speech_recognition as sr
from pydub import AudioSegment
from deepmultilingualpunctuation import PunctuationModel


# =========================================================
# PUNCTUATION MODEL
# =========================================================

punct_model = PunctuationModel()


# =========================================================
# FFMPEG CONFIGURATION
# =========================================================

AudioSegment.converter = (
    r"C:\Users\HP\Downloads\ffmpeg-8.1.2-essentials_build"
    r"\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe"
)


# =========================================================
# SPEECH TO TEXT
# =========================================================

def speech_to_text(audio_file):

    recognizer = sr.Recognizer()

    wav_path = None

    try:

        # -------------------------------------------------
        # 1. Load uploaded audio
        # -------------------------------------------------

        sound = AudioSegment.from_file(audio_file)


        # -------------------------------------------------
        # 2. Convert audio to mono
        # -------------------------------------------------

        sound = sound.set_channels(1)


        # -------------------------------------------------
        # 3. Set sample rate to 16000 Hz
        # -------------------------------------------------

        sound = sound.set_frame_rate(16000)


        # -------------------------------------------------
        # 4. Create temporary WAV file
        # -------------------------------------------------

        temp_wav = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        )

        wav_path = temp_wav.name
        temp_wav.close()


        # -------------------------------------------------
        # 5. Export audio as WAV
        # -------------------------------------------------

        sound.export(
            wav_path,
            format="wav"
        )


        # -------------------------------------------------
        # 6. Read WAV file
        # -------------------------------------------------

        with sr.AudioFile(wav_path) as source:

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

            audio_data = recognizer.record(source)


        # -------------------------------------------------
        # 7. Speech Recognition
        # -------------------------------------------------

        text = recognizer.recognize_google(
            audio_data,
            language="en-IN"
        )


        # -------------------------------------------------
        # 8. Restore Punctuation
        # -------------------------------------------------

        text = punct_model.restore_punctuation(text)


        # -------------------------------------------------
        # 9. Improve Capitalization
        # -------------------------------------------------

        text = text.strip()

        if text:

            # Capitalize first letter
            text = text[0].upper() + text[1:]


        # -------------------------------------------------
        # 10. Capitalize after sentence endings
        # -------------------------------------------------

        text = re.sub(
            r'([.!?]\s+)([a-z])',
            lambda match:
            match.group(1) + match.group(2).upper(),
            text
        )


        # -------------------------------------------------
        # 11. Add comma after common greetings
        # -------------------------------------------------

        text = re.sub(
            r'^(Good morning|Good afternoon|Good evening)\s+everyone',
            r'\1, everyone',
            text,
            flags=re.IGNORECASE
        )


        # -------------------------------------------------
        # 12. Add final full stop
        # -------------------------------------------------

        if text and text[-1] not in ".!?":

            text += "."


        # -------------------------------------------------
        # 13. Return final text
        # -------------------------------------------------

        return text


    # =====================================================
    # ERROR HANDLING
    # =====================================================

    except sr.UnknownValueError:

        return "Sorry, could not understand the audio."


    except sr.RequestError:

        return "Google Speech Recognition service is unavailable."


    except Exception as e:

        return f"Error: {str(e)}"


    # =====================================================
    # DELETE TEMPORARY WAV FILE
    # =====================================================

    finally:

        if wav_path and os.path.exists(wav_path):

            try:

                os.remove(wav_path)

            except Exception:

                pass