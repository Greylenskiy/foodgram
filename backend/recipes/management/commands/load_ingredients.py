import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из data/ingredients.json'

    def handle(self, *args, **options):
        file_path = 'data/ingredients.json'

        with open(file_path, 'r', encoding='utf-8') as file:
            ingredients = json.load(file)

            for item in ingredients:
                Ingredient.objects.get_or_create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )

        self.stdout.write(self.style.SUCCESS('Ингредиенты успешно загружены'))
