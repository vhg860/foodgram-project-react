import csv
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загрузка данных из CSV-файлов"

    def handle(self, *args, **options):
        csv_file = os.path.join(os.getcwd(), 'data', 'ingredients.csv')
        if os.path.exists(csv_file):
            try:
                with open(csv_file, encoding='utf-8') as file:
                    reader = csv.reader(file)
                    next(reader)
                    ingredients_to_create = [
                        Ingredient(name=row[0], measurement_unit=row[1])
                        for row in reader
                    ]
                    Ingredient.objects.bulk_create(ingredients_to_create)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Успешно создано {len(ingredients_to_create)} "
                            "объектов Ingredient."
                        )
                    )
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Произошла ошибка: {str(e)}"
                ))
        else:
            self.stdout.write(
                self.style.ERROR(
                    "Файл не найден. Укажите правильный путь к файлу."
                )
            )
