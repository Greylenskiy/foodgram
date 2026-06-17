import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из data/ingredients.json'

    def handle(self, *args, **options):
        project_root = os.path.dirname(settings.BASE_DIR)
        file_path = os.path.join(project_root, 'data', 'ingredients.json')

        self.stdout.write(f'Ищу файл: {file_path}')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as file:
            ingredients = json.load(file)

            for item in ingredients:
                Ingredient.objects.get_or_create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )

        self.stdout.write(self.style.SUCCESS(
            f'Загружено {len(ingredients)} ингредиентов'))
