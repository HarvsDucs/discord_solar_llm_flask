import discord
import requests
import json
from pinecone import Pinecone
from dotenv import load_dotenv
import os
from supabase import create_client, Client
load_dotenv()

# --- Supabase Setup ---
SUPABASE_URL = os.environ.get("SUPABASE_URL") # Placeholder - replace with your Supabase project URL
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") # Placeholder - replace with your Supabase API key
SUPABASE_TABLE_NAME = os.environ.get("SUPABASE_TABLE_NAME") # You can customize your table name

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Pinecone Setup ---
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY") # Placeholder - replace with your Pinecone API key
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME") # You can customize your index name
PINECONE_NAMESPACE = os.environ.get("PINECONE_NAMESPACE") # You can customize your namespace

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)


url_embed = os.environ.get("URL_EMBED") # Placeholder URL - replace with your actual embedding API endpoint
API_KEY = os.environ.get("API_KEY") # Placeholder - replace with your actual API key if needed (same as chunking for this example)
headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        print(message.content)
        data_embed = {
            "text": message.content[6:]
}
        
        try:
            response = requests.post(url_embed, headers=headers, json=data_embed)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            print("Request successful!")
            print("Status code:", response.status_code)

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if response is not None:
                print(f"Status code: {response.status_code}")
                print("Response text (for debugging):", response.text)

        response_pinecone = index.query(
            namespace="",
            vector=response.json(), 
            top_k=3,
            include_metadata=True,
            include_values=False
        )

        i = 0
        reply = [""] * 3

        for i in range(3):
            match = response_pinecone['matches'][i]

            id_value = match['id']

            response = (
                    supabase.table("vector_text")
                    .select("text", "headers")
                    .eq("id", id_value)
                .execute())

            headerz = response.data[0]['headers']
            text = response.data[0]['text']
                
            reply[i] = f"Rank {i+1} reference with HEADER: {headerz}  \nTEXT: {text}\n\n"
            i += 1

        final_reply = "\n".join(reply)

        if len(final_reply) > 1990:
            final_reply = final_reply[:1990] + "..."
            
        await message.channel.send(final_reply)

client.run(os.environ.get("DISCORD_CLIENT_RUN"))
