import json
import base64
import re
import logging
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


def process_uploaded_images(request, product, product_image_model):
    """
    Process images from JavaScript upload system.

    Args:
        request: The HTTP request object
        product: The Product instance to attach images to
        product_image_model: The ProductImage model class
    """
    image_data_fields = [key for key in request.POST.keys() if key.startswith('image_data_')]

    print(f"DEBUG: Processing images for product {product.name}")
    print(f"DEBUG: Found {len(image_data_fields)} image fields: {image_data_fields}")
    print(f"DEBUG: All POST keys: {list(request.POST.keys())}")
    logger.info(f"Processing images for product {product.name}")
    logger.info(f"Found {len(image_data_fields)} image fields: {image_data_fields}")

    for field_name in image_data_fields:
        try:
            image_data_json = request.POST.get(field_name)

            if image_data_json:
                image_data = json.loads(image_data_json)

                image_src = image_data.get('src', '')
                if image_src.startswith('data:image'):
                    format_part, imgstr = image_src.split(';base64,')
                    ext = format_part.split('/')[-1]

                    img_data = base64.b64decode(imgstr)

                    original_name = image_data.get('name', 'uploaded_image.jpg')
                    safe_name = re.sub(r'[<>:"/\\|?*]', '_', original_name)
                    file_name = f"{product.slug}_{safe_name}"

                    img_file = ContentFile(img_data, name=file_name)

                    product_image = product_image_model(
                        product=product,
                        image=img_file,
                        alt_text=f"{product.name} image",
                        is_main=image_data.get('isMain', False)
                    )
                    product_image.save()
                    print(f"DEBUG: Successfully saved image: {file_name}")
                    logger.info(f"Successfully saved image: {file_name}")

        except Exception as e:
            print(f"DEBUG ERROR: Error processing {field_name}: {str(e)}")
            logger.error(f"Error processing {field_name}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            logger.error(traceback.format_exc())
            continue


def is_admin_user(user):
    """Check if user is staff or superuser"""
    return user.is_staff or user.is_superuser
