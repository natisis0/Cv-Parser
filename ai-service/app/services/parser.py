from app.services.extractors.factory import get_extractor


def parse_resume(file_path: str):

    extractor = get_extractor(file_path)

    text = extractor.extract(file_path)

    return text