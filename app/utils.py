from difflib import get_close_matches


def find_similar_products(product_name, products):
    product_names = [product.product_name for product in products]
    similar_names = get_close_matches(
        product_name, product_names, n=5, cutoff=0.5)
    return [product for product in products if product.product_name in similar_names]
