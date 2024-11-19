import csv
import json
from django.core.management.base import BaseCommand
from myapp.models import Category, Product

category_csv_file = 'data/P_categories.csv'
product_csv_file = 'data/P_products.csv'


class Command(BaseCommand):
    help = 'Import Amazon data from CSV files into Django models'

    def handle(self, *args, **kwargs):
        self.import_categories()
        self.import_products()

    def import_categories(self):
        with open(category_csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                parent = None
                if row['parent_id']:
                    parent = Category.objects.get(id=row['parent_id'])

                category, created = Category.objects.get_or_create(
                    id=row['id'],
                    name=row['name'],
                    parent=parent
                )

                if created:
                    print(f"Created category: {category}")

    def import_products(self):
        with open(product_csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                category = Category.objects.get(id=row['category_id'])

                # Handle the description field
                description = row['description']

                # Check if the description contains commas (i.e., a list-like structure)
                if ',' in description:
                    # Split the description by commas
                    parsed_description = description.split(',')
                    # Join the list into a string with newlines or commas
                    description = "\n".join(parsed_description)
                else:
                    # If it's a plain string, use it as-is
                    description = description.strip()

                product, created = Product.objects.get_or_create(
                    ItemID=row['ItemID'],
                    category=category,
                    defaults={
                        'name': row['name'],
                        'description': description,  # Save the processed description
                        'price': row['price'],
                        'image': row['image'],
                        'AllImagesURLs': json.loads(row['AllImagesURLs']),
                        'ItemSpecifications': json.loads(row['ItemSpecifications']),
                    }
                )

                if created:
                    print(f"Created product: {product}")
