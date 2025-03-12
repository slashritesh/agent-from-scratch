import instructor
from groq import Groq
import os


groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

client = instructor.from_groq(groq,mode=instructor.Mode.JSON)



res = client.chat.completions.create(
    max_retries=1,
    messages=
)