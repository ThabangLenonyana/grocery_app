import json
from app.models import Product
from app import db


def seed_data():
    with open('products.json') as file:
        data = json.load(file)

    for item in data:
        product_name = item.get('product-name')
        price = item.get('price')
        store_name = item.get('store')
        validity_period = item.get('validity_period')
        offer_description = item.get('offer-description', '')

        # Check if price is None and set a default value if needed
        if price is None:
            price = "N/A"

        if product_name and price and store_name and validity_period:
            product = Product(
                product_name=product_name,
                price=price,
                store_name=store_name,
                validity_period=validity_period,
                offer_description=offer_description
            )
            db.session.add(product)
        else:
            print(f"Skipping item due to missing required fields: {item}")

    db.session.commit()
