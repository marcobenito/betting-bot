from app.src.project.betting import Betting
from app.src.project.pick_info import PickInfo
from app.src.project.OCR import ImageText
import json
from PIL import Image
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from app.src.utils.utils import generate_text
from decouple import config
from datetime import datetime

# Read inputs file
with open("app/input.json", "rb") as f:
    inputs = json.load(f)

# Read environment variables
inputs["bet"]["username"] = config("PS3838_USERNAME")
inputs["bet"]["password"] = config("PS3838_PASSWORD")
inputs["telegram"]["username"] = config("TELEGRAM_USERNAME")
inputs["telegram"]["api_id"] = int(config("TELEGRAM_API_ID"))
inputs["telegram"]["api_hash"] = config("TELEGRAM_API_HASH")
inputs["telegram"]["session_token"] = config("TELEGRAM_SESSION_TOKEN")
inputs["telegram"]["input_channel"] = int(config("TELEGRAM_INPUT_CHANNEL"))
inputs["telegram"]["manual_channel"] = int(config("TELEGRAM_MANUAL_INPUT_CHANNEL"))
inputs["telegram"]["output_channel"] = int(config("TELEGRAM_OUTPUT_CHANNEL"))

# Define telegram client
client = TelegramClient(StringSession(inputs["telegram"]["session_token"]),
                        inputs["telegram"]["api_id"],
                        inputs["telegram"]["api_hash"])

# Path for storing the downloaded image (in the /tmp/ folder of the AWS ECS instance)
img_path = "/tmp/img.jpg"
# Authentication variable for connecting to the PS3838 API
bet_auth = (inputs["bet"]["username"], inputs["bet"]["password"])


async def main(pick):
    """Main function which will be executed every time a new or an edited message arrives matching the
    filter criterion (see functions new_message_listener and edited_message_listener.
    The workflow of the function is as follows:
        1. Check if the message contains an image, and download it
        2. Use OCR to extract the text from the image and check if it is a bet (steps 1 and 2 done in function
            check_message)
        3. Extract the relevant information from the pick, combining the image text and the message text
        4. Use the PS3838 API to convert the pick info into relevant information for placing the bet
        5. Place the bet
        6. Send message to another telegram channel with the info of the bet, or the logs if it went wrong

    :param pick: dictionary containing the pick text (image + description)"""

    output_message = ""
    output_message_repeated_bet = ""

    # Step 3: Create a pick object for generating all the relevant information from the pick
    my_pick = PickInfo(pick, bet_auth)
    my_pick.extract_from_description()
    my_pick.extract_from_image_text(inputs["bet"]["tipster_stake_1"])
    my_pick.select_bet()
    my_pick.map_tournament()
    my_pick.map_bet()
    print("Pick info: ", my_pick.info)

    # Step 4: Create a betting object and generate all the necessary information for placing the bet
    my_bet = Betting(config=inputs["bet"], params=my_pick.info)
    if my_pick.error == "":
        my_bet.set_fixtures()
        my_bet.odds()
        my_bet.set_line()
        my_bet.set_betting_units()

        # Step 5: Place bet using the generated parameters
        # First, check if the last bet is the same we are trying to place, in order not to repeat it
        # last_placed_bet = my_bet.get_last_placed_bet()

        # my_bet.place_bet()

        # if last_placed_bet["eventId"] != my_bet.bet_info["event_id"]:
        #     my_bet.place_bet()
        # else:
        #     output_message_repeated_bet += "You are trying to repeat the bet"

    # Step 6: Send message to the output channel with the status of the placed bet
    print(my_bet.bet_info)

    if "placed_bet" in my_bet.bet_info.keys():
        output_message += "**The bet has been placed successfully: ** \n"
        output_message += generate_text(my_bet.bet_info["placed_bet"])
    else:
        output_message += "**The bet could not be placed correctly: ** \n" + generate_text(my_pick.info)
        if my_bet.warning != "":
            output_message += "\n**WARNINGS: **\n" + my_bet.warning
        if my_bet.error != "":
            output_message += "\n**ERRORS: ** \n" + my_bet.error
        if my_pick.error != "":
            output_message += "\n**ERRORS: ** \n" + my_pick.error

    output_message += output_message_repeated_bet
    print("Output: ", output_message)
    # entity = await client.get_entity(inputs["telegram"]["output_channel"])
    # await client.send_message(entity=entity, message=output_message)


async def check_message(event):
    """Check if the message received should be considered as a bet or not
    :param event: the message received from the telegram channel
    :return text: dictionary containing the image text and the description"""
    new_message = event.message.message
    message = event.message

    # if message is not None and message.media is not None:
    if event.photo is not None:
        # Step 1: If the message contains an image, download it
        await message.download_media(img_path)
        # Step 2: Extract the text from the downloaded image using OCR
        image = Image.open(img_path)
        obj = ImageText(image, new_message)  # Create object
        obj.preprocess_image()  # Call pre-processing image method
        obj.image_to_text()  # Extract text from the image through OCR
        text = obj.text

        # "Sencillas" is the keyword for detecting our bets
        # If "Cerrar apuesta" is in the image, it will mean the tipster is showing a running bet, and we donẗ want to
        # place the bet twice. Also, "Crear apuesta" means it is a parlay bet, which is still not implemented
        if "sencillas" in text["image_text"] and "cerrar apuesta" not in text["image_text"] and \
                "crear apuesta" not in text["image_text"]:
            return text
        else:
            return None


@client.on(events.NewMessage(chats=[inputs["telegram"]["input_channel"], inputs["telegram"]["manual_channel"]]))
async def new_message_listener(event):
    """Event listener for new messages. Whenever a new message arrives, matching the filtering
        criterion, call the main function"""
    print("new message at: ", datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    check = await check_message(event)
    if check is not None:
        await main(check)


def run_app():
    client.start()
    client.run_until_disconnected()
