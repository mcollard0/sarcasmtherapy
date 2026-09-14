import os;
import sys;
import re;
from llm import SarcasticTherapist;
from audio import AudioPipeline;

def main():
    debug_mode = "--debug" in sys.argv;
    if ( not debug_mode ):
        print( "Initializing SarcasmTherapy Voice Bot... (Run with --debug to see ALSA logs)" );
    else:
        print( "Initializing SarcasmTherapy Voice Bot in DEBUG mode..." );
    
    # Path to the Piper model (defaults to ryan if present, falls back to voice.onnx)
    ryan_path = os.path.join( os.path.dirname( __file__ ), "..", "models", "en_US-ryan-medium.onnx" );
    default_path = os.path.join( os.path.dirname( __file__ ), "..", "models", "voice.onnx" );
    
    # Check if a custom --voice argument was supplied
    model_path = ryan_path if os.path.exists( ryan_path ) else default_path;
    for idx, arg in enumerate( sys.argv ):
        if ( arg == "--voice" and idx + 1 < len( sys.argv ) ):
            custom_name = sys.argv[ idx + 1 ];
            candidate = os.path.join( os.path.dirname( __file__ ), "..", "models", custom_name );
            if ( not candidate.endswith( ".onnx" ) ):
                candidate += ".onnx";
            if ( os.path.exists( candidate ) ):
                model_path = candidate;
            else:
                print( f"Warning: Voice '{custom_name}' not found at {candidate}. Using default." );
    
    if ( not os.path.exists( model_path ) ):
        print( f"Error: Piper TTS model not found at {model_path}." );
        sys.exit( 1 );
        
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
