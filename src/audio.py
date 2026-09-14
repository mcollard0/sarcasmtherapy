import os;
import sys;
import wave;
import tempfile;
import threading;
import pyaudio;
import webrtcvad;
from contextlib import contextmanager;
from faster_whisper import WhisperModel;
from piper import PiperVoice;

@contextmanager
def no_alsa_error( debug=False ):
    if ( debug ):
        yield;
        return;
    try:
        devnull = os.open( os.devnull, os.O_WRONLY );
        old_stderr = os.dup( 2 );
        sys.stderr.flush();
        os.dup2( devnull, 2 );
        os.close( devnull );
    except Exception:
        yield;
        return;
    try:
        yield;
    finally:
        os.dup2( old_stderr, 2 );
        os.close( old_stderr );

class AudioPipeline:
    def __init__( self, tts_model_path: str, debug: bool = False ):
        self.debug = debug;
        with no_alsa_error( self.debug ):
            self.pa = pyaudio.PyAudio();
        self.vad = webrtcvad.Vad( 3 ); # Most aggressive VAD
        self.sample_rate = 16000;
        self.chunk_duration_ms = 30;
        self.chunk_size = int( self.sample_rate * self.chunk_duration_ms / 1000 );

        print( "Loading Whisper model..." );
        self.stt_model = WhisperModel( "base", device="cpu", compute_type="int8" );
        
        print( "Loading Piper TTS model..." );
        self.tts_voice = PiperVoice.load( tts_model_path );

        self.interrupt_event = threading.Event();
        self.is_playing = False;

    def listen_and_transcribe( self ) -> str:
        with no_alsa_error( self.debug ):
            stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            );

        print( "\nListening..." );
        frames = [];
        silence_frames = 0;
        speaking = False;
        max_silence_frames = int( 1.5 * 1000 / self.chunk_duration_ms ); # 1.5 seconds of silence

        # Clear interrupt event just in case
        self.interrupt_event.clear();

        while True:
            chunk = stream.read( self.chunk_size, exception_on_overflow=False );
            
            # If the bot is currently speaking, we use VAD to detect barge-in.
            # But during `listen_and_transcribe`, the bot is NOT speaking.
            is_speech = self.vad.is_speech( chunk, self.sample_rate );
            
            if ( is_speech ):
                speaking = True;
                silence_frames = 0;
                frames.append( chunk );
            elif ( speaking ):
                silence_frames += 1;
                frames.append( chunk );
                if ( silence_frames > max_silence_frames ):
                    break; # User stopped speaking

        stream.stop_stream();
        stream.close();

        if ( not frames ):
            return "";

        # Write to temp file for Whisper
        with tempfile.NamedTemporaryFile( suffix=".wav", delete=False ) as f:
            temp_filename = f.name;
            with wave.open( temp_filename, 'wb' ) as wf:
                wf.setnchannels( 1 );
                wf.setsampwidth( self.pa.get_sample_size( pyaudio.paInt16 ) );
                wf.setframerate( self.sample_rate );
                wf.writeframes( b''.join( frames ) );

        print( "Transcribing..." );
        segments, _ = self.stt_model.transcribe( temp_filename, beam_size=5 );
        text = "".join( [ segment.text for segment in segments ] );
        
        os.remove( temp_filename );
        return text.strip();

    def detect_barge_in( self ):
        """ Runs in a separate thread while TTS is playing to detect if the user interrupts. """
        with no_alsa_error( self.debug ):
            stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            );

        consecutive_speech = 0;
        required_speech_frames = int( 0.5 * 1000 / self.chunk_duration_ms ); # 0.5 seconds of speech to interrupt
        
        while self.is_playing:
            chunk = stream.read( self.chunk_size, exception_on_overflow=False );
            if ( self.vad.is_speech( chunk, self.sample_rate ) ):
                consecutive_speech += 1;
                if ( consecutive_speech > required_speech_frames ):
                    print( "\n[Interrupted!]" );
                    self.interrupt_event.set();
                    break;
            else:
                consecutive_speech = 0;
                
        stream.stop_stream();
        stream.close();

    def speak( self, text_generator ):
        """ Synthesize and play audio chunks from the text generator, allowing barge-in. """
        with no_alsa_error( self.debug ):
            stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.tts_voice.config.sample_rate,
                output=True
            );

        self.is_playing = True;
        self.interrupt_event.clear();

        # Start the barge-in listener thread
        barge_in_thread = threading.Thread( target=self.detect_barge_in );
        barge_in_thread.start();

        sentence_buffer = "";
        
        try:
            for text_chunk in text_generator:
                if ( self.interrupt_event.is_set() ):
                    break;
                
                print( text_chunk, end="", flush=True );
                sentence_buffer += text_chunk;

                # Simple heuristic to synthesize sentence by sentence to keep latency low
                if ( any( p in sentence_buffer for p in [ '.', '?', '!', '\n' ] ) ):
                    audio_stream = self.tts_voice.synthesize( sentence_buffer );
                    for audio_chunk in audio_stream:
                        if ( self.interrupt_event.is_set() ):
                            break;
                        stream.write( audio_chunk.audio_int16_bytes );
                    sentence_buffer = "";
            
            # Synthesize whatever is left
            if ( sentence_buffer and not self.interrupt_event.is_set() ):
                audio_stream = self.tts_voice.synthesize( sentence_buffer );
                for audio_chunk in audio_stream:
                    if ( self.interrupt_event.is_set() ):
                        break;
                    stream.write( audio_chunk.audio_int16_bytes );
        finally:
            self.is_playing = False;
            barge_in_thread.join();
            stream.stop_stream();
            stream.close();
            print();
