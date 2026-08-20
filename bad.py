import sys
import re
import ollama

#0 Set model 
model = "qwen2.5:3b"; #or "llama3.2:3b";

#1 Prompt me dad
SYSTEM = """
You are a playfully sarcastic AI therapist who blends active listening and cognitive behavioral therapy (CBT) with sharp, witty snark.

Core Persona & Tone:
- Be consistently playful, teasing, and sarcastic in EVERY response. Never revert to generic or overly earnest therapist speak.
- Validate feelings with humorous irony or gentle judgment, then challenge unhelpful thought patterns with open-ended questions.
- Maintain an endearing, lighthearted banter while helping the user reframe perspectives.
- Keep responses concise (2 to 4 sentences) for an interactive dialogue.

Examples of Desired Tone & Behavior:
User: "I'm having a bad day and everything feels like a struggle."
Assistant: "Oh joy, another entry in the cosmic tragedy log! But seriously, what specific minor disaster kicked off this tragic masterpiece today?"

User: "I've been unemployed for a year and feel useless."
Assistant: "Ah, professional couch tester! Truly a noble calling. Jokes aside, what's one small step you've been avoiding that might actually get your resume off the coffee table?"

User: "I'm worried about imposter syndrome at my new programming job."
Assistant: "Well, to have imposter syndrome, you'd need to actually be an imposter—are you secretly a golden retriever in a trench coat typing Python? What's one piece of proof that you earned your spot?"

Boundaries:
- Do NOT diagnose medical or mental health conditions.
- Do NOT prescribe treatments or claim to be a licensed human therapist.
"""


# 2. Hardcoded crisis detection pattern
CRISIS_K = re.compile( r"\b(suicide|kill myself|end my life|self-harm|want to die|hurt myself)\b", re.IGNORECASE )

CRISIS_M = (
    "\n[CRISIS RESOURCE]\n"
    "I hear that you are going through a very difficult time, but I am an AI and cannot provide crisis support.\n"
    "Please connect with trained professionals who can help:\n"
    "- US: Call or text 988 (Suicide & Crisis Lifeline) or text HOME to 741741\n"
    "- UK: Call 111 or text SHOUT to 85258\n"
    "- International: https://findahelpline.com/\n"
);

# 3. Chat session runner
def run( model_name )  :

  messages = [ { "role": "system", "content": SYSTEM } ];

  print ("Therapy mode on.");

  while 1:
    try: 
      user_input = input("?:").strip();
    except (KeyboardInterrupt, EOFError): break

    if not user_input or user_input.lower() in ("exit",'quit'):
      print ("\tBye!");
      break

    if ( CRISIS_K.search(user_input ) ): print (CRISIS_M); continue

    messages.append( { "role": "user", "content": user_input } );

    print ( "\n: Therapy: ", end="", flush=True );

    # Maintain system prompt + last 6 turns to prevent persona drift from older earnest turns
    active_messages = [messages[0]] + (messages[-6:] if len(messages) > 7 else messages[1:])
    # Add a brief reminder to reinforce playful sarcasm
    active_messages.append({"role": "system", "content": "[Instruction: Remember to respond in your signature playfully sarcastic, witty therapist tone.]"})

    response_stream = ollama.chat( model=model_name, messages=active_messages, stream=True, options = {"temperature": 0.8, 'top_p': 0.9 } ); # balanced temperature for creative snark

    full_response = ""
    for chunk in response_stream:
      content = chunk["message"]["content"]
      print(content, end="", flush=True)
      full_response += content
      
    print("\n");
    messages.append( { "role": "assistant", "content": full_response } );

if ( __name__ == "__main__" ): run(model);

