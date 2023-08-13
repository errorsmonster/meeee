from pyrogram import Client, filters
from info import CHANNELS
from database.ia_filterdb import save_file
import pymongo
from info import DATABASE_NAME, COLLECTION_NAME, DATABASE_URI, ADMINS
media_filter = filters.document | filters.video | filters.audio
myclient = pymongo.MongoClient(DATABASE_URI)
db = myclient[DATABASE_NAME]
col = db[COLLECTION_NAME]

@Client.on_message(filters.command("savefile") & filters.user(ADMINS))
async def start(client, message):
    try:
        for file_type in ("document", "video", "audio"):
            media = getattr(message.reply_to_message, file_type, None)
            if media is not None:
                break
        else:
            return

        media.file_type = file_type
        media.caption = message.reply_to_message.caption
        await save_file(media)
        await message.reply_text("Saved In DB")
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")
@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    """Media Handler"""
    for file_type in ("document", "video", "audio"):
        media = getattr(message, file_type, None)
        if media is not None:
            break
    else:
        return

    media.file_type = file_type
    media.caption = message.caption
    await save_file(media)


@Client.on_message(filters.command("sendkey") & filters.user(ADMINS))
async def send_messages_with_keyword(app, msg):
    try:
        keywords = msg.command[1].split("-")
    except IndexError:
        await msg.reply_text("Please provide keyword(s) to search for in the file names.")
        return
    regex_pattern = "|".join(keywords)
    documents = col.find({"file_name": {"$regex": '|'.join(keywords)}})
    
    id_list = [
        {
            'id': document['_id'],
            'file_name': document.get('file_name', 'N/A'),
            'file_caption': document.get('caption', 'N/A'),
            'file_size': document.get('file_size', 0)
        } 
        for document in documents
    ]
    
    for j, i in enumerate(id_list):
        try:
            try:
                await app.send_video(
                    msg.chat.id,
                    i['id'],
                    caption=CUSTOM_FILE_CAPTION.format(
                        file_name=i['file_name'],
                        file_caption=i['file_caption'],
                        file_size=get_size(int(i['file_size']))
                    )
                )
            except Exception as e:
                print(e)
                await app.send_document(
                    msg.chat.id,
                    i['id'],
                    caption=CUSTOM_FILE_CAPTION.format(
                        file_name=i['file_name'],
                        file_caption=i['file_caption'],
                        file_size=get_size(int(i['file_size']))
                    )
                )
            
            await asyncio.sleep(random.randint(3,6))
        except FloodWait as e:
            print(f"Sleeping for {e.x} seconds.")
            await asyncio.sleep(e.x)
        except Exception as e:
            print(e)
            #await jj.delete()
            await msg.reply_text("An error occurred while sending messages.")
            break
    
    await msg.reply_text("Completed")
