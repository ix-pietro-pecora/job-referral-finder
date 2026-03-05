import responses
from scrapers import greenhouse, lever, ashby, gem, workable, smartrecruiters, workday


class TestGreenhouseScraper:
    @responses.activate
    def test_fetch_jobs_success(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/testco/jobs?content=true",
            json={
                "jobs": [
                    {
                        "title": "Software Engineer",
                        "location": {"name": "San Francisco"},
                        "absolute_url": "https://boards.greenhouse.io/testco/jobs/123",
                        "content": "<p>Build things</p>",
                    }
                ]
            },
            status=200,
        )
        jobs = greenhouse.fetch_jobs("testco")
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Software Engineer"
        assert jobs[0]["location"] == "San Francisco"
        assert jobs[0]["url"] == "https://boards.greenhouse.io/testco/jobs/123"
        assert "<p>" not in jobs[0]["description"]

    @responses.activate
    def test_fetch_jobs_empty(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/empty/jobs?content=true",
            json={"jobs": []},
            status=200,
        )
        assert greenhouse.fetch_jobs("empty") == []

    @responses.activate
    def test_fetch_jobs_404(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/bad/jobs?content=true",
            status=404,
        )
        assert greenhouse.fetch_jobs("bad") == []

    @responses.activate
    def test_fetch_jobs_malformed_json(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/broken/jobs?content=true",
            body="not json",
            status=200,
        )
        assert greenhouse.fetch_jobs("broken") == []


class TestLeverScraper:
    @responses.activate
    def test_fetch_jobs_success(self):
        responses.add(
            responses.GET,
            "https://api.lever.co/v0/postings/testco?mode=json",
            json=[
                {
                    "text": "Product Manager",
                    "categories": {"location": "New York"},
                    "hostedUrl": "https://jobs.lever.co/testco/456",
                    "descriptionPlain": "Lead product.",
                    "additionalPlain": "Nice to have.",
                }
            ],
            status=200,
        )
        jobs = lever.fetch_jobs("testco")
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Product Manager"
        assert jobs[0]["location"] == "New York"
        assert "Lead product." in jobs[0]["description"]

    @responses.activate
    def test_fetch_jobs_empty(self):
        responses.add(
            responses.GET,
            "https://api.lever.co/v0/postings/empty?mode=json",
            json=[],
            status=200,
        )
        assert lever.fetch_jobs("empty") == []

    @responses.activate
    def test_fetch_jobs_error(self):
        responses.add(
            responses.GET,
            "https://api.lever.co/v0/postings/bad?mode=json",
            status=500,
        )
        assert lever.fetch_jobs("bad") == []


class TestAshbyScraper:
    @responses.activate
    def test_fetch_jobs_success(self):
        responses.add(
            responses.GET,
            "https://api.ashbyhq.com/posting-api/job-board/testco",
            json={
                "jobs": [
                    {
                        "title": "Designer",
                        "location": "Remote",
                        "jobUrl": "https://jobs.ashbyhq.com/testco/789",
                        "descriptionHtml": "<b>Design systems</b>",
                    }
                ]
            },
            status=200,
        )
        jobs = ashby.fetch_jobs("testco")
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Designer"
        assert jobs[0]["location"] == "Remote"
        assert "<b>" not in jobs[0]["description"]

    @responses.activate
    def test_fetch_jobs_empty(self):
        responses.add(
            responses.GET,
            "https://api.ashbyhq.com/posting-api/job-board/empty",
            json={"jobs": []},
            status=200,
        )
        assert ashby.fetch_jobs("empty") == []

    @responses.activate
    def test_fetch_jobs_plain_fallback(self):
        responses.add(
            responses.GET,
            "https://api.ashbyhq.com/posting-api/job-board/plain",
            json={
                "jobs": [
                    {
                        "title": "Engineer",
                        "location": "NYC",
                        "jobUrl": "https://jobs.ashbyhq.com/plain/1",
                        "descriptionHtml": "",
                        "descriptionPlain": "Plain text desc",
                    }
                ]
            },
            status=200,
        )
        jobs = ashby.fetch_jobs("plain")
        assert jobs[0]["description"] == "Plain text desc"


