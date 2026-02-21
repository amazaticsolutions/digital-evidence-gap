import os
import shutil
import subprocess
import tempfile
import time

import pytest

from multimedia_rag.ingestion import ingest_video
from multimedia_rag.ingestion import mongo_store


def _generate_test_video(path: str, duration: int = 3, size: str = "320x240", rate: int = 1):
    """Generate a short test video using ffmpeg testsrc."""
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc=duration={duration}:size={size}:rate={rate}",
        "-pix_fmt",
        "yuv420p",
        path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


@pytest.mark.e2e
def test_ingest_video_local_stub(monkeypatch):
    """End-to-end ingest: generate a video, stub Drive download, run ingest, verify DB documents."""
    tmpdir = tempfile.mkdtemp(prefix="de_gap_e2e_")
    try:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        _generate_test_video(video_path, duration=3, rate=1)

        # Stub the ingestion-level download/delete functions so the already-imported
        # names inside the ingestion package use our local file.
        import multimedia_rag.ingestion as ingestion_mod

        def _stub_download(gdrive_url: str) -> str:
            return video_path

        def _stub_delete(path: str) -> bool:
            try:
                if os.path.exists(path):
                    os.remove(path)
                return True
            except Exception:
                return False

        monkeypatch.setattr(ingestion_mod, "download_video_from_drive", _stub_download)
        monkeypatch.setattr(ingestion_mod, "delete_temp_video", _stub_delete)

        # Use a unique cam_id / gdrive_url to identify inserted docs
        cam_id = f"e2e_cam_{int(time.time())}"
        gdrive_url = f"e2e://local/{cam_id}"
        gps_lat, gps_lng = 12.34, 56.78

        # Run ingestion
        frames_processed = ingest_video(gdrive_url=gdrive_url, cam_id=cam_id, gps_lat=gps_lat, gps_lng=gps_lng, skip_existing=False)

        assert frames_processed > 0, "No frames were processed by ingest_video"

        # Verify documents in MongoDB
        embeddings_col = mongo_store.get_collection("frame_embeddings")
        metadata_col = mongo_store.get_collection("frame_metadata")

        # Query for documents matching cam_id and gdrive_url
        found_embeddings = list(embeddings_col.find({"cam_id": cam_id, "gdrive_url": gdrive_url}))
        found_metadata = list(metadata_col.find({"cam_id": cam_id, "gdrive_url": gdrive_url}))

        assert len(found_embeddings) == frames_processed
        assert len(found_metadata) == frames_processed

        # Cleanup created documents
        embeddings_col.delete_many({"cam_id": cam_id, "gdrive_url": gdrive_url})
        metadata_col.delete_many({"cam_id": cam_id, "gdrive_url": gdrive_url})

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
