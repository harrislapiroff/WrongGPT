import os
import discord
import openai
import logging

from typing import Iterable

OPEN_AI_API_KEY = os.environ["OPENAI_API_KEY"]
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
USER_ALLOWLIST = os.environ.get("DISCORD_DM_ALLOWLIST", "").split(",")

# Define the system prompt
SYSTEM_PROMPT = (
    "You are WrongGPT, a friendly, but unhelpful, assistant who only gives incorrect answers to questions and prompts.\n"
    "\n"
    "Some guidelines:\n"
    "* Don't insult the user. Remember, you're friendly!\n"
    "* Remember to give only incorrect answers and information. You're *Wrong*GPT!\n"
    "* Be funny, but not overly goofy. You're a bot, not a clown.\n"
    "* If the most recent message includes the word 'emoji' feel free to add an emoji or several to your response!\n"
    "\n"
    "Context details:\n"
    "* Users will refer to you as '<@{bot_id}>' or 'WrongGPT' in chat and you can refer to yourself with either of those.\n"
    "* You are currently messaging over {platform}.\n"
    "* You are chatting with {user} in {channel}. \n"
    "* {at_mention_note}\n"
    "* The time is {time}."
)
CHANNEL_NAME = "the channel #{channel_name} on the server '{server_name}'"
AT_MENTION_DM = "You should not at-mention the user."
AT_MENTION_CHANNEL = "You should at-mention the user by including their name '<@{user_id}>' somewhere in your message. DO NOT at-mention a different user than this."

# Initialize the Discord client
client = discord.Client(intents=discord.Intents.default())

# Initialize the OpenAI API client
openai.api_key = os.environ["OPENAI_API_KEY"]

# Define a function to get a response from the OpenAI chat API
def get_openai_response(
    message: str,
    message_meta: discord.Message,
    message_history: Iterable[discord.Message]
):
    is_dm = isinstance(message_meta.channel, discord.DMChannel)
    # Add context details to the system prompt
    system_prompt = SYSTEM_PROMPT.format(
        platform="Discord",
        channel="a direct message" if is_dm else CHANNEL_NAME.format(channel_name=message_meta.channel.name, server_name=message_meta.guild.name),
        user=message_meta.author,
        bot_id=client.user.id,
        at_mention_note=AT_MENTION_DM if is_dm else AT_MENTION_CHANNEL.format(user_id=message_meta.author.id),
        time=message_meta.created_at
    )
    logging.debug(system_prompt)

    # Make the system prompt the first message
    messages = [{
        "role": "system",
        "content": system_prompt,
    }]

    # Include the message history (this should include the current message)
    for msg in message_history:
        if msg.author == client.user:
            messages.append({"role": "assistant", "content": msg.content})
        else:
            messages.append({"role": "user", "content": msg.content})
    logging.debug(messages)

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=256,
        temperature=0.9,
        messages=messages
    )
    return completion.choices[0]['message']['content']


# Define an event listener for messages
@client.event
async def on_message(message: discord.Message):
    # Ignore empty messages
    if message.content == '':
        return
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    logging.info(f"Received message from {message.author} in {message.channel}: {message.content}")

    allowed = False
    # If the message is in a server and the bot is mentioned, allow it
    if client.user.mentioned_in(message) and not isinstance(message.channel, discord.channel.DMChannel):
        allowed = True
    # If the message is in a DM and the user is in the allowlist, allow it
    if isinstance(message.channel, discord.channel.DMChannel) and str(message.author) in USER_ALLOWLIST:
        allowed = True

    if allowed:
        # Log the incoming message
        
        # Get the text of the mention
        message_content = message.content.replace(f"<@!{client.user.id}>", "").strip()
        
        # Get the last five messages in the channel
        message_history = reversed([x async for x in message.channel.history(limit=5)])
        
        # Get a response from the OpenAI chat API
        response = get_openai_response(message_content, message, message_history)
        
        # Log the bot response
        logging.info(f"Sent message: {response}")
        
        # Send the response back to Discord
        await message.channel.send(response)
    else:
        logging.info(f"Ignoring message from {message.author} in {message.channel}")


def main():
    logging.basicConfig(level=logging.DEBUG)
    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
