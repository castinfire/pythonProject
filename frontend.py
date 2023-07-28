# импорты


import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from tokens import community_token, access_token
from backend import VkTools

from database import *


class VKinder():

    def __init__(self, community_token, access_token):
        self.vk = vk_api.VkApi(token=community_token)
        self.longpoll = VkLongPoll(self.vk)

        self.vk_tools = VkTools(access_token)
        self.params = {}
        self.worksheets = []
        self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()
                        }
                       )

    def event_handler(self):
        longpoll = VkLongPoll(self.vk)
        engine = create_engine(db_url_object)

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:

                if event.text.lower() == 'привет':
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(event.user_id,
                                      f'здравствуйте, {self.params["name"]}. чтобы найти анкету, введите слово "ищи" ')
                elif event.text.lower() == 'ищи':
                    ''' здесь логика для поиска анкет'''

                    self.message_send(event.user_id, 'начинаю поиск')

                    if self.worksheets:
                        worksheet = self.worksheets.pop()
                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                    else:
                        self.worksheets = self.vk_tools.search_worksheet(
                            self.params, self.offset)
                        worksheet = self.worksheets.pop()

                        '''проверка анкеты в бд'''

                        while check_user(engine, event.user_id, worksheet['id']):
                            if self.worksheets:
                                worksheet = self.worksheets.pop()
                            else:
                                self.offset += 10
                                self.worksheets = self.vk_tools.search_worksheet(self.params, self.offset)
                                worksheet = self.worksheets.pop()

                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                        self.offset += 10

                    self.message_send(
                        event.user_id,
                        f'имя: {worksheet["name"]} ссылка: vk.com/id{worksheet["id"]}',
                        attachment=photo_string
                    )

                    add_user(engine, event.user_id, worksheet["id"])


                elif event.text.lower() == 'пока':
                    self.message_send(event.user_id, 'До новых встреч')

                else:
                    self.message_send(event.user_id, 'Неизвестная команда, чтобы начать диалог, напишите "привет"')


if __name__ == '__main__':
    bot = VKinder(community_token, access_token)
    bot.event_handler()




