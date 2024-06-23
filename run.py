from app import create_app, db
from app.models import Product
import json

app = create_app()


@app.before_first_request
def load_data():
    db.create_all()
    with open('products.json') as file:
        products = json.load(file)
        for product in products:
            db.session.add(Product(
                product_name=product['product-name'],
                price=product['price'],
                store=product['store'],
                offer_description=product['offer-description'],
                validity_period=product['validity_period']
            ))
        db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
