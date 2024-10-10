from openai import OpenAI # openai==1.2.0
import os



client = OpenAI(
    api_key=os.environ.get("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1/solar"
)

stream = client.chat.completions.create(
    model="solar-pro",
    messages=[
        {
            "role": "system",
            "content": "You are the person making the funniest cleverest novel concise jokes. They should be short, funny, clever, innovative, visual, surprising and concise. They must have less than fifteen words."
        },
        {
            "role": "user",
            "content": "Write me ten funny jokes"
        }
    ],
    stream=False,
)


# for chunk in stream:
#     if chunk.choices[0].delta.content is not None:
#         print(chunk.choices[0].delta.content, end="")

ten_jokes = stream.choices[0].message.content
print(ten_jokes)

while True:
    # Use with stream=False

    stream = client.chat.completions.create(
        model="solar-pro",
        messages=[
            {
                "role": "system",
                "content": "You are a funny clever person expert in evaluating how funny jokes are. You will be given jokes and asked to assess if they are really funny or not based on their innovativeness, conciseness, the theme they're about, how visual they are etc ... based on your conclusion, you will return the top funniest three ones in order without a small justification preceded by 'These are the three funniest jokes'. Then, you will also return the seven not so funny ones preceded by 'These are seven not so funny jokes.' Between the funny jokes and the not so funny jokes, you will add the separator '-----' five dashes."
            },
            {
                "role": "user",
                "content": f"{ten_jokes}"
            }
        ],
        stream=False,
    )

    three_jokes = stream.choices[0].message.content
    print(three_jokes)
    print('{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}')

    stream = client.chat.completions.create(
        model="solar-pro",
        messages=[
            {
                "role": "system",
                "content": "You will be given three funny jokes as a template, and seven not so funny ones and you will try to make ten even funnier jokes, funnier then the three first ones. They must have less than fifteen words "
            },
            {
                "role": "user",
                "content": f"{three_jokes}"
            }
        ],
        stream=False,
    )

    ten_jokes = stream.choices[0].message.content
    print(ten_jokes)
    print('{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}')