class TestGemScraper:
    @responses.activate
    def test_fetch_jobs_success(self):
        responses.add(
            responses.GET,
            "https://api.gem.com/job_board/v0/testco/job_posts/",
            json=[
                {
                    "title": "Software Engineer",
                    "location": {"name": "San Francisco"},
                    "absolute_url": "https://jobs.gem.com/testco/123",
                    "content": "<p>Build things</p>",
                    "content_plain": "Build things",
                }
            ],
            status=200,
        )
        jobs = gem.fetch_jobs("testco")
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Software Engineer"
        assert jobs[0]["location"] == "San Francisco"
        assert jobs[0]["url"] == "https://jobs.gem.com/testco/123"
        assert jobs[0]["description"] == "Build things"

    @responses.activate
    def test_fetch_jobs_empty(self):
        responses.add(
            responses.GET,
            "https://api.gem.com/job_board/v0/empty/job_posts/",
            json=[],
            status=200,
        )
        assert gem.fetch_jobs("empty") == []

    @responses.activate
    def test_fetch_jobs_404(self):
        responses.add(
            responses.GET,
            "https://api.gem.com/job_board/v0/bad/job_posts/",
            status=404,
        )
        assert gem.fetch_jobs("bad") == []

    @responses.activate
    def test_falls_back_to_html_content(self):
        responses.add(
            responses.GET,
            "https://api.gem.com/job_board/v0/htmlco/job_posts/",
            json=[
                {
                    "title": "PM",
                    "location": {"name": "NYC"},
                    "absolute_url": "https://jobs.gem.com/htmlco/456",
                    "content": "<b>Lead products</b>",
                    "content_plain": "",
                }
            ],
            status=200,
        )
        jobs = gem.fetch_jobs("htmlco")
        assert jobs[0]["description"] == "Lead products"
        assert "<b>" not in jobs[0]["description"]


class TestWorkableScraper:
    @responses.activate
    def test_fetch_jobs_success(self):
        responses.add(
            responses.POST,
            "https://apply.workable.com/api/v3/accounts/testco/jobs",
            json={
                "total": 1,
                "results": [
                    {
                        "title": "Frontend Engineer",
                        "shortcode": "ABC123",
                        "location": {"city": "Berlin", "region": "Berlin", "country": "DE"},
                        "department": "Engineering",
                        "workplace": "Remote",
                    }
                ],
            },
            status=200,
        )
        jobs = workable.fetch_jobs("testco")
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Frontend Engineer"
        assert "Berlin" in jobs[0]["location"]
        assert "Engineering" in jobs[0]["description"]
        assert jobs[0]["url"] == "https://apply.workable.com/testco/j/ABC123/"

    @responses.activate
    def test_fetch_jobs_empty(self):
        responses.add(
            responses.POST,
            "https://apply.workable.com/api/v3/accounts/empty/jobs",
            json={"total": 0, "results": []},
            status=200,
        )
        assert workable.fetch_jobs("empty") == []

    @responses.activate
    def test_fetch_jobs_404(self):
        responses.add(
            responses.POST,
            "https://apply.workable.com/api/v3/accounts/bad/jobs",
            status=404,
        )
        assert workable.fetch_jobs("bad") == []


