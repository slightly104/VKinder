from random import randrange
from vk_token import vk_token # токен группы
from access_token import access_token # токен пользователя
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from db import create_db, add_couple, check_exist # add_to_black_list, add_to_favorite



vk = vk_api.VkApi(token=vk_token)
vk_seeker = vk_api.VkApi(token=access_token)
longpoll = VkLongPoll(vk)

# Задаём количество пользователей для выдачи
count = 1000

fields_list = [
    "bdate",
    "sex",
    "city",
    "relation"
]
fields = ",".join(fields_list)

seeker_info = {
    "bdate": 0,
    "sex": 0,
    "city_id": 0,
    "city": 0,
    "relation": 0
}

couple_info = {
    "first_name": 0,
    "last_name": 0,
    "id": 0
}

couple_info_list = list()

men_sex_spellings = [
    "2", "мужской", "парень", "мужик", "муж", "м", "мужчинка", "мачо", "молодой человек", 
    "дядька", "мужчина", "мэн", "дядя", "мистер", "сильный пол", "man", "m", "male"
    ]
woman_sex_spellings = [
    "1", "женский", "женщина", "девушка", "девочка", "леди", "богиня", "королева", "принцесса", 
    "дама", "царица", "гражданка", "дева", "мадам", "дамочка", "мисс", "миссис", 
    "сударыня", "прекрасный пол", "нежный пол", "слабый пол", "миледи", "woman", 
    "girl", "female", "lady", "w", "f"
    ]

relation_list = [str(x) for x in range(9)]



def listen_answer():
    """Слушаем ответ от пользователя"""

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                text = event.text.lower()
                
                return text



def write_msg(user_id, message):
    """Ответ бота"""
    vk.method("messages.send", {"user_id": user_id, "message": message,  "random_id": randrange(10 ** 7),})



def start_info(fields):
    """Ищем информацию о пользователе
     для которого будем искать пару"""
    
    seeker = listen_answer()
    res = vk.method("users.get", {"user_ids": seeker, "fields": fields,})
    if not res:
        write_msg(event.user_id, "Человека с таким id не существует, попробуйте ещё раз")
        return start_info(fields)
    
    return res



def find_city_id():
    """Находим id города по его названию. Повторно спрашиваем пользователя при неправильном вводе"""
    city = listen_answer()
    res = vk_seeker.method("database.getCities", {"q": city,})
    if res["count"] == 0:
        write_msg(
            event.user_id, 
            "Похоже такого города ВК не знает, попробуйте ещё раз или введите соседний город"
            )
        res = find_city_id()

    return res



def check_bdate():
    """Проверяем корректность даты рождения. Если неправильный, возвращаем к вводу даты"""
    date = listen_answer()
    try:
        date = int(date)
    except ValueError:
        write_msg(event.user_id, "Введите полный год рождения в формате ГГГГ")
        date = check_bdate()
    
    if date not in range(1900, 2023):
        write_msg(event.user_id, "Введите адекватный (1900-2022) год рождения в формате ГГГГ")
        date = check_bdate()

    return date 



def check_sex():
    """Проверяем корректность пола. Если неправильный, возвращаем к вводу пола"""
    sex = listen_answer()
    if sex in woman_sex_spellings:
        sex = "1"
    elif sex in men_sex_spellings:
        sex = "2"
    else:
        write_msg(event.user_id, """Введите пол
                1 - женский
                2 - мужской""")
        sex = check_sex()
    
    return sex



def check_relation():
    """Проверяем корректность семейного положения. 
    Если неправильный, возвращаем к вводу семейного положения"""

    relation = listen_answer()
    if relation in relation_list:
        return relation
        
    write_msg(event.user_id, "Введите цифру от 0 до 8 включительно, в соответствии с указанными выше")
    relation = check_relation()

    return relation



