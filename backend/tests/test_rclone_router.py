"""Tests for src/kortana/routers/rclone.py - Rclone file synchronization endpoints"""
from unittest.mock import MagicMock, patch

import pytest
from tests.conftest import SyncTestClient


@pytest.fixture
def client():
    """Create a test client for FastAPI app"""
    from src.kortana.main import app

    return SyncTestClient(app)


class TestListRemotes:
    def test_list_remotes_success(self, client):
        """Test successful listing of rclone remotes"""
        with patch("src.kortana.routers.rclone.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "google_drive:\nonedrive:\ns3remote:\n"
            mock_run.return_value = mock_result

            response = client.get("/api/rclone/list")

            assert response.status_code == 200
            data = response.json()
            assert "remotes" in data
            assert len(data["remotes"]) == 3

    def test_list_remotes_empty(self, client):
        """Test listing remotes when none are configured"""
        with patch("src.kortana.routers.rclone.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            response = client.get("/api/rclone/list")

            assert response.status_code == 200
            data = response.json()
            assert data["remotes"] == []

    def test_list_remotes_rclone_not_found(self, client):
        """Test handling when rclone is not installed"""
        with patch("src.kortana.routers.rclone.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("rclone not found")

            response = client.get("/api/rclone/list")

            assert response.status_code == 200
            data = response.json()
            assert data["remotes"] == []
            assert "warning" in data

    def test_list_remotes_subprocess_error(self, client):
        """Test handling of subprocess errors"""
        with patch("src.kortana.routers.rclone.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Permission denied")

            response = client.get("/api/rclone/list")

            assert response.status_code == 500


class TestListFiles:
    def test_list_files_success(self, client):
        """Test successful file listing on remote"""
        with patch("src.kortana.routers.rclone.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "file1.txt\nfile2.txt\nfolder/\n"
            mock_run.return_value = mock_result

            response = client.get("/api/rclone/files/google_drive")

            assert response.status_code == 200
            data = response.json()
            assert "files" in data
            assert len(data["files"]) == 3

    def test_list_files_with_path(self, client):
        """Test listing files with specific path"""
        with patch("src.kortana.routers.rclone.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "document1.docx\ndocument2.docx\n"
            mock_run.return_value = mock_result

            response = client.get("/api/rclone/files/google_drive?path=/Documents")

            assert response.status_code == 200
            # Verify the correct path was used
            call_args = mock_run.call_args[0]
            assert "/Documents" in call_args[0][2]

    def test_list_files_remote_without_colon(self, client):
        """Test that remote name gets colon appended if missing"""
        with patch("src.kortana.routers.rclone.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "file.txt\n"
            mock_run.return_value = mock_result

            response = client.get("/api/rclone/files/s3")

            assert response.status_code == 200
            # Verify colon was appended
            call_args = mock_run.call_args[0]
            assert "s3:" in call_args[0][2]

    def test_list_files_empty_remote(self, client):
        """Test listing empty remote"""
        with patch("src.kortana.routers.rclone.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            response = client.get("/api/rclone/files/empty_remote")

            assert response.status_code == 200
            data = response.json()
            assert data["files"] == []

    def test_list_files_subprocess_error(self, client):
        """Test error handling during file listing"""
        with patch("src.kortana.routers.rclone.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Remote not found")

            response = client.get("/api/rclone/files/nonexistent")

            assert response.status_code == 500

    def test_list_files_remote_with_existing_colon(self, client):
        """Test that remote names with colon aren't duplicated"""
        with patch("src.kortana.routers.rclone.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "file.txt\n"
            mock_run.return_value = mock_result

            response = client.get("/api/rclone/files/google_drive:")

            assert response.status_code == 200
            # Verify colon wasn't duplicated
            call_args = mock_run.call_args[0]
            assert "google_drive::" not in call_args[0][2]


class TestCopyFile:
    def test_copy_file_success(self, client):
        """Test successful file copy initiation"""
        with patch("src.kortana.routers.rclone.subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            response = client.post(
                "/api/rclone/copy?source=google_drive:/Documents/file.txt&destination=s3:/backup/"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "started"
            assert data["source"] == "google_drive:/Documents/file.txt"
            assert data["destination"] == "s3:/backup/"
            assert mock_popen.called

    def test_copy_file_with_folder(self, client):
        """Test copying entire folder"""
        with patch("src.kortana.routers.rclone.subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            response = client.post(
                "/api/rclone/copy?source=google_drive:/Projects&destination=onedrive:/Archive/"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "started"

    def test_copy_file_subprocess_error(self, client):
        """Test error during copy initiation"""
        with patch("src.kortana.routers.rclone.subprocess.Popen") as mock_popen:
            mock_popen.side_effect = Exception("Failed to start process")

            response = client.post("/api/rclone/copy?source=source:&destination=dest:")

            assert response.status_code == 500

    def test_copy_file_verifies_progress_flag(self, client):
        """Test that --progress flag is included in copy command"""
        with patch("src.kortana.routers.rclone.subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            response = client.post(
                "/api/rclone/copy?source=google_drive:/file.txt&destination=s3:/file.txt"
            )

            assert response.status_code == 200
            # Verify --progress was included in command
            call_args = mock_popen.call_args[0]
            assert "--progress" in call_args[0]

    def test_copy_file_missing_source(self, client):
        """Test validation for missing source"""
        response = client.post("/api/rclone/copy?destination=s3:/backup/")

        # FastAPI validation should return 422
        assert response.status_code == 422

    def test_copy_file_missing_destination(self, client):
        """Test validation for missing destination"""
        response = client.post("/api/rclone/copy?source=google_drive:/file.txt")

        # FastAPI validation should return 422
        assert response.status_code == 422


class TestRcloneRouterIntegration:
    def test_list_then_copy_workflow(self, client):
        """Test common workflow: list files then copy"""
        with patch("src.kortana.routers.rclone.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "important_file.txt\n"
            mock_run.return_value = mock_result

            # List files
            list_response = client.get("/api/rclone/files/source_remote")
            assert list_response.status_code == 200

            with patch("src.kortana.routers.rclone.subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_popen.return_value = mock_process

                # Copy the file
                copy_response = client.post(
                    "/api/rclone/copy?source=source_remote:/important_file.txt&destination=dest_remote:/backup/"
                )
                assert copy_response.status_code == 200
