from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os, uuid, config

def run_update():
    load_dotenv()
    MONGO_URI = os.getenv('MONGO_CONNECTION_STRING')
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = client.farmbot_db
    player_collection = db.players
    print("✅ Đã kết nối tới MongoDB.")

    all_players = list(player_collection.find({}))
    modified_count = 0

    for player_data in all_players:
        user_id = player_data['_id']
        animals = player_data.get('barn', {}).get('animals', {})
        needs_update = False
        
        for animal_id, data_list in animals.items():
            if data_list and isinstance(data_list[0], (float, int)):
                needs_update = True
                print(f"-> Tìm thấy dữ liệu animals cũ cho người chơi {user_id}. Đang chuyển đổi...")
                new_animal_list = []
                animal_info = config.ANIMALS.get(animal_id, {})
                for index, ready_time in enumerate(data_list):
                    new_animal_list.append({
                        "id": str(uuid.uuid4()),
                        "name": f"{animal_info.get('display_name', 'Vật nuôi')} #{index + 1}",
                        "ready_time": ready_time
                    })
                animals[animal_id] = new_animal_list
        
        if needs_update:
            player_collection.update_one(
                {'_id': user_id},
                {"$set": {"barn.animals": animals}}
            )
            modified_count += 1
            
    print(f"\n✅ Hoàn tất! Đã sửa đổi {modified_count} người chơi.")

if __name__ == "__main__":
    run_update()