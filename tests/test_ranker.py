import json
from unittest.mock import patch, MagicMock
from claude_client.ranker import filter_and_rank


def _mock_claude_response(text):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


class TestFilterAndRank:
    def test_empty_jobs(self):
        assert filter_and_rank([], "Software Engineer") == []

    @patch("claude_client.ranker.client")
    def test_returns_matched_jobs(self, mock_client):
        jobs = [
            {"title": "Software Engineer", "location": "SF", "url": "http://a.com", "description": "Build stuff"},
            {"title": "Office Manager", "location": "NY", "url": "http://b.com", "description": "Manage office"},
        ]
        mock_client.messages.create.return_value = _mock_claude_response(
            json.dumps([{"index": 0, "match_note": "Relevant SWE role"}])
        )
        result = filter_and_rank(jobs, "Software Engineer")
        assert len(result) == 1
        assert result[0]["title"] == "Software Engineer"
        assert result[0]["match_note"] == "Relevant SWE role"

    @patch("claude_client.ranker.client")
    def test_handles_code_fenced_response(self, mock_client):
        jobs = [
            {"title": "PM", "location": "Remote", "url": "http://c.com", "description": "Product role"},
        ]
        mock_client.messages.create.return_value = _mock_claude_response(
            '```json\n[{"index": 0, "match_note": "Good fit"}]\n```'
        )
        result = filter_and_rank(jobs, "Product Manager")
        assert len(result) == 1
        assert result[0]["match_note"] == "Good fit"

    @patch("claude_client.ranker.client")
    def test_handles_invalid_json(self, mock_client):
        jobs = [
            {"title": "Engineer", "location": "LA", "url": "http://d.com", "description": "Code"},
        ]
        mock_client.messages.create.return_value = _mock_claude_response("not valid json")
        result = filter_and_rank(jobs, "Engineer")
        assert result == []

    @patch("claude_client.ranker.client")
    def test_handles_out_of_bounds_index(self, mock_client):
        jobs = [
            {"title": "Engineer", "location": "LA", "url": "http://d.com", "description": "Code"},
        ]
        mock_client.messages.create.return_value = _mock_claude_response(
            json.dumps([{"index": 99, "match_note": "Ghost job"}])
        )
        result = filter_and_rank(jobs, "Engineer")
        assert result == []

    @patch("claude_client.ranker.client")
    def test_with_background(self, mock_client):
        jobs = [
            {"title": "Senior PM", "location": "SF", "url": "http://e.com", "description": "Lead products"},
        ]
        mock_client.messages.create.return_value = _mock_claude_response(
            json.dumps([{"index": 0, "match_note": "Matches seniority"}])
        )
        result = filter_and_rank(jobs, "Product Manager", background="5 years PM experience")
        assert len(result) == 1
        call_args = mock_client.messages.create.call_args
        assert "5 years PM experience" in call_args[1]["messages"][0]["content"]
