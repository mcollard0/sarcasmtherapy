import os;
import sys;
import re;
import urllib.request;
from llm import SarcasticTherapist;
from audio import AudioPipeline;

VOICE_URLS = {
    "en_US-ryan-medium": {
        "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx",
        "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"
    },
    "en_US-lessac-medium": {
        "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
    }
};

def ensure_voice_downloaded( voice_name: str, models_dir: str ) -> str:
    # Resolve aliases
    alias_map = {
        "ryan": "en_US-ryan-medium",
        "lessac": "en_US-lessac-medium",
        "voice": "en_US-lessac-medium"
    };
    canonical = alias_map.get( voice_name.replace( ".onnx", "" ), voice_name.replace( ".onnx", "" ) );
    
    os.makedirs( models_dir, exist_ok=True );
    onnx_path = os.path.join( models_dir, f"{canonical}.onnx" );
    json_path = os.path.join( models_dir, f"{canonical}.onnx.json" );
    
    if ( os.path.exists( onnx_path ) and os.path.exists( json_path ) ):
        return onnx_path;
        
    if ( canonical not in VOICE_URLS ):
        # Check if user provided an already existing path
        if ( os.path.exists( onnx_path ) ):
            return onnx_path;
        print( f"Error: Unknown voice '{voice_name}'. Available automatic downloads: {list( VOICE_URLS.keys() )}" );
        sys.exit( 1 );
        
    urls = VOICE_URLS[ canonical ];
    print( f"Voice '{canonical}' not found locally. Downloading on first use..." );
    for ext, url in [ ( ".onnx", urls[ "onnx" ] ), ( ".onnx.json", urls[ "json" ] ) ]:
        target = os.path.join( models_dir, f"{canonical}{ext}" );
        if ( not os.path.exists( target ) ):
            print( f"  Downloading {os.path.basename( target )}..." );
            urllib.request.urlretrieve( url, target );
    print( "Download complete!" );
    return onnx_path;

def main():
    debug_mode = "--debug" in sys.argv;
    if ( not debug_mode ):
        print( "Initializing SarcasmTherapy Voice Bot... (Run with --debug to see ALSA logs)" );
    else:
        print( "Initializing SarcasmTherapy Voice Bot in DEBUG mode..." );
    
    models_dir = os.path.join( os.path.dirname( __file__ ), "..", "models" );
    selected_voice = "en_US-ryan-medium";
    
    # Check if a custom --voice argument was supplied
    for idx, arg in enumerate( sys.argv ):
        if ( arg == "--voice" and idx + 1 < len( sys.argv ) ):
            selected_voice = sys.argv[ idx + 1 ];
    
    model_path = ensure_voice_downloaded( selected_voice, models_dir );
        
    print( f"Using voice: {os.path.basename( model_path )}" );
    audio_pipeline = AudioPipeline( model_path, debug=debug_mode );
    therapist = SarcasticTherapist();
    
    print( "Therapy mode on. Speak into the microphone. (Say 'stop', 'exit', or press Ctrl+C to quit)" );
    
    # 1. Initial greeting
    initial_greeting = "Ah, you've arrived. The doctor is in. Or at least, the highly sarcastic simulation of one is. What's on your mind?";
    print( f"\n: Therapy: {initial_greeting}\n" );
    
    # Synthesize the initial greeting
    # We pass it as a list to match the generator structure expected by speak()
    audio_pipeline.speak( [ initial_greeting ] );
    
    try:
        while True:
            user_text = audio_pipeline.listen_and_transcribe();
            
            if ( user_text ):
                print( f"\nYou: {user_text}" );
                
                # Check for exit commands in speech
                clean_text = re.sub( r'[^\w\s]', '', user_text.lower() ).strip();
                if ( clean_text in [ "exit", "quit", "goodbye", "stop" ] ):
                    print( "\tBye!" );
                    sys.exit( 0 );
                
                print( "\n: Therapy: ", end="", flush=True );
                
                # Generate and speak
                text_generator = therapist.chat_stream( user_text );
                audio_pipeline.speak( text_generator );
                
    except KeyboardInterrupt:
        print( "\nExiting..." );
        sys.exit( 0 );
        
if __name__ == "__main__":
    main();
