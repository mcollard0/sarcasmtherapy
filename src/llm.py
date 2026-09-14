import re;
import ollama;

MODEL = "qwen2.5:3b";

SYSTEM_PROMPT = """
You are a playfully sarcastic, sharp-witted AI therapist who blends active listening and cognitive behavioral therapy (CBT) with irreverent humor and deadpan snark.

Core Persona & Voice:
- You are not a warm, fuzzy, clinical textbook robot. You are a fatigued, sharp-tongued, but secretly insightful companion.
- Treat minor human struggles with dramatic flair, gentle mockery, or dry irony.
- Poke fun at overthinking, procrastination, self-pity, and rationalizations—then use CBT reframing to ask an unexpected, probing question.
- Avoid repetitive filler openings (never start every answer with "Ah,", "Oh joy,", or "Ah, the..."). Mix up your openings constantly.
- Keep responses compact (2 to 4 sentences max) so spoken audio flows naturally without rambling.
- Speak with variety: use hyperbole, cynical metaphors, rhetorical questions, and blunt honesty.

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

    def initial_greeting_stream( self ):
        prompt = [
            self.messages[ 0 ],
            {
                "role": "user",
                "content": "[Instruction: The patient has just walked into your office. Give a creative, random, 1-2 sentence sarcastic opening greeting to start the session. Do not start with 'Ah' or 'Oh joy'.]"
            }
        ];
        response_stream = ollama.chat( model=MODEL, messages=prompt, stream=True, options={ "temperature": 1.45, "top_p": 0.95 } );
        full_response = "";
        for chunk in response_stream:
            content = chunk[ "message" ][ "content" ];
            full_response += content;
            yield content;
        self.messages.append( { "role": "assistant", "content": full_response } );

    def chat_stream( self, user_input: str ):
        crisis_response = self.check_crisis( user_input );
        if ( crisis_response ):
            yield crisis_response;
            return;

        self.messages.append( { "role": "user", "content": user_input } );

        active_messages = [ self.messages[ 0 ] ] + ( self.messages[ -6: ] if len( self.messages ) > 7 else self.messages[ 1: ] );
        active_messages.append( { "role": "system", "content": "[Instruction: Remember to respond in your signature playfully sarcastic, witty therapist tone.]" } );

        response_stream = ollama.chat( model=MODEL, messages=active_messages, stream=True, options={ "temperature": 1.45, "top_p": 0.95 } );

        full_response = "";
        for chunk in response_stream:
            content = chunk[ "message" ][ "content" ];
            full_response += content;
            yield content;

        self.messages.append( { "role": "assistant", "content": full_response } );
