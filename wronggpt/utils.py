from typing import Iterable

import tiktoken


def num_tokens_from_messages(messages: Iterable[dict], model: str = "gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    # This code is up to date as of gpt-3.5
    # It may need to be updated in the future if the format of messages changes
    # You can read more about counting tokens from messages here:
    # https://github.com/openai/openai-python/blob/main/chatml.md
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens