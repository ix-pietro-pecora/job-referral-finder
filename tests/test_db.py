from unittest.mock import patch, MagicMock
from db import add_subscription, get_all_subscriptions, unsubscribe, get_sent_urls, mark_jobs_sent


def _mock_client():
    client = MagicMock()
    return client


class TestAddSubscription:
    @patch("db._client")
    def test_upserts_subscription(self, mock_client_fn):
        client = _mock_client()
        mock_client_fn.return_value = client
        result_mock = MagicMock()
        result_mock.data = [{"email": "a@b.com", "companies": ["Stripe"], "target_role": "PM", "active": True}]
        client.table.return_value.upsert.return_value.execute.return_value = result_mock

        result = add_subscription("a@b.com", ["Stripe"], "PM")
        assert result["email"] == "a@b.com"
        client.table.assert_called_with("subscriptions")

    @patch("db._client")
    def test_returns_empty_on_no_data(self, mock_client_fn):
        client = _mock_client()
        mock_client_fn.return_value = client
        result_mock = MagicMock()
        result_mock.data = []
        client.table.return_value.upsert.return_value.execute.return_value = result_mock

        result = add_subscription("a@b.com", ["Stripe"], "PM")
        assert result == {}


class TestGetAllSubscriptions:
    @patch("db._client")
    def test_returns_active_subs(self, mock_client_fn):
        client = _mock_client()
        mock_client_fn.return_value = client
        result_mock = MagicMock()
        result_mock.data = [
            {"email": "a@b.com", "companies": ["Stripe"], "active": True},
            {"email": "c@d.com", "companies": ["Notion"], "active": True},
        ]
        client.table.return_value.select.return_value.eq.return_value.execute.return_value = result_mock

        subs = get_all_subscriptions()
        assert len(subs) == 2


class TestUnsubscribe:
    @patch("db._client")
    def test_sets_active_false(self, mock_client_fn):
        client = _mock_client()
        mock_client_fn.return_value = client
        unsubscribe("a@b.com")
        client.table.return_value.update.assert_called_with({"active": False})


class TestGetSentUrls:
    @patch("db._client")
    def test_returns_set_of_urls(self, mock_client_fn):
        client = _mock_client()
        mock_client_fn.return_value = client
        result_mock = MagicMock()
        result_mock.data = [{"job_url": "http://a.com"}, {"job_url": "http://b.com"}]
        client.table.return_value.select.return_value.eq.return_value.execute.return_value = result_mock

        urls = get_sent_urls("a@b.com")
        assert urls == {"http://a.com", "http://b.com"}


class TestMarkJobsSent:
    @patch("db._client")
    def test_skips_empty_list(self, mock_client_fn):
        client = _mock_client()
        mock_client_fn.return_value = client
        mark_jobs_sent("a@b.com", [])
        client.table.assert_not_called()

    @patch("db._client")
    def test_upserts_rows(self, mock_client_fn):
        client = _mock_client()
        mock_client_fn.return_value = client
        mark_jobs_sent("a@b.com", ["http://a.com", "http://b.com"])
        client.table.assert_called_with("sent_jobs")
