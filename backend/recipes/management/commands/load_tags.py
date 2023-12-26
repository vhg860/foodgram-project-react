import json
import os

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Загрузить данные из файла JSON в модель Tag'

    def handle(self, *args, **options):
        file_path = os.path.abspath('data/tags.json')
        try:
            with open(file_path, encoding='utf-8') as data_file:
                tags_data = json.load(data_file)
                tags_to_create = [Tag(**data) for data in tags_data]
                Tag.objects.bulk_create(tags_to_create)
                self.stdout.write(self.style.SUCCESS(
                    'Теги успешно загружены!'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Файл не найден!'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(
                'Ошибка декодирования файла JSON!'))
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка целостности данных: {str(e)}'))
