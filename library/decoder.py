import base64
from io import BytesIO

from PIL import Image


def data_url_to_image(data_url: str) -> Image.Image:
    """
    Decode a Base64 data URL into a PIL Image.

    Args:
        data_url: Image data URL such as:
            data:image/jpeg;base64,/9j/4AAQ...

    Returns:
        PIL.Image.Image: Decoded image object.

    Raises:
        ValueError: If the data URL is invalid.
        ValueError: If the Base64 data cannot be decoded.
        PIL.UnidentifiedImageError: If the decoded data is not an image.
    """

    if not isinstance(data_url, str):
        raise TypeError("data_url must be a string")

    if "," not in data_url:
        raise ValueError("Invalid data URL: missing comma")

    header, encoded = data_url.split(",", 1)

    if not header.startswith("data:image/"):
        raise ValueError(f"Unsupported data URL: {header}")

    try:
        image_data = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("Invalid Base64 image data") from exc

    try:
        image = Image.open(BytesIO(image_data))
        image.load()
    except Exception:
        raise

    return image