def check_info(fields_list, info):
    """Проверяем информацию на полноту, и если чего-то не хватает
    отправляем сообщение, что нужно дополнить в словаре seeker_info"""

    for elem in fields_list:
        if elem in info[0].keys():
            if elem == "bdate":
                
                if len(info[0]["bdate"].split(".")) < 3:
                    write_msg(event.user_id, "Не хватает информации!")
                    write_msg(event.user_id, "Введите полный год рождения (например: 1990)")
                    seeker_info["bdate"] = check_bdate()
                else:
                    seeker_info["bdate"] = info[0]["bdate"].split(".")[2]

            elif elem == "sex":
                seeker_info["sex"] = info[0].get("sex")

            elif elem == "city":
                seeker_info["city_id"] = info[0].get("city").get("id")
                seeker_info["city"] = info[0].get("city").get("title")

            elif elem == "relation":
                seeker_info["relation"] = info[0].get("relation")

        else:
            write_msg(event.user_id, "Не хватает информации!")
            if elem == "bdate":
                write_msg(event.user_id, "Введите полный год рождения (например: 1977)")
                seeker_info["bdate"] = check_bdate()
            
            elif elem == "sex":
                write_msg(event.user_id, """Введите пол
                1 - женский
                2 - мужской""")
                seeker_info["sex"] = check_sex()                

            elif elem == "city":
                write_msg(event.user_id, "Введите город")
                city_info = find_city_id()
                seeker_info["city"] = city_info["items"][0]["title"]
                seeker_info["city_id"] = city_info["items"][0]["id"]

            elif elem == "relation":
                write_msg(event.user_id, """Введите cемейное положение
                1 — не женат/не замужем
                2 — есть друг/есть подруга
                3 — помолвлен/помолвлена
                4 — женат/замужем
                5 — всё сложно
                6 — в активном поиске
                7 — влюблён/влюблена
                8 — в гражданском браке
                0 — не указано""")
                seeker_info["relation"] = check_relation()
                        
    return seeker_info
            


def find_couple(bdate, sex, city_id, relation, count):
    """Находим подходящих людей"""

    if int(sex) == 1:
        sex = 2
    else:
        sex = 1
    res = vk_seeker.method("users.search", {"fields": fields, "city": city_id, "sex": sex, 
                    "count": count, "status": relation, "birth_year": bdate, "has_photo": 1})

    for elem in res["items"]:
        couple_info_temp = {
            "first_name": 0,
            "last_name": 0,
            "id": 0
        }
        couple_info_temp["first_name"] = elem["first_name"]
        couple_info_temp["last_name"] = elem["last_name"]
        couple_info_temp["id"] = elem["id"]
        couple_info_list.append(couple_info_temp)
        
    return couple_info_list



def show_couple(couple_info):
    """Собираем пользователю информацию о подходящей паре"""
    show_str = f"{couple_info['first_name']} {couple_info['last_name']}\nhttps://vk.com/id{couple_info['id']}"
    
    return show_str



def get_photos(couple_id):
    """Получает информацию о фотографиях пары, считает количество лайков и комментов, 
        возвращает строки с url фото"""

    # Исключаем падение бота от парсинга закрытого профиля ВК 
    try:
        photos_info = vk_seeker.method("photos.get", {"owner_id": couple_id, "album_id": "profile", "rev": 1, "extended": 1})
    except vk_api.exceptions.ApiError:
        return "closed profile" # У этого человека закрытый профиль

    photos_amount = photos_info["count"]
    photos_info_dict = dict()
    photo_urls_list = list()

    if photos_amount < 3:
        return "low_anount" # У этого человека кол-во фото меньше 3
    elif photos_amount > 50:
        photos_amount = 50

    for i in range(photos_amount):
        photos_info_dict[photos_info["items"][i]["id"]] = photos_info["items"][i]["likes"]["count"] + photos_info["items"][i]["comments"]["count"]

    sorted_photos_dict = dict(sorted(photos_info_dict.items(), key=lambda x: -x[1]))
    photos_ids = list(sorted_photos_dict.keys())

    for i in range(3):
        photo_id = photos_ids[i]
        photo_url = f'https://vk.com/id{couple_id}?z=photo{couple_id}_{photo_id}%2Falbum{couple_id}_0%2Frev'
        photo_urls_list.append(photo_url)
        photo_urls_str = "\n".join(photo_urls_list)

    return photo_urls_str



