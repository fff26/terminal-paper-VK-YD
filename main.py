import requests
import os
from dotenv import load_dotenv
import time
import json
from tqdm import tqdm


load_dotenv()

class CopyPhotoVK:
    base_url = 'https://api.vk.com/method/'

    def __init__(self, token_ya, api_token_vk, user_id, count=5):
        self.params = {
            'album_id': 'profile', 
            'rev': 0, 
            'extended': 'likes', 
            'photo_sizes': 1, 
            'type': 'z', 
            'access_token': api_token_vk, 
            'v': '5.131'
        }
        self.token_ya = token_ya
        self.user_id = user_id
        self.count = count

    def get_photo_data(self):
        """
        Метод получает данные о изображениях пользователя ВК
        """
        method = 'photos.get'
        url = f'{self.base_url}{method}'
        params = {'owner_id': self.user_id, 'count': self.count}
        params.update(self.params)
        response = requests.get(url, params=params)
        data = response.json()
        if 'response' not in data:
            print(f'Ошибка получения данных: {data.get("error", {}).get("error_msg", "неизвестная ошибка")}')
            return None
        return data

    def data_assembly(self):
        """
        Метод формирует имена файлов и список данных изображений
        """
        data = self.get_photo_data()

        list_url_photos, list_likes = [], []
        list_dates, list_sizes = [], []

        for info in data['response']['items']:
            list_url_photos.append(info['sizes'][-1]['url'])
            list_likes.append(info['likes']['count'])
            list_dates.append(info['date'])
            list_sizes.append(info['sizes'][-1]['type'])
        for i in range(len(list_likes)):
            if list_likes.count(list_likes[i]) > 1:
                index = list_likes.index(list_likes[i], i+1)
                list_likes[i] = str(list_likes[i]) + '_' + str(list_dates[index])
        lists_dates = {'url_photos': list_url_photos, 'likes': list_likes, 'dates': list_dates, 'sizes': list_sizes}
        return lists_dates

    def file_json_record(self):
        """
        Метод формирует и записывает на ПК json-файл с информацией
        (имя и размер файла) о полученных изображениях
        """
        data = self.data_assembly()
        likes = data['likes']
        sizes = data['sizes']

        json_dict = {'image': {}}
        for i in range(len(likes)):
            json_dict['image'][likes[i]] = sizes[i]

        with open('photos_info.json', 'w') as f:
            json.dump(json_dict, f)

        self.upload_photos_to_yandex_disk(likes)

    def upload_photos_to_yandex_disk(self, likes):
        """
        Метод создаёт папку изагружает изображения на Яндекс.Диск
        """
        headers = {'Authorization': f'OAuth {token_ya}'}
        create_folder_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        params = {'path': '/VK_photos'}

        response = requests.put(create_folder_url, headers=headers, params=params)
        if response.status_code == 201:
            print('Папка успешно создана')
        else:
            print(f'Ошибка {response.status_code}: {response.json()["message"]}')

        for url_photo in tqdm(self.data_assembly()['url_photos'], desc='Загрузка изображений на Яндекс.Диск'):
            url_index = self.data_assembly()['url_photos'].index(url_photo)
            response = requests.post(upload_url, headers=headers, params={'path': f'/VK_photos/{likes[url_index]}.jpg', 'url': url_photo})
            if response.status_code == 202:
                time.sleep(0.34)
            else:
                print(f'Ошибка загрузки изображения {likes[self.data_assembly()["url_photos"].index(url_photo)]}.jpg на Яндекс.Диск: {response.text}')

if __name__ == '__main__':
    token_ya = input('Введите токен Яндекс с Полигон: ')
    user_id = input('Введите id пользователя ВК: ')
    count = int(input('Введите количество фотографий для загрузки: '))
    vk_token = os.getenv('TOKEN_API_VK')

    vk = CopyPhotoVK(token_ya, vk_token, user_id, count)
    vk.file_json_record()