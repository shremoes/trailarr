from core.base.connection_manager import (
    BaseConnectionManager,
    MediaUpdateDC,
)
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.helpers import MediaReadDC
from core.base.database.models.media import MediaCreate
from core.radarr.data_parser import parse_movie
from core.base.database.models.connection import ConnectionRead
from core.radarr.api_manager import RadarrManager


class RadarrConnectionManager(BaseConnectionManager):
    """Connection manager for working with the Radarr application."""

    connection_id: int

    def __init__(self, connection: ConnectionRead):
        """Initialize the RadarrConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        radarr_manager = RadarrManager(connection.url, connection.api_key)
        self.connection_id = connection.id
        super().__init__(
            connection,
            radarr_manager,
            parse_movie,
            inline_trailer=True,
        )

    def create_or_update_bulk(self, media_data: list[MediaCreate]) -> list[MediaReadDC]:
        """Create or update movies in the database and return MediaRead objects.\n
        Args:
            media_data (list[MovieCreate]): The movie data to create or update.\n
        Returns:
            list[MediaReadDC]: A list of MediaRead objects."""
        movie_read_list = MediaDatabaseManager().create_or_update_bulk(media_data)
        return [
            MediaReadDC(
                movie_read.id,
                created,
                movie_read.folder_path,
                movie_read.arr_monitored,
                movie_read.monitor,
            )
            for movie_read, created in movie_read_list
        ]

    def remove_deleted_media(self, media_ids: list[int]) -> None:
        """Remove the media from the database that are not present in the Radarr application. \n
        Args:
            media_ids (list[int]): List of media ids to remove."""
        MediaDatabaseManager().delete_except(self.connection_id, media_ids)
        return

    def update_media_status_bulk(self, media_update_list: list[MediaUpdateDC]):
        """Update the media status in the database. \n
        Args:
            media_status_list (list[tuple[int, bool, bool]]): List of tuples containing the \
                media id, monitor status, and trailer status."""
        MediaDatabaseManager().update_media_status_bulk(media_update_list)
        return
