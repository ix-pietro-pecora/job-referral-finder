import responses
from unittest.mock import patch, MagicMock
from scraper_job import scrape_companies, build_email_html
from discovery import resolver


class TestScrapeCompanies:
    @responses.activate
    @patch("scraper_job.filter_and_rank")
    @patch("scraper_job.posthog")
    def test_resolved_company_fetches_jobs(self, mock_posthog, mock_rank):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true",
            json={
                "jobs": [
                    {
                        "title": "Engineer",
                        "location": {"name": "SF"},
                        "absolute_url": "http://stripe.com/jobs/1",
                        "content": "Build payments",
                    }
                ]
            },
            status=200,
        )
        mock_rank.return_value = [
            {"title": "Engineer", "location": "SF", "url": "http://stripe.com/jobs/1",
             "description": "Build payments", "company": "Stripe", "match_note": "Good fit"}
        ]

        matched, unresolved = scrape_companies(["Stripe"], "Engineer")
        assert len(matched) == 1
        assert matched[0]["company"] == "Stripe"
        assert unresolved == []

    @responses.activate
    @patch("discovery.resolver._probe_workday", return_value=None)
    @patch("scraper_job.filter_and_rank")
    @patch("scraper_job.posthog")
    def test_unresolved_company(self, mock_posthog, mock_rank, mock_wd):
        responses.add(responses.GET, "https://boards-api.greenhouse.io/v1/boards/xyzcorp123/jobs", status=404)
        responses.add(responses.GET, "https://api.lever.co/v0/postings/xyzcorp123", status=404)
        responses.add(responses.GET, "https://api.ashbyhq.com/posting-api/job-board/xyzcorp123", status=404)
        responses.add(responses.GET, "https://api.gem.com/job_board/v0/xyzcorp123/job_posts/", status=404)
        responses.add(responses.POST, "https://apply.workable.com/api/v3/accounts/xyzcorp123/jobs", json={"total": 0, "results": []}, status=200)
        responses.add(responses.GET, "https://api.smartrecruiters.com/v1/companies/xyzcorp123/postings", status=404)
        mock_rank.return_value = []

        matched, unresolved = scrape_companies(["XyzCorp123"], "PM")
        assert unresolved == ["XyzCorp123"]
        mock_posthog.capture.assert_called_once()
        call_args = mock_posthog.capture.call_args
        assert call_args[0][1] == "unsupported_company_requested"


class TestBuildEmailHtml:
    def test_includes_job_details(self):
        jobs = [
            {
                "title": "Engineer",
                "company": "stripe",
                "location": "SF",
                "url": "http://stripe.com/jobs/1",
                "match_note": "Great fit",
            }
        ]
        html = build_email_html("Engineer", jobs, [], email="test@test.com")
        assert "Stripe" in html
        assert "Engineer" in html
        assert "Great fit" in html

    def test_includes_unresolved_note(self):
        html = build_email_html("PM", [], ["FakeCorp"], email="test@test.com")
        assert "FakeCorp" in html
        assert "unsupported ATS" in html

    def test_no_unresolved_note_when_empty(self):
        html = build_email_html("PM", [], [], email="test@test.com")
        assert "unsupported ATS" not in html

    def test_role_count_singular(self):
        jobs = [
            {"title": "PM", "company": "stripe", "location": "", "url": "http://a.com", "match_note": ""}
        ]
        html = build_email_html("PM", jobs, [])
        assert "1 role" in html

    def test_role_count_plural(self):
        jobs = [
            {"title": "PM", "company": "stripe", "location": "", "url": "http://a.com", "match_note": ""},
            {"title": "PM2", "company": "notion", "location": "", "url": "http://b.com", "match_note": ""},
        ]
        html = build_email_html("PM", jobs, [])
        assert "2 roles" in html
