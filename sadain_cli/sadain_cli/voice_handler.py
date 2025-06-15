import speech_recognition as sr
import pyttsx3
import os
from rich.console import Console
from rich.prompt import Prompt
import threading
import queue
from pynput import keyboard
import time

console = Console()

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.key_pressed = False
        
        # Configure text-to-speech engine
        self.engine.setProperty('rate', 150)    # Speed of speech
        self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
        
        # Get available voices and set a default one
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[0].id)

    def on_press(self, key):
        """Callback for key press events."""
        self.key_pressed = True
        return False  # Stop listener

    def listen_in_background(self, source):
        """Listen in the background and put audio in queue."""
        try:
            self.is_listening = True
            audio_data = []
            
            while self.is_listening and not self.key_pressed:
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    audio_data.append(audio)
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    continue
            
            # Combine all audio data
            if audio_data:
                final_audio = audio_data[-1]
                self.audio_queue.put(final_audio)
                
        except Exception as e:
            console.print(f"[red]Error in background listening: {str(e)}[/red]")
        finally:
            self.is_listening = False

    def listen_for_command(self) -> str:
        """Listen for voice command and return the transcribed text."""
        try:
            with sr.Microphone() as source:
                console.print("[bold blue]Listening...[/bold blue]")
                console.print("[dim]Speak your command and press any key when done[/dim]")
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Reset key pressed flag
                self.key_pressed = False
                
                # Start background listening
                self.is_listening = True
                listen_thread = threading.Thread(target=self.listen_in_background, args=(source,))
                listen_thread.daemon = True
                listen_thread.start()
                
                # Wait for any key press
                with keyboard.Listener(on_press=self.on_press) as listener:
                    listener.join()
                
                # Give a small delay to ensure the last audio segment is captured
                time.sleep(0.5)
                
                # Stop listening
                self.is_listening = False
                listen_thread.join(timeout=1)
                
                console.print("[bold green]Processing speech...[/bold green]")
                
                # Get the audio from queue
                try:
                    audio = self.audio_queue.get_nowait()
                    text = self.recognizer.recognize_google(audio, language='en-US')
                    return text.lower()
                except queue.Empty:
                    return ""
                
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            console.print(f"[red]Could not request results; {str(e)}[/red]")
            return ""
        except Exception as e:
            console.print(f"[red]Error in voice recognition: {str(e)}[/red]")
            return ""

    def speak_response(self, text: str) -> None:
        """Convert text to speech and speak it."""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            console.print(f"[red]Error in text-to-speech: {str(e)}[/red]")

def handle_voice_mode() -> None:
    """Handle voice mode interaction."""
    voice_handler = VoiceHandler()
    
    console.print("[bold green]Voice mode activated![/bold green]")
    console.print("[dim]Speak your command and press any key when done.[/dim]")
    
    while True:
        # Wait for Enter to start speaking
        user_input = Prompt.ask("\nPress Enter to start speaking (or 'q' to quit)")
        if user_input.lower() == 'q':
            console.print("[bold blue]Exiting voice mode...[/bold blue]")
            break
        
        # Get voice command
        command = voice_handler.listen_for_command()
        
        if not command:
            continue
            
        if command.lower() == 'quit' or command.lower() == 'exit':
            console.print("[bold blue]Exiting voice mode...[/bold blue]")
            break
            
        # Process the command and get response
        # This will be handled by the main CLI logic
        return command 