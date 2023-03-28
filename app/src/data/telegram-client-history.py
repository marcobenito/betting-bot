from telethon.sync import TelegramClient
import re
import pickle

api_id = 16387020
api_hash = "6e2c750ba8c04e340f656681216d7398"
user_input_channel = "https://t.me/test_mbk"
user_input_channel = "https://t.me/joinchat/AAAAAFAI2Pbhi_a3dc3dKw"
# user_input_channel = "me"
filter = "STAKE"
name = "marcobenito"
client = TelegramClient('marcobenito', api_id, api_hash)
client.start()
# with open('bet-history-images/text.pickle', 'rb') as handle:
#     b = pickle.load(handle)
# print("---------------------------")
# print(b)
# print("-----------------------------")

text = []
async def main():
    i = 0
    async for message in client.iter_messages(user_input_channel, limit=10000):
        # filtered = re.findall(filter, message)
        try:
            if filter in message.message and message.media is not None:
                i += 1
                print(message.date)
                text.append({"id": str(i), "text": message.message, "date": message.date})
                # text["img" + str(i)] = message.message
                await message.download_media("bet-history-images/img" + str(i) + ".jpg")

        except TypeError:
            pass


with client:
    client.loop.run_until_complete(main())

with open("bet-history-images/text.pickle", "wb") as f:
    pickle.dump(text, f)
# with TelegramClient(name, api_id, api_hash) as client:
#     for message in client.iter_messages(chat):
#         print(message.sender_id, ':', message.text)