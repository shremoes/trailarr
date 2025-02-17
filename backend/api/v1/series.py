import logging

from fastapi import APIRouter, HTTPException, status

from api.v1 import websockets
from api.v1.models import ErrorResponse
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.media import MediaRead, MediaUpdate
from core.files_handler import FilesHandler, FolderInfo
from core.tasks.download_trailers import download_trailer_by_id


series_router = APIRouter(prefix="/series", tags=["Series"])


@series_router.get("/all")
async def get_all_series() -> list[MediaRead]:
    db_handler = MediaDatabaseManager()
    all_series = db_handler.read_all(movies_only=False)
    return all_series


@series_router.get("/")
async def get_recent_series(limit: int = 30, offset: int = 0) -> list[MediaRead]:
    db_handler = MediaDatabaseManager()
    all_series = db_handler.read_recent(limit, offset, movies_only=False)
    return all_series


@series_router.get(
    "/{series_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Series Not Found",
        }
    },
)
async def get_series_by_id(series_id: int) -> MediaRead:
    db_handler = MediaDatabaseManager()
    try:
        series = db_handler.read(series_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return series


@series_router.get(
    "/{series_id}/files",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Series Not Found",
        }
    },
)
async def get_series_files(series_id: int) -> FolderInfo | str:
    db_handler = MediaDatabaseManager()
    try:
        series = db_handler.read(series_id)
        if not series.folder_path:
            return "Series has no folder path!"
        files_handler = FilesHandler()
        files = await files_handler.get_folder_files(series.folder_path)
        if not files:
            return "No files found in series folder!"
        return files
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@series_router.post(
    "/{series_id}/download",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Series Not Found",
        }
    },
)
async def download_series_trailer(series_id: int, yt_id: str = "") -> str:
    msg = f"Downloading trailer for series with ID: {series_id}"
    if yt_id:
        msg += f" from [{yt_id}]"
    logging.info(msg)
    return download_trailer_by_id(series_id, is_movie=False, yt_id=yt_id)


@series_router.post(
    "/{series_id}/monitor",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Series Not Found",
        }
    },
)
async def monitor_series(series_id: int, monitor: bool = True) -> str:
    logging.info(f"Updating monitor status for series with ID: {series_id}")
    db_handler = MediaDatabaseManager()
    try:
        series = db_handler.read(series_id)
        if series.trailer_exists and monitor:
            msg = f"Series '{series.title}' [{series.id}] already has a trailer!"
            await websockets.ws_manager.broadcast(msg, "Error")
            return msg
        series_update = MediaUpdate(monitor=monitor)
        db_handler.update(series_id, series_update)
        if monitor:
            msg = f"Series '{series.title}' [{series.id}] is now monitored"
        else:
            msg = f"Series '{series.title}' [{series.id}] is no longer monitored"
        logging.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success")
        return msg
    except Exception as e:
        await websockets.ws_manager.broadcast(
            "Failed to update monitor status!", "Error"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@series_router.delete(
    "/{series_id}/trailer",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Series Not Found",
        }
    },
)
async def delete_series_trailer(series_id: int) -> str:
    logging.info(f"Deleting trailer for series with ID: {series_id}")
    db_handler = MediaDatabaseManager()
    try:
        series = db_handler.read(series_id)
        if not series.trailer_exists:
            msg = f"Series '{series.title}' [{series.id}] has no trailer to delete!"
            await websockets.ws_manager.broadcast(msg, "Error")
            return msg
        if not series.folder_path:
            msg = f"Series '{series.title}' [{series.id}] has no folder path!"
            await websockets.ws_manager.broadcast(msg, "Error")
            return msg
        files_handler = FilesHandler()
        res = await files_handler.delete_trailer(series.folder_path)
        if not res:
            msg = f"Failed to delete trailer for series '{series.title}' [{series.id}]"
            await websockets.ws_manager.broadcast(msg, "Error")
            return msg
        series_update = MediaUpdate(trailer_exists=False)
        db_handler.update(series_id, series_update)
        msg = f"Trailer for series '{series.title}' [{series.id}] has been deleted."
        logging.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success")
        return msg
    except Exception as e:
        await websockets.ws_manager.broadcast("Failed to delete trailer!", "Error")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@series_router.get("/search/{query}")
async def search_series(query: str) -> list[MediaRead]:
    db_handler = MediaDatabaseManager()
    series = db_handler.search(query)
    return series