class TestSmartRecruitersScraper:
    @responses.activate
    def test_fetch_jobs_success(self):
        responses.add(
            responses.GET,
            "https://api.smartrecruiters.com/v1/companies/testco/postings",
            json={
                "content": [
                    {
                        "id": "111",
                        "uuid": "aaa-bbb",
                        "name": "Data Scientist",
                        "location": {"fullLocation": "New York, NY"},
                        "department": {"label": "Engineering"},
                        "experienceLevel": {"label": "Mid-Senior Level"},
                    }
                ]
            },
            status=200,
        )
        jobs = smartrecruiters.fetch_jobs("testco")
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Data Scientist"
        assert jobs[0]["location"] == "New York, NY"
        assert "Engineering" in jobs[0]["description"]
        assert jobs[0]["_uuid"] == "aaa-bbb"

    @responses.activate
    def test_fetch_jobs_empty(self):
        responses.add(
            responses.GET,
            "https://api.smartrecruiters.com/v1/companies/empty/postings",
            json={"content": []},
            status=200,
        )
        assert smartrecruiters.fetch_jobs("empty") == []

    @responses.activate
    def test_fetch_jobs_404(self):
        responses.add(
            responses.GET,
            "https://api.smartrecruiters.com/v1/companies/bad/postings",
            status=404,
        )
        assert smartrecruiters.fetch_jobs("bad") == []

    @responses.activate
    def test_fetch_description_on_demand(self):
        responses.add(
            responses.GET,
            "https://api.smartrecruiters.com/v1/companies/testco/postings/aaa-bbb",
            json={
                "jobAd": {
                    "sections": {
                        "jobDescription": {"text": "<p>Analyze data</p>"},
                        "qualifications": {"text": "<p>PhD preferred</p>"},
                    }
                }
            },
            status=200,
        )
        desc = smartrecruiters.fetch_description("testco", "aaa-bbb")
        assert "Analyze data" in desc
        assert "PhD preferred" in desc
        assert "<p>" not in desc


class TestWorkdayScraper:
    BASE = "https://testco.wd1.myworkdayjobs.com"
    BOARD = "TestBoard"

    @responses.activate
    def test_fetch_jobs_success(self):
        responses.add(
            responses.POST,
            f"{self.BASE}/wday/cxs/testco/{self.BOARD}/jobs",
            json={
                "jobPostings": [
                    {
                        "title": "Backend Engineer",
                        "locationsText": "San Francisco",
                        "externalPath": "/job/SF/Backend-Engineer_123",
                        "bulletFields": ["Full time", "Engineering"],
                    }
                ]
            },
            status=200,
        )
        jobs = workday.fetch_jobs("testco", base_url=self.BASE, board_name=self.BOARD)
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Backend Engineer"
        assert jobs[0]["location"] == "San Francisco"
        assert "Full time" in jobs[0]["description"]
        assert jobs[0]["_path"] == "/job/SF/Backend-Engineer_123"

    @responses.activate
    def test_fetch_jobs_empty(self):
        responses.add(
            responses.POST,
            f"{self.BASE}/wday/cxs/testco/{self.BOARD}/jobs",
            json={"jobPostings": []},
            status=200,
        )
        assert workday.fetch_jobs("testco", base_url=self.BASE, board_name=self.BOARD) == []

    def test_missing_base_url_returns_empty(self):
        assert workday.fetch_jobs("testco") == []
        assert workday.fetch_jobs("testco", base_url="", board_name="Board") == []
        assert workday.fetch_jobs("testco", base_url="https://x.com", board_name="") == []

    @responses.activate
    def test_fetch_jobs_api_error(self):
        responses.add(
            responses.POST,
            f"{self.BASE}/wday/cxs/testco/{self.BOARD}/jobs",
            status=403,
        )
        assert workday.fetch_jobs("testco", base_url=self.BASE, board_name=self.BOARD) == []

    @responses.activate
    def test_fetch_description_on_demand(self):
        responses.add(
            responses.GET,
            f"{self.BASE}/wday/cxs/testco/{self.BOARD}/job/SF/Backend-Engineer_123",
            json={
                "jobPostingInfo": {
                    "jobDescription": "<b>Build APIs</b>",
                }
            },
            status=200,
        )
        desc = workday.fetch_description(self.BASE, "testco", self.BOARD, "/job/SF/Backend-Engineer_123")
        assert "Build APIs" in desc
        assert "<b>" not in desc