def searching_for_user():
    """Отправляет напоминание, что может сделать юзер во время поиска пары"""
    return "Если у вас нет слов, то, наверное, стоит связаться с последним человеком) Иначе напишите 'дальше' или 'стоп'"



def next_or_stop():
    """Заканчивает или продолжает поиск"""
    user_answer = listen_answer()
    if user_answer == "дальше":
        return "next"
    elif user_answer == "стоп":
        return "stop"

    write_msg(event.user_id, f"{searching_for_user()}")
    user_answer = next_or_stop()

    return user_answer



for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:

        if event.to_me:
            request = event.text.lower()
                
            if request == "привет":
                # Инициализируем разговор с ботом и создаём базу данных
                write_msg(event.user_id, f"Хай, {event.user_id}")
                write_msg(event.user_id, """Вот мои команды:
                Найди пару - начать поиск пары
                Пока - завершить работу 
                """)
                # Cоздаём БД
                create_db()

            elif request == "пока":
                # Прощаемся с ботом и завершаем его работу
                # Для возобновления работы необходимо повторно запустить скрипт
                write_msg(event.user_id, "Пока((")
                quit()

            elif request == "найди пару":
                # Обнуляем предыдущий поиск (выданные ранее пользователи сохранены в БД)
                couple_info_list = list()

                # Собираем информацию от пользователя
                write_msg(event.user_id, "Для кого? Введи id пользователя")
                resp = start_info(fields)

                # Проверяем чего не хватает
                check_info(fields_list, resp)
                write_msg(event.user_id, "Информации достаточно")

                # Ищем пользователю подходящих людей предоставленной информации
                find_couple(seeker_info["bdate"], seeker_info["sex"], seeker_info["city_id"], seeker_info["relation"], count)

                for elem in couple_info_list:
                    # Проверяем есть ли эта пара в БД. Если есть - пропускаем, если нет - добавляем в БД
                    if check_exist(elem.get("id")) == True:
                        write_msg(event.user_id, "Этого человека уже смотрели... Ищем дальше...")
                        continue
                    else:
                        add_couple(elem.get("id"))

                    # Выдаём результат
                    show_str = show_couple(elem)
                    write_msg(event.user_id, f"{show_str}")
                    res_get_photos = get_photos(elem.get('id'))
                    if res_get_photos == "closed profile":
                        write_msg(event.user_id, 
                        "У этого человека закрытый профиль, но он подходит. Может быть захотите связаться с ним?..")
                        continue
                    elif res_get_photos == "low_anount":
                        write_msg(event.user_id, 
                        "У этого человека недостаточно фотографий профиля для оценки, но вы можете перейти на страничку")
                        continue
                    else:
                        write_msg(event.user_id, f"{res_get_photos}")

                    # Спрашиваем выдавать ли ещё результаты
                    write_msg(event.user_id, "Если хотите увидеть следующего человека, напишите: дальше")
                    write_msg(event.user_id, "Если хотите на этом закончить, напишите: стоп")
                    next_stop = next_or_stop()
                    if next_stop == "next":
                        continue
                    elif next_stop == "stop":
                        break
                
                # После окончания, либо прерывания подбора, явно сообщаем пользователю об этом
                write_msg(event.user_id, "На этом пока что всё. Возвращайтесь обязательно!")    


            else:
                write_msg(event.user_id, "Не поняла вашего ответа...")
                write_msg(event.user_id, """Вот мои команды:
                Найди пару - начать поиск пары
                Пока - завершить работу 
                """)

