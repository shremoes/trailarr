export interface Settings {
    api_key: string
    app_data_dir: string
    version: string
    server_start_time: string
    timezone: string
    debug: boolean
    monitor_enabled: boolean
    monitor_interval: number
    trailer_folder_movie: boolean
    trailer_folder_series: boolean
    trailer_resolution: number
    trailer_audio_format: string
    trailer_video_format: string
    trailer_subtitles_enabled: boolean
    trailer_subtitles_format: string
    trailer_subtitles_language: string
    trailer_file_format: string
    trailer_embed_metadata: boolean
    trailer_remove_sponsorblocks: boolean
    trailer_web_optimized: boolean
    wait_for_media: boolean
    yt_cookies_path: string
}

export interface ServerStats {
    trailers_downloaded: number
    movies_count: number
    movies_monitored: number
    series_count: number
    series_monitored: number
}