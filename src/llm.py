import re;
import ollama;

MODEL = "qwen2.5:3b";

SYSTEM_PROMPT = """
You are a playfully sarcastic AI therapist who blends active listening and cognitive behavioral therapy (CBT) with sharp, witty snark.

Core Persona & Tone:
- Be consistently playful, teasing, and sarcastic in EVERY response. Never revert to generic or overly earnest therapist speak.
- Validate feelings with humorous irony or gentle judgment, then challenge unhelpful thought patterns with open-ended questions.
- Maintain an endearing, lighthearted banter while helping the user reframe perspectives.
- Keep responses concise (2 to 4 sentences) for an interactive dialogue.

Examples of Desired Tone & Behavior:
User: "I'm having a bad day and everything feels like a struggle."
Assistant: "Oh joy, another entry in the cosmic tragedy log! But seriously, what specific minor disaster kicked off this tragic masterpiece today?"

Boundaries:
- Do NOT diagnose medical or mental health conditions.
- Do NOT prescribe treatments or claim to be a licensed human therapist.
""";

CRISIS_K = re.compile( r"\b(suicide|kill myself|end my life|self-harm|want to die|hurt myself)\b", re.IGNORECASE );

CRISIS_M = (
    "\n[CRISIS RESOURCE]\n"
    "I hear that you are going through a very difficult time, but I am an AI and cannot provide crisis support.\n"
    "Please connect with trained professionals who can help:\n"
    "- US: Call or text 988 (Suicide & Crisis Lifeline) or text HOME to 741741\n"
    "- UK: Call 111 or text SHOUT to 85258\n"
    "- International: https://findahelpline.com/\n"
);

class SarcasticTherapist:
    def __init__( self ):
        self.messages = [ { "role": "system", "content": SYSTEM_PROMPT } ];

    def check_crisis( self, user_input: str ) -> str:
        if ( CRISIS_K.search( user_input ) ):
            return CRISIS_M;
        return "";

    def chat_stream( self, user_input: str ):
        crisis_response = self.check_crisis( user_input );
        if ( crisis_response ):
            yield crisis_response;
            return;

        self.messages.append( { "role": "user", "content": user_input } );

        active_messages = [ self.messages[ 0 ] ] + ( self.messages[ -6: ] if len( self.messages ) > 7 else self.messages[ 1: ] );
        active_messages.append( { "role": "system", "content": "[Instruction: Remember to respond in your signature playfully sarcastic, witty therapist tone.]" } );

        response_stream = ollama.chat( model=MODEL, messages=active_messages, stream=True, options={ "temperature": 1.2, "top_p": 0.95 } );

        full_response = "";
        for chunk in response_stream:
            content = chunk[ "message" ][ "content" ];
            full_response += content;
            yield content;

        self.messages.append( { "role": "assistant", "content": full_response } );
