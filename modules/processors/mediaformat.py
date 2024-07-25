from enum import Enum


class MediaFormat(Enum):
    IMAGE = 0
    VIDEO = 1
    STREAM = 2


def parse_media_format(media_path: str) -> MediaFormat:
    ''' Determine whether a media source is an image, video or stream

    @param  media_path    Filepath or URL of media source

    @return MediaFormat value corresponding to the media source '''

    ext = media_path.split('.')[-1]

    if ext.lower() in ["jpg", "png"]:
        return MediaFormat.IMAGE
    elif ext.lower() in ["mp4"]:
        return MediaFormat.VIDEO
    elif media_path.startswith("rtsp://"):
        return MediaFormat.STREAM

    raise ValueError(f"Invalid Media: {media_path}")
